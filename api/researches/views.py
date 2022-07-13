from collections import defaultdict

import simplejson as json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import JsonResponse

from api.researches.help_files.constructor_help import constructor_help_message
from directions.models import FrequencyOfUseResearches

import users.models as users
from api.directions.views import get_research_for_direction_params
from clients.models import AdditionalPatientDispensaryPlan
from directory.models import (
    Researches as DResearches,
    ParaclinicInputGroups,
    Fractions,
    ParaclinicTemplateName,
    ParaclinicInputField,
    ParaclinicTemplateField,
    HospitalService,
    DispensaryPlan,
    Localization,
    ServiceLocation,
)
from directory.utils import get_researches_details
from laboratory.decorators import group_required
from laboratory.settings import REQUIRED_STATTALON_FIELDS, RESEARCHES_PK_REQUIRED_STATTALON_FIELDS, DISABLED_RESULT_FORMS
from podrazdeleniya.models import Podrazdeleniya
from researches.models import Tubes
from rmis_integration.client import get_md5
from slog.models import Log
from users.models import AssignmentTemplates, Speciality
from utils.nsi_directories import NSI
from utils.response import status_response
from hospitals.models import HospitalsGroup


@login_required
def get_researches_templates(request):
    templates = []
    for t in (
        users.AssignmentTemplates.objects.filter(global_template=True)
        .filter(Q(doc__isnull=True, podrazdeleniye__isnull=True) | Q(doc=request.user.doctorprofile) | Q(podrazdeleniye=request.user.doctorprofile.podrazdeleniye))
        .prefetch_related('assignmentresearches_set')
    ):
        templates.append(
            {
                "values": [x.research_id for x in t.assignmentresearches_set.all()],
                "pk": t.pk,
                "title": t.title,
                "for_current_user": t.doc_id is not None,
                "for_users_department": t.podrazdeleniye_id is not None,
            }
        )
    result = {"templates": templates}
    if hasattr(request, 'plain_response') and request.plain_response:
        return result
    return JsonResponse(result)


