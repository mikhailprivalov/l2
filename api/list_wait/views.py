import datetime
from typing import List

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card
from directory.models import Researches
from laboratory.utils import current_time
from list_wait.models import ListWait
from plans.models import PlanHospitalization
from utils.data_verification import data_parse


@login_required
def create(request):
    print(request.body)
    data = data_parse(request.body, {'card_pk': 'card', 'comment': 'str_strip', 'date': str, 'researches': list, 'phone': 'str_strip'})

    card: Card = data[0]
    comment: str = data[1]
    date: str = data[2]
    researches: List[int] = data[3]
    phone: str = data[4]
    hosp_department_id = None

    if phone != card.phone:
        card.phone = phone
        card.save(update_fields=['phone'])

    hospital_researches = [r for r in Researches.objects.filter(pk__in=researches) if r.is_hospital]
    if len(hospital_researches) > 1:
        return JsonResponse({"ok": False})
    print(hospital_researches)

    if len(hospital_researches) == 1:
        if not hosp_department_id:
            hosp_department_id = hospital_researches[0].podrazdeleniye.pk
        PlanHospitalization.plan_hospitalization_save(
            {
                'card': card,
                'research': hospital_researches[0].pk,
                'date': date,
                'comment': comment,
                'phone': phone,
                'action': 0,
                'hospital_department_id': hosp_department_id
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

    return JsonResponse(rows, safe=False)
