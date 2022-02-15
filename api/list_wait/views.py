import datetime
from typing import List, Optional

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card
from directory.models import Researches
from doctor_schedule.views import check_available_hospital_slot_before_save
from laboratory.utils import current_time, localtime
from list_wait.models import ListWait
from plans.models import PlanHospitalization
from utils.data_verification import data_parse


@login_required
def create(request):
    data = data_parse(
        request.body,
        {'card_pk': 'card', 'comment': 'str_strip', 'date': str, 'researches': list, 'phone': 'str_strip', 'hospitalDepartment': int, 'diagnosis': 'str_strip'},
        {'hospitalDepartment': None, 'diagnosis': None},
    )

    card: Card = data[0]
    comment: str = data[1]
    date: str = data[2]
    researches: List[int] = data[3]
    phone: str = data[4]
    hosp_department_id: Optional[int] = data[5]
    diagnosis: Optional[str] = data[6]

    if phone != card.phone:
        card.phone = phone
        card.save(update_fields=['phone'])

    hospital_researches = [r for r in Researches.objects.filter(pk__in=researches) if r.is_hospital]
    if len(hospital_researches) > 1:
        return JsonResponse({"ok": False, "message": "Выбрано больше одной услуги"})

    if len(hospital_researches) == 1:
        if not hosp_department_id:
            hosp_department_id = hospital_researches[0].podrazdeleniye.pk
        has_free_slots = check_available_hospital_slot_before_save(hospital_researches[0].pk, None, date)
        if not has_free_slots:
            return JsonResponse({"ok": False, "message": "Нет свободных слотов"})
        PlanHospitalization.plan_hospitalization_save(
            {
                'card': card,
                'research': hospital_researches[0].pk,
                'date': date,
                'comment': comment,
                'phone': phone,
                'action': 0,
                'hospital_department_id': hosp_department_id,
                'diagnos': diagnosis,
            },
            request.user.doctorprofile,
        )
    else:
        for research_pk in researches:
            ListWait.list_wait_save(
                {
                    'card': card,
                    'research': research_pk,
                    'date': date,
                    'comment': comment,
                    'phone': phone,
                },
                request.user.doctorprofile,
            )

    return JsonResponse({"ok": True})


@login_required
def actual_rows(request):
    data = data_parse(request.body, {'card_pk': int})
    card_pk: int = data[0]

    date_from = datetime.datetime.combine(current_time(), datetime.time.min)

    rows = list(ListWait.objects.filter(client_id=card_pk, exec_at__gte=date_from).order_by('exec_at', 'pk').values('pk', 'exec_at', 'research__title', 'comment', 'work_status', 'phone'))
    p: PlanHospitalization
    for p in PlanHospitalization.objects.filter(client_id=card_pk, exec_at__gte=date_from, action=0).order_by('exec_at', 'pk'):
        if p.slot_fact:
            slot_datetime = f"{datetime.datetime.strftime(localtime(p.slot_fact.plan.datetime), '%d.%m.%Y %H:%M')}, {p.slot_fact.plan.duration_minutes} мин."
        elif p.why_cancel:
            slot_datetime = p.why_cancel
        else:
            slot_datetime = "Ожидает решение"
        rows.append({
            "pk": p.pk,
            "pk_plan": p.pk,
            "exec_at": p.exec_at,
            "date": p.exec_at,
            "research_id": p.research_id,
            "research__title": p.research.title,
            "research_title": p.research.title,
            "comment": p.comment,
            "work_status": p.work_status,
            "phone": p.phone,
            "diagnos": p.diagnos,
            "hospital_department__title": p.hospital_department.title,
            "slot": slot_datetime,
            "patient_card": card_pk,
            "fio_patient": p.client.individual.fio(),
            "canceled": p.work_status == 2,
        })

    return JsonResponse(rows, safe=False)