def get_researches(request, last_used=False):
    deps = defaultdict(list)
    doctorprofile = request.user.doctorprofile
    k = f'get_researches:restricted_to_direct:{doctorprofile.pk}'
    restricted_to_direct = cache.get(k)
    if not restricted_to_direct:
        restricted_to_direct = [x['pk'] for x in doctorprofile.restricted_to_direct.all().values('pk')]

        white_list_monitoring = [x for x in users.DoctorProfile.objects.values_list('white_list_monitoring', flat=True).filter(pk=doctorprofile.pk) if x is not None]
        restricted_monitoring = []

        if len(white_list_monitoring) > 0:
            restricted_monitoring = list(DResearches.objects.values_list('pk', flat=True).filter(hide=False, is_monitoring=True).exclude(pk__in=white_list_monitoring))
        else:
            black_list_monitoring = [x for x in users.DoctorProfile.objects.values_list('black_list_monitoring', flat=True).filter(pk=doctorprofile.pk) if x is not None]
            if len(black_list_monitoring) > 0:
                restricted_monitoring = list(DResearches.objects.values_list('pk', flat=True).filter(hide=False, is_monitoring=True, pk__in=black_list_monitoring))

        doc_hospital = [doctorprofile.get_hospital()]
        groups_black_list = HospitalsGroup.access_black_list_edit_monitoring.through.objects.filter(hospitalsgroup__hospital__in=doc_hospital).values_list('researches__pk', flat=True)
        groups_white_list = HospitalsGroup.access_white_list_edit_monitoring.through.objects.filter(hospitalsgroup__hospital__in=doc_hospital).values_list('researches__pk', flat=True)

        if groups_white_list:
            restricted_monitoring.extend(list(DResearches.objects.values_list('pk', flat=True).filter(hide=False, is_monitoring=True).exclude(pk__in=groups_white_list)))
        else:
            restricted_monitoring.extend(groups_black_list)

        restricted_to_direct.extend(restricted_monitoring)

        # Доступные услуги по роли
        user_gr = [x.pk for x in request.user.groups.all()]
        global_groups = [x.pk for x in Group.objects.all()]
        restricted_researches_by_group = []
        for global_gr in global_groups:
            researches_in_group = users.AvailableResearchByGroup.objects.values_list('research_id', flat=True).filter(group_id=global_gr)
            if len(researches_in_group) > 0 and global_gr not in user_gr:
                restricted_researches_by_group.extend(researches_in_group)
        restricted_to_direct.extend(restricted_researches_by_group)

        restricted_to_direct = list(set(restricted_to_direct))
        cache.set(k, json.dumps(restricted_to_direct), 30)
    else:
        restricted_to_direct = json.loads(restricted_to_direct)
    mk = f'get_researches:result:{get_md5(";".join([str(x) for x in restricted_to_direct]))}'
    result = cache.get(mk) if not last_used else None

    if not result:
        q = {}
        cnts = {}
        if last_used:
            res = FrequencyOfUseResearches.objects.filter(user=doctorprofile, research__hide=False, cnt__gt=0).order_by('-cnt')[:20]
            q['pk__in'] = [x.research_id for x in res]
            cnts = {x.research_id: x.cnt for x in res}
        res = (
            DResearches.objects.filter(hide=False, **q)
            .exclude(pk__in=restricted_to_direct)
            .select_related('podrazdeleniye', 'comment_variants')
            .prefetch_related(
                Prefetch('localization', queryset=Localization.objects.only('pk', 'title'), to_attr='localization_list'),
                Prefetch('service_location', queryset=ServiceLocation.objects.only('pk', 'title'), to_attr='service_location_list'),
                'a',
                'b',
            )
            .distinct('title', 'pk')
            .order_by('title')
            .defer(
                "preparation",
                "paraclinic_info",
                "instructions",
                "internal_code",
                "co_executor_2_title",
                "bac_conclusion_templates",
                "bac_culture_comments_templates",
                "rmis_id",
                "podrazdeleniye__title",
                "podrazdeleniye__short_title",
                "podrazdeleniye__hide",
                "podrazdeleniye__vaccine",
                "podrazdeleniye__rmis_id",
                "podrazdeleniye__rmis_direction_type",
                "podrazdeleniye__rmis_department_title",
                "podrazdeleniye__can_has_pacs",
                "podrazdeleniye__oid",
                "podrazdeleniye__hospital_id",
            )
        )

        r: DResearches

        has_morfology = {}

        for r in res:
            k = f'get_researches:research:{r.pk}'
            research_data = cache.get(k)

            if not research_data:
                autoadd = [x.b_id for x in r.a.all()]
                addto = [x.a_id for x in r.b.all()]

                direction_params_pk = (r.direction_params_id or -1) if not r.is_application else r.pk
                research_data = {
                    "pk": r.pk,
                    "onlywith": r.onlywith_id or -1,
                    "department_pk": r.reversed_type,
                    "title": r.get_title(),
                    "full_title": r.title,
                    "doc_refferal": r.is_doc_refferal,
                    "treatment": r.is_treatment,
                    "is_hospital": r.is_hospital,
                    "is_form": r.is_form,
                    "is_application": r.is_application,
                    "stom": r.is_stom,
                    "need_vich_code": r.need_vich_code,
                    "comment_variants": [] if not r.comment_variants else r.comment_variants.get_variants(),
                    "autoadd": autoadd,
                    "addto": addto,
                    "code": r.code,
                    "type": "4" if not r.podrazdeleniye else str(r.podrazdeleniye.p_type),
                    "site_type": r.get_site_type_id(),
                    "site_type_raw": r.site_type_id if not r.is_application else -13,
                    "localizations": [{"code": x.pk, "label": x.title} for x in r.localization_list],
                    "service_locations": [{"code": x.pk, "label": x.title} for x in r.service_location_list],
                    "direction_params": direction_params_pk,
                    "research_data": {'research': {'status': 'NOT_LOADED'}},
                }
                cache.set(k, json.dumps(research_data), 30)
            else:
                research_data = json.loads(research_data)

            if not last_used:
                tpls = []
                if r.is_microbiology and 'is_microbiology' not in has_morfology:
                    has_morfology['is_microbiology'] = True
                    for at in AssignmentTemplates.objects.filter(show_in_research_picker=True, is_microbiology=True):
                        tpls.append(at.as_research())

                if r.is_citology and 'is_citology' not in has_morfology:
                    has_morfology['is_citology'] = True
                    for at in AssignmentTemplates.objects.filter(show_in_research_picker=True, is_citology=True):
                        tpls.append(at.as_research())

                if r.is_gistology and 'is_gistology' not in has_morfology:
                    has_morfology['is_gistology'] = True
                    for at in AssignmentTemplates.objects.filter(show_in_research_picker=True, is_gistology=True):
                        tpls.append(at.as_research())

                if r.reversed_type not in deps:
                    if r.reversed_type > 0:
                        for at in AssignmentTemplates.objects.filter(show_in_research_picker=True, podrazdeleniye_id=r.reversed_type):
                            tpls.append(at.as_research())
                    if r.is_doc_refferal:
                        for at in AssignmentTemplates.objects.filter(show_in_research_picker=True, is_doc_refferal=True):
                            tpls.append(at.as_research())
                    if r.is_treatment:
                        for at in AssignmentTemplates.objects.filter(show_in_research_picker=True, is_treatment=True):
                            tpls.append(at.as_research())
                    if r.is_stom:
                        for at in AssignmentTemplates.objects.filter(show_in_research_picker=True, is_stom=True):
                            tpls.append(at.as_research())
                    if r.is_hospital:
                        for at in AssignmentTemplates.objects.filter(show_in_research_picker=True, is_hospital=True):
                            tpls.append(at.as_research())
                if tpls:
                    deps[r.reversed_type].extend(tpls)
            deps['-109999' if last_used else r.reversed_type].append(research_data)

        for dk in deps:
            if last_used:
                deps[dk] = list(sorted(deps[dk], key=lambda d: cnts.get(d['pk'], 0), reverse=True))
            else:
                deps[dk] = list(sorted(deps[dk], key=lambda d: d['title']))

        if not last_used:
            k = 'get_researches:tubes'
            tubes = cache.get(k)
            if not tubes:
                tubes = list(Tubes.objects.values('pk', 'title', 'color'))
                cache.set(k, json.dumps(tubes), 60)
            else:
                tubes = json.loads(tubes)

            result = {"researches": deps, "tubes": tubes}
            cache.set(mk, json.dumps(result), 30)
        else:
            result = {"researches": deps, "cnts": cnts}
    else:
        result = json.loads(result)

    if hasattr(request, 'plain_response') and request.plain_response:
        return result
    return JsonResponse(result)


