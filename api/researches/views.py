from collections import defaultdict

import simplejson as json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse

import users.models as users
from directory.models import (
    Researches as DResearches,
    ParaclinicInputGroups,
    Fractions,
    ParaclinicTemplateName,
    ParaclinicInputField,
    ParaclinicTemplateField,
    HospitalService,
    DispensaryPlan,
)
from laboratory.decorators import group_required
from podrazdeleniya.models import Podrazdeleniya
from researches.models import Tubes
from slog.models import Log
from users.models import Speciality


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

    return JsonResponse({"templates": templates})


def get_researches(request):
    deps = defaultdict(list)

    res = (
        DResearches.objects.filter(hide=False)
        .exclude(pk__in=[x.pk for x in request.user.doctorprofile.restricted_to_direct.all()])
        .select_related('podrazdeleniye', 'comment_variants')
        .prefetch_related('localization', 'service_location', 'a', 'b')
        .distinct()
        .order_by('title')
    )

    r: DResearches
    for r in res:
        autoadd = [x.b_id for x in r.a.all()]
        addto = [x.a_id for x in r.b.all()]

        deps[r.reversed_type].append(
            {
                "pk": r.pk,
                "onlywith": r.onlywith_id or -1,
                "department_pk": r.reversed_type,
                "title": r.get_title(),
                "full_title": r.title,
                "doc_refferal": r.is_doc_refferal,
                "treatment": r.is_treatment,
                "is_hospital": r.is_hospital,
                "stom": r.is_stom,
                "need_vich_code": r.need_vich_code,
                "comment_variants": [] if not r.comment_variants else r.comment_variants.get_variants(),
                "autoadd": autoadd,
                "addto": addto,
                "code": r.code,
                "type": "4" if not r.podrazdeleniye else str(r.podrazdeleniye.p_type),
                "site_type": r.get_site_type_id(),
                "site_type_raw": r.site_type_id,
                "localizations": [{"code": x.pk, "label": x.title} for x in r.localization.all()],
                "service_locations": [{"code": x.pk, "label": x.title} for x in r.service_location.all()],
            }
        )

    tubes = list(Tubes.objects.values('pk', 'title', 'color'))

    result = {"researches": deps, "tubes": tubes}

    return JsonResponse(result)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования", "Врач стационара")
