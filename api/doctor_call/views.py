import datetime
import json
from typing import List

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse

from appconf.manager import SettingManager
from slog.models import Log
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
        },
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

    #     if fact_address != card.fact_address:
    #         card.fact_address = fact_address
    #         card_updates.append('fact_address')

    if phone != card.phone:
        card.phone = phone
        card_updates.append('phone')

    if card_updates:
        card.save(update_fields=card_updates)

    for research_pk in researches:
        DoctorCall.doctor_call_save(
            {
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
                'external': False,
                'num_book': -1,
            },
            request.user.doctorprofile,
        )

    return JsonResponse({"ok": True})


@login_required
def actual_rows(request):
    data = data_parse(request.body, {'card_pk': int})
    card_pk: int = data[0]

    date_from = datetime.datetime.combine(current_time(), datetime.time.min)

    rows = list(
        DoctorCall.objects.filter(client_id=card_pk, exec_at__gte=date_from)
        .order_by('exec_at', 'pk')
        .values(
            'pk',
            'exec_at',
            'research__title',
            'comment',
            'cancel',
            'district__title',
            'address',
            'phone',
            'cancel',
            'doc_assigned__fio',
            'doc_assigned__podrazdeleniye__title',
            'purpose',
            'hospital__title',
            'hospital__short_title',
        )
    )

    return JsonResponse(rows, safe=False)


@login_required
def cancel_row(request):
    data = data_parse(request.body, {'pk': int})
    pk_row: int = data[0]
    row = DoctorCall.objects.get(pk=pk_row)
    row.cancel = not row.cancel
    row.save()

    Log(
        key=data[0],
        type=80004,
        body=json.dumps({"card_pk": row.client.pk, "status": row.cancel}),
        user=request.user.doctorprofile,
    ).save()

    return JsonResponse(True, safe=False)


@login_required
def search(request):
    request_data = json.loads(request.body)
    district = int(request_data.get("district", -1))
    cancel = request_data["is_canceled"]
    doc_assigned = int(request_data.get("doc", -1))
    purpose_id = int(request_data.get("purpose", -1))
    hospital = int(request_data.get("hospital_pk", -1))
    external = request_data.get("is_external")
    page = max(int(request_data.get("page", 1)), 1)

    date = request_data["date"]
    time_start = f'{date} {request_data.get("time_start", "00:00")}:00'
    time_end = f'{date} {request_data.get("time_end", "23:59")}:59'
    datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
    datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S')

    if external:
        doc_call = DoctorCall.objects.filter(
            create_at__range=[datetime_start, datetime_end],
        )
    else:
        doc_call = DoctorCall.objects.filter(create_at__range=[datetime_start, datetime_end])
    doc_call = doc_call.filter(is_external=external, cancel=cancel)

    if hospital > -1:
        doc_call = doc_call.filter(hospital__pk=hospital)
    if doc_assigned > -1:
        doc_call = doc_call.filter(doc_assigned__pk=doc_assigned)
    if district > -1:
        doc_call = doc_call.filter(district_id__pk=district)
    if purpose_id > -1:
        doc_call = doc_call.filter(purpose=purpose_id)

    if external:
        doc_call = doc_call.order_by('hospital', 'pk')
    elif hospital + doc_assigned + district + purpose_id > -4:
        doc_call = doc_call.order_by("pk")
    else:
        doc_call = doc_call.order_by("district__title")

    p = Paginator(doc_call, SettingManager.get("doc_call_page_size", default='30', default_type='i'))

    return JsonResponse({
        "rows": [
            x.json
            for x in p.page(page).object_list
        ],
        "page": page,
        "pages": p.num_pages,
        "total": p.count,
    })