def last_used_researches(request):
    return get_researches(request, last_used=True)


def by_direction_params(request):
    data = {}
    res = DResearches.objects.filter(hide=False, is_direction_params=True, is_global_direction_params=True).order_by('title').values('pk', 'title', 'short_title')
    for r in res:
        data[r['pk']] = {"title": r['short_title'] or r['title'], "full_title": r['title'], "research_data": {}}

    if hasattr(request, 'plain_response') and request.plain_response:
        return data
    return JsonResponse(data)


def get_direction_params(request):
    request_data = json.loads(request.body)
    pk = int(request_data["pk"])
    data = get_research_for_direction_params(pk).get('research', {})
    return JsonResponse(data)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def localization(request):
    request_data = json.loads(request.body)
    pk = int(request_data["pk"])
    research = DResearches.objects.get(pk=pk)
    selected = [x["pk"] for x in research.localization.all().values('pk')]
    localizations = list(Localization.objects.all().order_by('title').values('pk', 'title', 'fsli', 'barcode'))
    return JsonResponse({"localizations": localizations, "selected": selected})


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def localization_save(request):
    request_data = json.loads(request.body)
    pk = int(request_data["pk"])
    selected = [int(x) for x in list(request_data["selected"])]
    research = DResearches.objects.get(pk=pk)
    for lс in research.localization.all():
        if lс.pk not in selected:
            research.localization.remove(lс.pk)
        else:
            selected = [x for x in selected if x != lс.pk]
    if selected:
        research.localization.add(*list(Localization.objects.filter(pk__in=selected)))
    return status_response(True)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования", "Врач стационара")
