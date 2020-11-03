import datetime
from typing import List

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card
from doctor_call.models import DoctorCall
from laboratory.utils import current_time
from utils.data_verification import data_parse


@login_required
def create(request):
    data = data_parse(
        request.body,
        {
            'card_pk': 'card',
            'comment': 'str_strip',
            'date': str,
            'district': int,
            'fact_address': 'str_strip',
            'researches': list,
            'phone': 'str_strip',
            'doc': int,
            'purpose': int,
            'hospital': int,
        }
    )

    card: Card = data[0]
    comment: str = data[1]
    date: str = data[2]
    district: int = data[3]
    fact_address: str = data[4]
    researches: List[int] = data[5]
    phone: str = data[6]
    doc: int = data[7]
    purpose: int = data[8]
    hospital: int = data[9]

    card_updates = []
    if district != (card.district_id or -1):
        card.district_id = district if district > -1 else None
        card_updates.append('district_id')

    if fact_address != card.fact_address:
        card.fact_address = fact_address
        card_updates.append('fact_address')

    if phone != card.phone:
        card.phone = phone
        card_updates.append('phone')

    if card_updates:
        card.save(update_fields=card_updates)

    for research_pk in researches:
        DoctorCall.doctor_call_save({
            'card': card,
            'research': research_pk,
            'address': fact_address,
            'district': district,
            'date': date,
            'comment': comment,
            'phone': phone,
            'doc': doc,
            'purpose': purpose,
            'hospital': hospital,
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
        DoctorCall.objects.filter(client_id=card_pk, exec_at__gte=date_from)
        .order_by('exec_at', 'pk')
        .values(
            'pk', 'exec_at', 'research__title', 'comment', 'cancel', 'district__title',
            'address', 'phone', 'cancel', 'doc_assigned__fio', 'doc_assigned__podrazdeleniye__title', 'purpose',
            'hospital__title', 'hospital__short_title',
        )
    )

    return JsonResponse(rows, safe=False)


@login_required
def cancel_row(request):
    data = data_parse(
        request.body,
        {'pk': int}
    )
    pk_row: int = data[0]
    row = DoctorCall.objects.get(pk=pk_row)
    row.cancel = not row.cancel
    row.save()

    return JsonResponse(True, safe=False)