def researches_by_department(request):
    direction_form = DResearches.DIRECTION_FORMS
    spec_data = [{"pk": -1, "title": "Не выбрано"}, *list(users.Speciality.objects.all().values('pk', 'title').order_by("title"))]
    response = {"researches": [], "direction_forms": direction_form, "specialities": spec_data}
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
        code = request_data.get("code", "").strip()
        internal_code = request_data.get("internal_code", "").strip()
        spec_pk = request_data.get("speciality", -1)
        speciality = Speciality.objects.filter(pk=spec_pk).first()
        direction_current_form = request_data.get("direction_current_form", 0)
        if not direction_current_form:
            direction_current_form = 0
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
        hospital_research_department_pk = request_data.get("hospital_research_department_pk", -1)
        if tube == -1:
            tube = None
        stationar_slave = is_simple and -500 >= department_pk > -600 and main_service_pk != 1
        desc = stationar_slave or department_pk in [-2, -3, -4, -5, -6, -7, -8]
        if len(title) > 0 and (desc or Podrazdeleniya.objects.filter(pk=department_pk).exists()):
            department = None if desc else Podrazdeleniya.objects.filter(pk=department_pk)[0]
            res = None
            if int(hospital_research_department_pk) > -1:
                department = Podrazdeleniya.objects.filter(pk=int(hospital_research_department_pk))[0]
            if pk == -1:
                res = DResearches(
                    title=title,
                    short_title=short_title,
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
                    is_slave_hospital=stationar_slave,
                    microbiology_tube_id=tube if department_pk == -6 else None,
                    site_type_id=site_type,
                    internal_code=internal_code,
                    direction_form=direction_current_form,
                    speciality=speciality,
                    bac_conclusion_templates=conclusion_templates,
                    bac_culture_comments_templates=culture_comments_templates,
                )
            elif DResearches.objects.filter(pk=pk).exists():
                res = DResearches.objects.filter(pk=pk)[0]
                res.title = title
                res.short_title = short_title
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
                res.microbiology_tube_id = tube if department_pk == -6 else None
                res.paraclinic_info = info
                res.hide = hide
                res.site_type_id = site_type
                res.internal_code = internal_code
                res.speciality = speciality
                res.direction_form = direction_current_form
                res.bac_conclusion_templates = conclusion_templates
                res.bac_culture_comments_templates = culture_comments_templates
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
                            title=group["title"], show_title=group["show_title"], research=res, order=group["order"], hide=group["hide"], visibility=group.get("visibility", "")
                        )
                    elif ParaclinicInputGroups.objects.filter(pk=pk).exists():
                        g = ParaclinicInputGroups.objects.get(pk=pk)
                        g.title = group["title"]
                        g.show_title = group["show_title"]
                        g.research = res
                        g.order = group["order"]
                        g.hide = group["hide"]
                        g.visibility = group.get("visibility", "")
                    if g:
                        g.save()
                        for field in group["fields"]:
                            f = None
                            pk = field["pk"]
                            if pk == -1:
                                f = ParaclinicInputField(
                                    title=field["title"],
                                    group=g,
                                    order=field["order"],
                                    lines=field["lines"],
                                    for_extract_card=field.get("for_extract_card", False),
                                    for_med_certificate=field.get("for_med_certificate", False),
                                    hide=field["hide"],
                                    default_value=field["default"],
                                    visibility=field.get("visibility", ""),
                                    input_templates=json.dumps(field["values_to_input"]),
                                    field_type=field.get("field_type", 0),
                                    helper=field.get("helper", ''),
                                    required=field.get("required", False),
                                    attached=field.get("attached", '')
                                )
                            elif ParaclinicInputField.objects.filter(pk=pk).exists():
                                f = ParaclinicInputField.objects.get(pk=pk)
                                f.title = field["title"]
                                f.group = g
                                f.order = field["order"]
                                f.lines = field["lines"]
                                f.for_extract_card = field.get("for_extract_card", False)
                                f.hide = field["hide"]
                                f.default_value = field["default"]
                                f.visibility = field.get("visibility", "")
                                f.input_templates = json.dumps(field["values_to_input"])
                                f.field_type = field.get("field_type", 0)
                                f.required = field.get("required", False)
                                f.for_talon = field.get("for_talon", False)
                                f.for_med_certificate = field.get("for_med_certificate", False)
                                f.helper = field.get("helper", '')
                                f.attached = field.get("attached", '')
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
    response = {"pk": -1, "department": -1, "title": '', "short_title": '', "code": '', "info": '', "hide": False, "groups": []}
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    if DResearches.objects.filter(pk=pk).exists():
        res: DResearches = DResearches.objects.get(pk=pk)
        response["pk"] = res.pk
        response["department"] = res.podrazdeleniye_id or (-2 if not res.is_hospital else -1)
        response["title"] = res.title
        response["short_title"] = res.short_title
        response["code"] = res.code
        response["info"] = res.paraclinic_info or ""
        response["hide"] = res.hide
        response["tube"] = res.microbiology_tube_id or -1
        response["site_type"] = res.site_type_id
        response["internal_code"] = res.internal_code
        response["direction_current_form"] = res.direction_form
        response["conclusionTpl"] = res.bac_conclusion_templates
        response["cultureTpl"] = res.bac_culture_comments_templates
        response["speciality"] = res.speciality_id or -1

        for group in ParaclinicInputGroups.objects.filter(research__pk=pk).order_by("order"):
            g = {"pk": group.pk, "order": group.order, "title": group.title, "show_title": group.show_title, "hide": group.hide, "fields": [], "visibility": group.visibility}
            for field in ParaclinicInputField.objects.filter(group=group).order_by("order"):
                g["fields"].append(
                    {
                        "pk": field.pk,
                        "order": field.order,
                        "lines": field.lines,
                        "for_extract_card": field.for_extract_card,
                        "title": field.title,
                        "default": field.default_value,
                        "visibility": field.visibility,
                        "hide": field.hide,
                        "values_to_input": json.loads(field.input_templates),
                        "field_type": field.field_type,
                        "required": field.required,
                        "for_talon": field.for_talon,
                        "for_med_certificate": field.for_med_certificate,
                        "helper": field.helper,
                        "new_value": "",
                        "attached": field.attached
                    }
                )
            response["groups"].append(g)
    return JsonResponse(response)


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
def paraclinic_details(request):
    response = {"groups": []}
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    for group in ParaclinicInputGroups.objects.filter(research__pk=pk).order_by("order"):
        g = {"pk": group.pk, "order": group.order, "title": group.title, "show_title": group.show_title, "hide": group.hide, "fields": []}
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
    return JsonResponse({"fraction": fraction.title, "research": fraction.research.title, "units": fraction.units})


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
    rows = DResearches.objects.filter(hide=False).filter(Q(is_paraclinic=True) | Q(is_doc_refferal=True)).order_by('title').values('pk', 'title')
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
    diagnos = diagnos.split(' ')[0]
    for t_b in tb_data:
        if int(t_b.get('count', 0)) < 1:
            return JsonResponse({'message': 'Ошибка в количестве'})

    DispensaryPlan.objects.filter(diagnos=diagnos).delete()
    for t_b in tb_data:
        research_obj = None
        speciality_obj = None
        if t_b.get('type') == 'Услуга':
            research_obj = DResearches.objects.get(pk=t_b['current_researches'])
        else:
            speciality_obj = Speciality.objects.get(pk=t_b['current_researches'])
        d = DispensaryPlan(diagnos=diagnos, research=research_obj, repeat=t_b['count'], speciality=speciality_obj, is_visit=t_b.get('is_visit', False))
        d.save()

    return JsonResponse({'ok':True, 'message': 'Сохранено'})


@login_required
def load_research_by_diagnos(request):
    request_data = json.loads(request.body)
    diagnos_code = request_data.get('diagnos_code', '')
    diagnos = diagnos_code.split(' ')[0]
    d_plan = DispensaryPlan.objects.filter(diagnos=diagnos)
    rows = []
    for d_p in d_plan:
        type = 'Услуга' if d_p.research else 'Врач'
        code_id = d_p.research.pk if d_p.research else d_p.speciality.pk
        rows.append({'type': type, 'is_visit': d_p.is_visit, 'current_researches': code_id, 'count': d_p.repeat})

    return JsonResponse(rows, safe=False)