def researches_by_department(request):
    direction_form = DResearches.DIRECTION_FORMS
    result_form = [i for i in DResearches.RESULT_FORMS if i[0] not in DISABLED_RESULT_FORMS]
    period_types = [{'id': x[0], 'label': x[1]} for x in DResearches.PERIOD_TYPES]
    spec_data = [{"pk": -1, "title": "Не выбрано"}, *list(users.Speciality.objects.all().values('pk', 'title').order_by("title"))]

    response = {"researches": [], "direction_forms": direction_form, "result_forms": result_form, "specialities": spec_data, "permanent_directories": NSI, "period_types": period_types}
    request_data = json.loads(request.body)
    department_pk = int(request_data["department"])
    if -500 >= department_pk > -600:
        for hospital_service in HospitalService.objects.filter(site_type=-department_pk - 500):
            response["researches"].append(
                {
                    "pk": hospital_service.pk,
                    "slave_research_id": hospital_service.slave_research_id,
                    "main_research_id": hospital_service.main_research_id,
                    "is_hospital_service": True,
                    "title": hospital_service.get_title(),
                    "hide": hospital_service.hide,
                }
            )
    elif department_pk != -1:
        if department_pk == -2:
            q = DResearches.objects.filter(is_doc_refferal=True).order_by("title")
        elif department_pk == -3:
            q = DResearches.objects.filter(is_treatment=True).order_by("title")
        elif department_pk == -4:
            q = DResearches.objects.filter(is_stom=True).order_by("title")
        elif department_pk == -5:
            q = DResearches.objects.filter(is_hospital=True).order_by("title")
        elif department_pk == -6:
            q = DResearches.objects.filter(is_microbiology=True).order_by("title")
        elif department_pk == -7:
            q = DResearches.objects.filter(is_citology=True).order_by("title")
        elif department_pk == -8:
            q = DResearches.objects.filter(is_gistology=True).order_by("title")
        elif department_pk == -9:
            q = DResearches.objects.filter(is_form=True).order_by("title")
        elif department_pk == -10:
            q = DResearches.objects.filter(is_direction_params=True).order_by("title")
        elif department_pk == -11:
            q = DResearches.objects.filter(is_application=True).order_by("title")
        elif department_pk == -12:
            q = DResearches.objects.filter(is_monitoring=True).order_by("title")
        elif department_pk == -13:
            q = DResearches.objects.filter(is_expertise=True).order_by("title")
        else:
            q = DResearches.objects.filter(podrazdeleniye__pk=department_pk).order_by("title")

        for research in q:
            response["researches"].append(
                {
                    "pk": research.pk,
                    "title": research.title,
                    "short_title": research.short_title,
                    "preparation": research.preparation,
                    "hide": research.hide,
                    "code": research.code,
                }
            )
    return JsonResponse(response)


@login_required
def researches_params(request):
    response = {"researches": []}
    request_data = json.loads(request.body)
    pks = request_data.get("pks", [])
    for research in DResearches.objects.filter(pk__in=pks):
        params = []
        if research.is_paraclinic or research.is_doc_refferal:
            for g in ParaclinicInputGroups.objects.filter(research=research).exclude(title="").order_by("order"):
                params.append({"pk": g.pk, "title": g.title})
        else:
            for f in Fractions.objects.filter(research=research).order_by("sort_weight"):
                params.append({"pk": f.pk, "title": f.title})
        response["researches"].append(
            {"pk": research.pk, "title": research.title, "short_title": research.get_title(), "params": params, "is_paraclinic": research.is_paraclinic, "selected_params": []}
        )
    return JsonResponse(response)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
