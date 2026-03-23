import pytz_deprecation_shim as pytz
import simplejson as json
from django.db import transaction
from django.db.models import Prefetch
from django.http import JsonResponse

from api.procedure_list.sql_func import get_procedure_by_params, get_procedure_all_times
from api.stationar.stationar_func import forbidden_edit_dir, hosp_get_hosp_direction
from directions.models import Issledovaniya
from laboratory.utils import strfdatetime
from pharmacotherapy.models import ProcedureList, ProcedureListTimes, FormRelease, MethodsReception, DrugsTemplate, DrugsTemplatesRow, DrugsTemplatesRowsTime, DrugsTemplatesDepartment
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
from pharmacotherapy.sql_func import get_pharmacotherapy_exec_by_directions
from utils.dates import date_iter_range
from datetime import datetime, time as dtime
from utils.xh import get_hospitals_podrazdeleniya, get_all_hospitals
from directory.models import Researches
from laboratory.settings import TIME_ZONE

TIMES = [f"{x:02d}:00" for x in range(24)]


@login_required
@group_required("Врач стационара", "t, ad, p")
def get_procedure_by_dir(request):
    request_data = json.loads(request.body)
    dates = set()
    rows = []

    dates_times = {}
    procedure: ProcedureList
    for procedure in (
        ProcedureList.objects.filter(history_id=request_data["direction"], diary__issledovaniya__time_confirmation__isnull=False)
        .order_by('pk')
        .prefetch_related(Prefetch('procedurelisttimes_set', queryset=ProcedureListTimes.objects.all().order_by('times_medication')))
    ):
        row = {
            "pk": procedure.pk,
            "drug": str(procedure.drug),
            "created_at": strfdatetime(procedure.time_create, "%d.%m.%Y"),
            "form_release": str(procedure.form_release.title),
            "method": str(procedure.method.title),
            "dosage": f"{procedure.dosage} {procedure.units}".strip(),
            "cancel": bool(procedure.cancel),
            "who_cancel": None if not procedure.who_cancel else procedure.who_cancel.get_fio(),
            "comment": procedure.comment or None,
            "step": procedure.step or 1,
            "dates": {},
        }

        pt: ProcedureListTimes
        for pt in procedure.procedurelisttimes_set.all():
            date_str = strfdatetime(pt.times_medication.astimezone(pytz.timezone(TIME_ZONE)), "%d.%m.%Y")
            time_str = strfdatetime(pt.times_medication.astimezone(pytz.timezone(TIME_ZONE)), "%H:%M")
            if date_str not in dates_times:
                dates_times[date_str] = []
            if time_str not in dates_times[date_str]:
                dates_times[date_str].append(time_str)
                dates_times[date_str] = list(sorted(dates_times[date_str]))
            dates.add(pt.times_medication.astimezone(pytz.timezone(TIME_ZONE)).date())
            if date_str not in row["dates"]:
                row["dates"][date_str] = {}
            row["dates"][date_str][time_str] = {
                "datetime": f"{date_str} {time_str}",
                "pk": pt.pk,
                "empty": False,
                "ok": bool(pt.executor),
                "executor": None if not pt.executor else pt.executor.get_fio(),
                "cancel": bool(pt.cancel) or row["cancel"],
                "who_cancel": (None if not pt.who_cancel else pt.who_cancel.get_fio()) or row["who_cancel"],
            }
        rows.append(row)

    dates_all = []

    if dates:
        min_date = min(dates)
        max_date = max(dates)

        dates_all = [strfdatetime(x, "%d.%m.%Y") for x in date_iter_range(min_date, max_date, more_1=True)]

        for row in rows:
            for date in dates_all:
                if date not in dates_times:
                    continue
                if date not in row["dates"]:
                    row["dates"][date] = {}
                for t in dates_times[date]:
                    if t not in row["dates"][date]:
                        row["dates"][date][t] = {
                            "empty": True,
                            "datetime": f"{date} {t}",
                        }

    return JsonResponse({"result": rows, "dates": dates_all, "timesInDates": dates_times})


