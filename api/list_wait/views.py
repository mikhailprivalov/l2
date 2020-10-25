import datetime
from typing import List

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card
from laboratory.utils import current_time
from list_wait.models import ListWait
from utils.data_verification import data_parse


@login_required
def create(request):
    data = data_parse(
        request.body,
        {'card_pk': 'card', 'comment': 'str_strip', 'date': str, 'researches': list}
    )

    card: Card = data[0]
    comment: str = data[1]
    date: str = data[2]
    researches: List[int] = data[3]

    for research_pk in researches:
        ListWait.list_wait_save({
            'card': card,
            'research': research_pk,
            'date': date,
            'comment': comment,
        }, request.user.doctorprofile)

    return JsonResponse({"ok": True})


@login_required
def actual_rows(request):
    data = data_parse(
        request.body,
        {'card_pk': int}
    )
    card_pk: int = data[0]

    date_from = datetime.datetime.combine(current_time(), datetime.time.min)

    rows = list(
        ListWait.objects.filter(client_id=card_pk, exec_at__gte=date_from)
        .order_by('exec_at', 'pk')
        .values('pk', 'exec_at', 'research__title', 'comment', 'work_status')
    )

    return JsonResponse(rows, safe=False)