@transaction.atomic
def researches_update(request):
    response = {"ok": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -2)
    if pk > -2:
        department_pk = request_data.get("department")
        title = request_data.get("title", "").strip()
        short_title = request_data.get("short_title", "").strip()
        schedule_title = request_data.get("schedule_title", "").strip()
        is_global_direction_params = request_data.get("is_global_direction_params", False)
        code = request_data.get("code", "").strip()
        internal_code = request_data.get("internal_code", "").strip()
        spec_pk = request_data.get("speciality", -1)
        speciality = Speciality.objects.filter(pk=spec_pk).first()
        direction_current_form = request_data.get("direction_current_form", 0)
        result_current_form = request_data.get("result_current_form", 0)
        type_period = request_data.get("type_period")
        direction_current_params = request_data.get("direction_current_params", -1)
        direction_current_expertise = request_data.get("direction_current_expertise", -1)
        if direction_current_expertise == -1:
            direction_current_expertise = None
        researche_direction_current_params = None
        if int(direction_current_params) > -1:
            researche_direction_current_params = DResearches.objects.get(pk=int(direction_current_params))
        direction_current_form = direction_current_form or 0
        result_current_form = result_current_form or 0
        own_form_result = result_current_form > 0
        info = request_data.get("info", "").strip()
        hide = request_data.get("hide")
        site_type = request_data.get("site_type", None)
        groups = request_data.get("groups", [])
        tube = request_data.get("tube", -1)
        is_simple = request_data.get("simple", False)
        main_service_pk = request_data.get("main_service_pk", -1)
        hs_pk = request_data.get("hs_pk", -1)
        conclusion_templates = request_data.get("conclusionTpl", "")
        culture_comments_templates = request_data.get("cultureTpl", "")
        hide_main = request_data.get("hide_main", False)
        show_more_services = request_data.get("show_more_services", True)
        hospital_research_department_pk = request_data.get("hospital_research_department_pk", -1)
        if tube == -1:
            tube = None
        stationar_slave = is_simple and -500 >= department_pk > -600 and main_service_pk != 1
        desc = stationar_slave or department_pk in [-2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12, -13]
        if len(title) > 0 and (desc or Podrazdeleniya.objects.filter(pk=department_pk).exists()):
            department = None if desc else Podrazdeleniya.objects.filter(pk=department_pk)[0]
            res = None
            if int(hospital_research_department_pk) > -1:
                department = Podrazdeleniya.objects.filter(pk=int(hospital_research_department_pk))[0]
            if pk == -1:
                res = DResearches(
                    title=title,
                    short_title=short_title,
                    schedule_title=schedule_title,
                    podrazdeleniye=department,
                    code=code,
                    is_paraclinic=not desc and department.p_type == 3,
                    paraclinic_info=info,
                    hide=hide,
                    is_doc_refferal=department_pk == -2,
                    is_treatment=department_pk == -3,
                    is_stom=department_pk == -4,
                    is_hospital=department_pk == -5,
                    is_microbiology=department_pk == -6,
                    is_citology=department_pk == -7,
                    is_gistology=department_pk == -8,
                    is_form=department_pk == -9,
                    is_direction_params=department_pk == -10,
                    is_application=department_pk == -11,
                    is_monitoring=department_pk == -12,
                    is_expertise=department_pk == -13,
                    is_slave_hospital=stationar_slave,
                    microbiology_tube_id=tube if department_pk == -6 else None,
                    site_type_id=site_type,
                    internal_code=internal_code,
                    direction_form=direction_current_form,
                    result_form=result_current_form,
                    type_period=type_period,
                    speciality=speciality,
                    bac_conclusion_templates=conclusion_templates,
                    bac_culture_comments_templates=culture_comments_templates,
                    direction_params=researche_direction_current_params,
                    expertise_params_id=direction_current_expertise,
                    is_global_direction_params=is_global_direction_params,
                    has_own_form_result=own_form_result,
                    show_more_services=show_more_services,
                )
            elif DResearches.objects.filter(pk=pk).exists():
                res = DResearches.objects.filter(pk=pk)[0]
                if res == researche_direction_current_params:
                    return JsonResponse(response)
                res.title = title
                res.short_title = short_title
                res.schedule_title = schedule_title
                res.podrazdeleniye = department
                res.code = code
                res.is_paraclinic = not desc and department.p_type == 3
                res.is_doc_refferal = department_pk == -2
                res.is_treatment = department_pk == -3
                res.is_stom = department_pk == -4
                res.is_hospital = department_pk == -5
                res.is_slave_hospital = stationar_slave
                res.is_microbiology = department_pk == -6
                res.is_citology = department_pk == -7
                res.is_gistology = department_pk == -8
                res.is_form = department_pk == -9
                res.is_direction_params = department_pk == -10
                res.is_application = department_pk == -11
                res.is_monitoring = department_pk == -12
                res.is_expertise = department_pk == -13
                res.microbiology_tube_id = tube if department_pk == -6 else None
                res.paraclinic_info = info
                res.hide = hide
                res.site_type_id = site_type
                res.internal_code = internal_code
                res.speciality = speciality
                res.direction_form = direction_current_form
                res.result_form = result_current_form
                res.type_period = type_period
                res.bac_conclusion_templates = conclusion_templates
                res.bac_culture_comments_templates = culture_comments_templates
                res.direction_params = researche_direction_current_params
                res.expertise_params_id = direction_current_expertise
                res.is_global_direction_params = is_global_direction_params
                res.has_own_form_result = own_form_result
                res.show_more_services = show_more_services and not res.is_microbiology and not res.is_form
            if res:
                res.save()
                if main_service_pk != 1 and stationar_slave:
                    if hs_pk == -1:
                        hs = HospitalService(main_research_id=main_service_pk, hide=hide_main, site_type=-department_pk - 500, slave_research=res)
                        hs.save()
                    else:
                        hs = HospitalService.objects.get(pk=hs_pk)
                        hs.main_research_id = main_service_pk
                        hs.hide = hide_main
                        hs.site_type = -department_pk - 500
                        hs.slave_research = res
                        hs.save()

                templat_obj = ParaclinicTemplateName.make_default(res)
                for group in groups:
                    g = None
                    pk = group["pk"]
                    if pk == -1:
                        g = ParaclinicInputGroups(
                            title=group["title"],
                            show_title=group["show_title"],
                            research=res,
                            order=group["order"],
                            hide=group["hide"],
                            visibility=group.get("visibility", ""),
                            fields_inline=group.get("fieldsInline", False),
                        )
                    elif ParaclinicInputGroups.objects.filter(pk=pk).exists():
                        g = ParaclinicInputGroups.objects.get(pk=pk)
                        g.title = group["title"]
                        g.show_title = group["show_title"]
                        g.research = res
                        g.order = group["order"]
                        g.hide = group["hide"]
                        g.visibility = group.get("visibility", "")
                        g.fields_inline = group.get("fieldsInline", False)
                    if g:
                        g.save()
                        for field in group["fields"]:
                            f = None
                            pk = field["pk"]
                            if pk == -1:

                                f = ParaclinicInputField(
                                    title=field["title"],
                                    short_title=field.get("short_title", ""),
                                    group=g,
                                    order=field["order"],
                                    lines=field["lines"],
                                    for_extract_card=field.get("for_extract_card", False),
                                    for_med_certificate=field.get("for_med_certificate", False),
                                    sign_organization=field.get("sign_organization", False),
                                    hide=field["hide"],
                                    default_value=field["default"],
                                    visibility=field.get("visibility", ""),
                                    input_templates=json.dumps(field["values_to_input"]),
                                    field_type=field.get("field_type", 0),
                                    helper=field.get("helper", ''),
                                    required=field.get("required", False),
                                    not_edit=field.get("not_edit", False),
                                    operator_enter_param=field.get("operator_enter_param", False),
                                    attached=field.get("attached", ''),
                                    control_param=field.get("controlParam", ""),
                                    patient_control_param_id=field.get("patientControlParam", -1) if field.get("patientControlParam", -1) != -1 else None,
                                )
                            elif ParaclinicInputField.objects.filter(pk=pk).exists():
                                f = ParaclinicInputField.objects.get(pk=pk)
                                f.title = field["title"]
                                f.short_title = field["short_title"]
                                f.group = g
                                f.order = field["order"]
                                f.lines = field["lines"]
                                f.for_extract_card = field.get("for_extract_card", False)
                                f.sign_organization = field.get("sign_organization", False)
                                f.hide = field["hide"]
                                f.default_value = field["default"]
                                f.visibility = field.get("visibility", "")
                                f.input_templates = json.dumps(field["values_to_input"])
                                f.field_type = field.get("field_type", 0)
                                f.required = field.get("required", False)
                                f.not_edit = field.get("not_edit", False)
                                f.operator_enter_param = field.get("operator_enter_param", False)
                                f.for_talon = field.get("for_talon", False)
                                f.for_med_certificate = field.get("for_med_certificate", False)
                                f.helper = field.get("helper", '')
                                f.attached = field.get("attached", '')
                                f.control_param = field.get("controlParam", '')
                                f.patient_control_param_id = field.get("patientControlParam", -1) if field.get("patientControlParam", -1) != -1 else None
                            if f:
                                f.save()

                            if f.default_value == '':
                                continue
                            ParaclinicTemplateField.objects.filter(template_name=templat_obj, input_field=f).update(value=f.default_value)

                response["ok"] = True
        Log(key=pk, type=10000, body=json.dumps(request_data), user=request.user.doctorprofile).save()
    return JsonResponse(response)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def researches_details(request):
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    response = get_researches_details(pk)

    return JsonResponse(response)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def paraclinic_details(request):
    response = {"groups": []}
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    for group in ParaclinicInputGroups.objects.filter(research__pk=pk).order_by("order"):
        g = {
            "pk": group.pk,
            "order": group.order,
            "title": group.title,
            "show_title": group.show_title,
            "hide": group.hide,
            "fields": [],
            "fieldsInline": group.fields_inline,
        }
        for field in ParaclinicInputField.objects.filter(group=group).order_by("order"):
            g["fields"].append(
                {
                    "pk": field.pk,
                    "order": field.order,
                    "lines": field.lines,
                    "title": field.title,
                    "default": field.default_value,
                    "hide": field.hide,
                    "values_to_input": json.loads(field.input_templates),
                    "field_type": field.field_type,
                    "required": field.required,
                    "for_talon": field.for_talon,
                    "controlParam": field.control_param,
                }
            )
        response["groups"].append(g)
    return JsonResponse(response)