@login_required
@group_required("Врач стационара", "t, ad, p")
def procedure_cancel(request):
    request_data = json.loads(request.body)
    proc_obj = ProcedureList.objects.get(pk=request_data["pk"])
    forbidden_edit = forbidden_edit_dir(proc_obj.history_id)
    if forbidden_edit:
        return JsonResponse({"message": "Редактирование запрещено", "ok": False})
    proc_times = ProcedureListTimes.objects.filter(prescription=proc_obj, executor__isnull=True)
    canceled = 0
    for proc_time in proc_times:
        if request_data["cancel"]:
            proc_time.cancel = True
            proc_time.who_cancel = request.user.doctorprofile
            proc_time.save()
        else:
            proc_time.cancel = False
            proc_time.who_cancel = None
            proc_time.save()
        canceled += 1

    if request_data["cancel"]:
        proc_obj.cancel = True
        proc_obj.who_cancel = request.user.doctorprofile
    else:
        proc_obj.cancel = False
        proc_obj.who_cancel = None
    proc_obj.save()

    return JsonResponse({"message": f"{'Отменено' if request_data['cancel'] else 'Возвращено'} {canceled} записей времени", "ok": True})


def params(request):
    return JsonResponse(
        {
            "formReleases": list(FormRelease.objects.all().order_by('title').values('pk', 'title')),
            "methods": list(MethodsReception.objects.all().order_by('title').values('pk', 'title')),
            "times": TIMES,
            "units": [
                "мл",
                "мг",
                "мкг",
                "ед",
                "капля",
            ],
        }
    )


@login_required
@group_required("Врач стационара", "t, ad, p")
def procedure_execute(request):
    request_data = json.loads(request.body)
    proc_obj = ProcedureListTimes.objects.get(pk=request_data["pk"])
    forbidden_edit = forbidden_edit_dir(proc_obj.prescription.history_id)
    if forbidden_edit:
        return JsonResponse({"message": "Редактирование запрещено", "ok": False})
    if not proc_obj.cancel and not proc_obj.prescription.cancel:
        if request_data["status"]:
            proc_obj.executor = request.user.doctorprofile
            proc_obj.save()
            return JsonResponse({"message": "Приём записан", "ok": True})

        proc_obj.executor = None
        proc_obj.save()

        return JsonResponse({"message": "Приём убран", "ok": True})

    return JsonResponse({"message": "Приём не записан", "ok": False})


@login_required
@group_required("Врач стационара", "t, ad, p")
def procedure_aggregate(request):
    request_data = json.loads(request.body)
    start_date = datetime.strptime(request_data['start_date'], '%Y-%m-%d')
    start_date = datetime.combine(start_date, dtime.min)
    end_date = datetime.strptime(request_data['end_date'], '%Y-%m-%d')
    end_date = datetime.combine(end_date, dtime.max)
    department_pk = request_data.get('department_pk', -1)
    researches_pk = list(Researches.objects.values_list('pk', flat=True).filter(podrazdeleniye_id=int(department_pk)))
    if not researches_pk:
        return JsonResponse({"result": [], "dates": [], "timesInDates": {}})

    patient_procedures = get_procedure_by_params(start_date, end_date, researches_pk)
    all_times = get_procedure_all_times(start_date, end_date)

    empty = {k[0]: {'empty': True} for k in all_times}
    unique_dates = sorted(set([i[11] for i in patient_procedures]))
    data = {}
    for i in patient_procedures:
        card_pk = i[10]
        if card_pk not in data:
            data[card_pk] = {
                "pk": i[22],
                "card": card_pk,
                "patient": {"fio": i[8]},
                "drugs": {},
            }

        drug = i[1]
        form_release = i[3]
        method = i[4]
        unit = i[6]
        dosage = i[5]
        step = i[21]

        k = (drug, form_release, method, unit, dosage, step)

        if k not in data[card_pk]['drugs']:
            data[card_pk]['drugs'][k] = {
                'pk': i[22],
                'drug': drug,
                'created_at': i[2],
                'form_release': form_release,
                'method': method,
                'dosage': dosage,
                'step': step,
                'unit': unit,
                'cancel': i[23],
                'who_cancel': None,
                'history_num': i[17],
                'comment': i[18],
                'dates': {
                    d: {
                        t: {
                            **empty[t],
                            "datetime": f"{d} {t}",
                        }
                        for t in empty
                    }
                    for d in unique_dates
                },
            }
        data[card_pk]['drugs'][k]['dates'][i[11]][i[12]] = {
            'datetime': f'{i[11]} {i[12]}',
            'pk': i[0],
            'empty': False,
            'ok': bool(i[16]),
            'executor': i[16],
            'cancel': i[13],
            'who_cancel': i[20] or "",
            'history_num': i[17],
        }

    for card_pk in data:
        data[card_pk]['drugs'] = list(data[card_pk]['drugs'].values())

    unique_dates.sort(key=lambda x: datetime.strptime(x, '%d.%m.%Y'))

    times_in_dates = {d: [k[0] for k in all_times] for d in unique_dates}

    return JsonResponse({"result": list(data.values()), "dates": unique_dates, "timesInDates": times_in_dates})


