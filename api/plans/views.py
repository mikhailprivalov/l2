from datetime import datetime, time as dtime
import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from clients.models import Card
from laboratory.utils import strdate, current_time, strfdatetime
from plans.models import PlanOperations
from utils.xh import json_safe_parse
from .sql_func import get_plans_by_params_sql
from ..sql_func import users_by_group
from slog.models import Log


@login_required
def plan_operations_save(request):
    request_data = json.loads(request.body)
    ppk = PlanOperations.save_data(request_data, request.user.doctorprofile)

    return JsonResponse({"plan_pk": ppk})


@login_required
def plan_operations_cancel(request):
    request_data = json.loads(request.body)
    is_cancel = PlanOperations.cancel_operation(request_data, request.user.doctorprofile)

    return JsonResponse({"result": is_cancel})


@login_required
def get_plan_operations_by_patient(request):
    request_data = json.loads(request.body)
    start_date = datetime.combine(current_time(), dtime.min)
    patient_card = Card.objects.filter(pk=request_data['card_pk'])[0]
    result = PlanOperations.objects.filter(patient_card=patient_card, date__gte=start_date).order_by('date')
    data = [
        {
            'direction': i.direction,
            'hirurg': i.doc_operate.get_fio(),
            'hirurg_pk': i.doc_operate.pk,
            'date': strdate(i.date),
            'type_operation': i.type_operation,
            'pk_plan': i.pk,
            'cancel': i.canceled,
        }
        for i in result
    ]

    return JsonResponse({"data": data})


@login_required
def get_plan_operations_by_params(request):
    request_data = json.loads(request.body)
    start_date = datetime.strptime(request_data['start_date'], '%Y-%m-%d')
    start_date = datetime.combine(start_date, dtime.min)
    end_date = datetime.strptime(request_data['end_date'], '%Y-%m-%d')
    end_date = datetime.combine(end_date, dtime.max)
    doc_operate_pk = request_data.get('doc_operate_pk', -1)
    doc_anesthetist_pk = request_data.get('doc_anesthetist_pk', -1)
    department_pk = request_data.get('department_pk', -1)

    result = get_plans_by_params_sql(start_date, end_date, doc_operate_pk, doc_anesthetist_pk, department_pk)

    data = []
    for i in result:
        fio_patient = f"{i[8]} {i[9][0:1]}.{i[10][0:1]}."
        date_raw = i[3].split('.')
        date_raw = f"{date_raw[2]}-{date_raw[1]}-{date_raw[0]}"
        update_date = Log.objects.filter(key=i[0], type=80002)
        create_date = Log.objects.filter(key=i[0], type=80001)
        tooltip_data = []
        for c in create_date:
            doctor = c.user.get_fio()
            time = strfdatetime(c.time, '%d.%m.%y-%H:%M')
            tooltip_data.append(f'Создал: {doctor} ({time})')
        for u in update_date:
            doctor = u.user.get_fio()
            time = strfdatetime(u.time, '%d.%m.%y-%H:%M')
            tooltip_data.append(f"Обновил: {doctor} ({time})")

        data.append(
            {
                "pk_plan": i[0],
                "patient_card": i[1],
                "direction": i[2],
                "date": i[3],
                "date_raw": date_raw,
                "type_operation": i[4],
                "doc_operate_id": i[5],
                "doc_anesthetist_id": i[6] or -1,
                "canceled": i[7],
                "fio_patient": fio_patient,
                "birthday": i[11],
                "tooltip_data": '\n'.join(tooltip_data),
            }
        )

    return JsonResponse({"result": data})


@login_required
def get_departments_can_operate(request):
    users = users_by_group(['Оперирует'])

    departments = {}

    for row in users:
        if row[2] in departments:
            continue
        departments[row[2]] = {'id': row[2], 'label': row[4] or row[3]}

    return JsonResponse({"data": list(departments.values())})


@login_required
def change_anestesiolog(request):
    request_data = json.loads(request.body)
    plan_pk = request_data['plan_pk']
    doc_anesthetist_id = request_data['doc_anesthetist_pk']
    plan = PlanOperations.objects.get(pk=plan_pk)
    plan.doc_anesthetist_id = None if doc_anesthetist_id == -1 else doc_anesthetist_id
    plan.save()
    return JsonResponse({"ok": True})