def fast_templates(request):
    data = []
    request_data = json.loads(request.body)
    is_all = request_data.get('all', False)

    ParaclinicTemplateName.make_default(DResearches.objects.get(pk=request_data["pk"]))

    rts = ParaclinicTemplateName.objects.filter(research__pk=request_data["pk"])

    if not is_all:
        rts = rts.filter(hide=False)

    for rt in rts.order_by('pk'):
        data.append(
            {
                "pk": rt.pk,
                "title": rt.title,
                "hide": rt.hide,
                "readonly": not is_all or rt.title == ParaclinicTemplateName.DEFAULT_TEMPLATE_TITLE,
            }
        )

    return JsonResponse({"data": data})


def fast_template_data(request):
    request_data = json.loads(request.body)
    p = ParaclinicTemplateName.objects.get(pk=request_data["pk"])
    data = {
        "readonly": p.title == ParaclinicTemplateName.DEFAULT_TEMPLATE_TITLE,
        "hide": p.hide,
        "title": p.title,
        "fields": {},
    }

    for pi in ParaclinicTemplateField.objects.filter(template_name=p).order_by('pk'):
        data["fields"][pi.input_field_id] = pi.value

    return JsonResponse({"data": data})


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def fast_template_save(request):
    request_data = json.loads(request.body)
    data = request_data["data"]
    if request_data["pk"] == -1:
        p = ParaclinicTemplateName(research=DResearches.objects.get(pk=request_data["research_pk"]), title=data["title"], hide=data["hide"])
        p.save()
    else:
        p = ParaclinicTemplateName.objects.get(pk=request_data["pk"])
        p.title = data["title"]
        p.hide = data["hide"]
        p.save()
    to_delete = []
    has = []
    for pi in ParaclinicTemplateField.objects.filter(template_name=p):
        if str(pi.input_field_id) not in data["fields"]:
            to_delete.append(pi.pk)
            has.append(pi.input_field_id)
        elif data["fields"][str(pi.input_field_id)] != pi.value:
            pi.value = data["fields"][str(pi.input_field_id)]
            pi.save()
            has.append(pi.input_field_id)
        if data["fields"][str(pi.input_field_id)] == pi.value:
            has.append(pi.input_field_id)
    ParaclinicTemplateField.objects.filter(pk__in=to_delete).delete()
    for pk in data["fields"]:
        pki = int(pk)
        if pki not in has:
            i = ParaclinicInputField.objects.get(pk=pki)
            if i.field_type in [0, 2]:
                ParaclinicTemplateField(template_name=p, input_field=i, value=data["fields"][pk]).save()
    return JsonResponse({"pk": p.pk})