@login_required
def get_suitable_departments(request):
    hospital_pk = request.user.doctorprofile.get_hospital_id()
    pdr = get_hospitals_podrazdeleniya(hospital_pk)
    hospitals = get_all_hospitals()
    data = {"data": pdr, "hospitals": hospitals}
    if hasattr(request, 'plain_response') and request.plain_response:
        return data
    return JsonResponse(data)


@login_required
def procedure_for_extract(request):
    request_data = json.loads(request.body)
    iss_pk = request_data.get('pk', -1)
    obj_iss = Issledovaniya.objects.get(pk=iss_pk)
    hosp_direction = hosp_get_hosp_direction(obj_iss.napravleniye_id)
    result_dir = [i["direction"] for i in hosp_direction]
    pharma_result = get_pharmacotherapy_exec_by_directions(tuple(result_dir))

    prev_prescription = None
    step = 0
    tmp_prescription = {"pharmaTitle": "", "mode": ""}
    result = []
    for i in pharma_result:
        if i.prescription_id != prev_prescription and step != 0:
            tmp_result = ""
            for k, v in tmp_prescription["mode"].items():
                tmp_result = f"{tmp_result} {k}-{len(v)}р/д; "
            tmp_prescription["mode"] = tmp_result
            result.append(tmp_prescription.copy())
            tmp_prescription = {"pharmaTitle": "", "mode": ""}

        title = i.mnn if i.mnn else i.trade_name
        current_title = f"{title} {i.form_title} {i.method_title} {i.dosage} {i.units} {i.comment}"
        if tmp_prescription["pharmaTitle"] != current_title:
            tmp_prescription["pharmaTitle"] = current_title
            tmp_prescription["mode"] = {i.date_char: []}
        current_time = tmp_prescription["mode"].get(i.date_char, [])
        current_time.append(i.time_char)
        tmp_prescription["mode"][i.date_char] = current_time.copy()
        step += 1
        prev_prescription = i.prescription_id

    tmp_result = ""
    for k, v in tmp_prescription["mode"].items():
        tmp_result = f"{tmp_result} {k} {len(v)} р/д;"
    tmp_prescription["mode"] = tmp_result
    result.append(tmp_prescription.copy())

    return JsonResponse({"data": result})


@login_required
def get_templates(request):
    doctor_profile = request.user.doctorprofile
    templates = DrugsTemplate.get_templates(doctor_profile, doctor_profile.podrazdeleniye)
    return JsonResponse({"data": templates})