def fraction_title(request):
    request_data = json.loads(request.body)
    fraction = Fractions.objects.get(pk=request_data["pk"])
    return JsonResponse({"fraction": fraction.title, "research": fraction.research.title, "units": fraction.get_unit_str()})


def field_title(request):
    request_data = json.loads(request.body)
    field = ParaclinicInputField.objects.get(pk=request_data["pk"])
    return JsonResponse({"field": field.get_title(), "group": field.group.title, "research": field.group.research.title})


def hospital_service_details(request):
    request_data = json.loads(request.body)
    hs = HospitalService.objects.get(pk=request_data["pk"])
    return JsonResponse(
        {
            "pk": hs.pk,
            "department": -500 - hs.site_type,
            "hide": hs.hide,
            "main_service_pk": hs.main_research_id,
            "slave_service_pk": hs.slave_research_id,
        }
    )


def fields_and_groups_titles(request):
    request_data = json.loads(request.body)
    ids = request_data.get('ids', [])
    titles = {}
    i: str
    for i in ids:
        ii = i.replace('@', '')
        if ii.isdigit():
            if i.endswith('@'):
                g: ParaclinicInputGroups = ParaclinicInputGroups.objects.filter(pk=ii).first()
                if g:
                    titles[i] = ' – '.join([g.research.get_title(), g.title or 'группа без названия'])
                else:
                    titles[i] = None
            else:
                f: ParaclinicInputField = ParaclinicInputField.objects.filter(pk=i).first()
                if f:
                    t = [
                        f.group.research.get_title(),
                        f.group.title or 'группа без названия',
                        f.title or 'поле без названия',
                    ]
                    titles[i] = ' – '.join(t)
                else:
                    titles[i] = None
        else:
            titles[i] = None
    return JsonResponse(
        {
            "titles": titles,
        }
    )