@login_required()
def get_selected_template_data(request):
    request_data = json.loads(request.body)
    result = [{
        'drug': {
            'pk': row.drug.pk,
            'title': str(row.drug),
        },
        'form_release': row.form_release.pk,
        'method': row.method.pk,
        'dosage': row.dosage,
        'units': row.units,
        'days_count': row.days_count,
        'step': row.step,
        'comment': row.comment,
        'times': [time.times_medication for time in row.times]
    } for row in DrugsTemplatesRow.objects.filter(
        template_id=request_data['template_id']
    ).select_related(
        'drug',
        'form_release',
        'method'
    ).prefetch_related(
        Prefetch(
            'dtr_number',
            queryset=DrugsTemplatesRowsTime.objects.all(),
            to_attr='times'
        )
    )]

    return JsonResponse({"data": result})


def check_template(title, doctor_profile):
    if template := DrugsTemplate.objects.filter(title=title).first():
        my_template = False
        if template.doc_create == doctor_profile:
            my_template = True

        if my_template:
            return {"template_access": True, "template_exists": True, "message": "Шаблон доступен для изменения"}
        else:
            return {"template_access": False, "template_exists": True, "message": "Шаблон вам не принадлежит"}
    else:
        return {"template_exists": False, "message": "Шаблон доступен для сохранения"}


@login_required()
def find_template_for_edit_or_add(request):
    request_data = json.loads(request.body)
    result = check_template(request_data['template_title'], request.user.doctorprofile)
    if result.get("template_exists") is False and 'template_access' not in request_data:
        return JsonResponse({
            "template_exists": result.get("template_exists"),
            "message": result.get("message"),
        })
    else:
        return JsonResponse({
            "template_access": result.get("template_access"),
            "template_exists": result.get("template_exists"),
            "message": result.get("message")
        })


def template_add_rows(template_pk, rows):
    with transaction.atomic():
        for row in rows:
            template_row = DrugsTemplatesRow(
                template_id=template_pk,
                drug_id=row['drugPk'],
                form_release_id=row['form_release'],
                method_id=row['method'],
                dosage=row['dosage'],
                units=row['units'],
                days_count=row['countDays'],
                step=row['step'],
                comment=row['comment'],
            )
            template_row.save()
            if row['timesSelected']:
                for time in row['timesSelected']:
                    row_time = DrugsTemplatesRowsTime(
                        row_id=template_row.pk,
                        times_medication=time,
                    )
                    row_time.save()


@login_required()
def add_template(request):
    request_data = json.loads(request.body)
    template_check = check_template(request_data['template_title'], request.user.doctorprofile)
    if template_check.get("template_exists") is False and 'template_access' not in template_check:
        try:
            template = DrugsTemplate(
                title=request_data['template_title'],
                doc_create=request.user.doctorprofile,
                who_update=request.user.doctorprofile,
            )
            template.save()
            template_add_rows(template.pk, request_data['rows'])
            template_department = DrugsTemplatesDepartment(
                template_id=template.pk,
                department=request.user.doctorprofile.podrazdeleniye,
            )
            template_department.save()
            return JsonResponse({'message': 'Шаблон успешно сохранен'})
        except:
            return JsonResponse({'error': 'Ошибка при сохранении шаблона'})
    else:
        return JsonResponse({'warning': 'Шаблон уже существует'})


@login_required()
def edit_template(request):
    request_data = json.loads(request.body)
    template_check = check_template(request_data['template_title'], request.user.doctorprofile)
    if template_check.get("template_exists") is True and template_check.get("template_access") is True:
        try:
            template = DrugsTemplate.objects.get(title=request_data['template_title'])
            template_rows = DrugsTemplatesRow.objects.filter(template_id=template.pk)
            template_rows.delete()
            template_add_rows(template.pk, request_data['rows'])
            template.who_update = request.user.doctorprofile
            template.save()
            return JsonResponse({'message': 'Шаблон успешно изменен'})
        except:
            return JsonResponse({'error': 'Ошибка при изменении шаблона'})
    else:
        return JsonResponse({'error': 'Нет прав для изменения'})