@login_required
def descriptive_research(request):
    rows = DResearches.objects.filter(hide=False).filter(Q(is_paraclinic=True) | Q(is_doc_refferal=True) | Q(is_gistology=True)).order_by('title').values('pk', 'title')
    rows = [{"id": -1, "label": "НЕ ВЫБРАНО"}, *[{"id": x['pk'], "label": x["title"]} for x in rows]]
    return JsonResponse(rows, safe=False)


@login_required
def research_dispensary(request):
    rows = DResearches.objects.filter(hide=False, is_slave_hospital=False, is_hospital=False).order_by('title').values('pk', 'title')
    rows = [{"id": -1, "label": "НЕ ВЫБРАНО"}, *[{"id": x['pk'], "label": x["title"]} for x in rows]]
    return JsonResponse(rows, safe=False)


@login_required
def research_specialities(request):
    rows = Speciality.objects.filter(hide=False).order_by('title').values('pk', 'title')
    rows = [{"id": -1, "label": "НЕ ВЫБРАНО"}, *[{"id": x['pk'], "label": x["title"]} for x in rows]]
    return JsonResponse(rows, safe=False)


@login_required
def save_dispensary_data(request):
    request_data = json.loads(request.body)
    tb_data = request_data.get('tb_data', '')
    diagnos = request_data.get('diagnos', '')
    type_plan = request_data.get('typePlan', '')
    card_pk = int(request_data.get('card_pk', -1))
    for t_b in tb_data:
        if int(t_b.get('count', 0)) < 1:
            return JsonResponse({'message': 'Ошибка в количестве'})
    diagnos = diagnos.split(' ')[0]
    if type_plan == "Глобальный план" and diagnos:
        DispensaryPlan.objects.filter(diagnos=diagnos).delete()
        update_dispensary_plan_researches(DispensaryPlan, tb_data, diagnos, card_pk)

    if type_plan == "Индивидуальный план" and card_pk > 0:
        AdditionalPatientDispensaryPlan.objects.filter(card_id=card_pk).delete()
        update_dispensary_plan_researches(AdditionalPatientDispensaryPlan, tb_data, diagnos, card_pk)

    return JsonResponse({'ok': True, 'message': 'Сохранено'})


def update_dispensary_plan_researches(type_object, tb_data, diagnos, card_pk):
    for t_b in tb_data:
        research_obj = None
        speciality_obj = None
        if t_b.get('type') == 'Услуга':
            research_obj = DResearches.objects.get(pk=t_b['current_researches'])
        else:
            speciality_obj = Speciality.objects.get(pk=t_b['current_researches'])
        d = type_object(diagnos=diagnos, research=research_obj, repeat=t_b['count'], speciality=speciality_obj, is_visit=t_b.get('is_visit', False))
        if card_pk > 0:
            d.card_id = card_pk
        d.save()


@login_required
def load_research_by_diagnos(request):
    request_data = json.loads(request.body)
    diagnos_code = request_data.get('diagnos_code', '')
    type_plan = request_data.get('typePlan', 'Глобальный план')
    card_pk = int(request_data.get('card_pk', -1))
    d_plan = None
    diagnos = diagnos_code.split(' ')[0]
    if type_plan == "Глобальный план" and diagnos:
        d_plan = DispensaryPlan.objects.filter(diagnos=diagnos)
    if type_plan == "Индивидуальный план" and card_pk > 0:
        d_plan = AdditionalPatientDispensaryPlan.objects.filter(card_id=card_pk)

    rows = reserches_in_dplan(d_plan)
    return JsonResponse(rows, safe=False)


def reserches_in_dplan(d_plan):
    rows = []
    for d_p in d_plan:
        type = 'Услуга' if d_p.research else 'Врач'
        code_id = d_p.research.pk if d_p.research else d_p.speciality.pk
        rows.append({'type': type, 'is_visit': d_p.is_visit, 'current_researches': code_id, 'count': d_p.repeat})
    return rows


def required_stattalon_fields(request):
    return JsonResponse(REQUIRED_STATTALON_FIELDS)


def researches_required_stattalon_fields(request):
    return JsonResponse(RESEARCHES_PK_REQUIRED_STATTALON_FIELDS)


@login_required
def help_link_field(request):
    address_url = request.headers['Referer'].split(request.headers['Origin'])
    help_message = [{"param": "", "value": ""}]
    if address_url[1] == "/ui/construct/descriptive":
        help_message = constructor_help_message

    return JsonResponse({"data": help_message})
