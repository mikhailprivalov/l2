import datetime
from typing import List

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card, Individual
from doctor_call.models import DoctorCall
from hospitals.models import Hospitals
from laboratory.utils import current_time
from utils.data_verification import data_parse
from directory.models import Researches
import simplejson as json


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

    return JsonResponse(True, safe=False)


def external_create(request):
    fact_address, phone = '', ''

    enp, book_num, hospital_id = '', '', ''

    data = json.loads(request.body)
    family = data.get('family', '').title()
    name = data.get('given', '').title()
    patronymic = data.get('patronymic', '').title()
    gender = data.get('gender', '').lower()
    bdate = data.get('birthdate', '').split(' ')[0]
    enp = data.get('enp', '')
    idp = data.get('idp')
    birthday = datetime.datetime.strptime(bdate, "%d.%m.%Y" if '.' in bdate else "%Y-%m-%d").date()
    address = data.get('address', '').title().replace('Ул.', 'ул.').replace('Д.', 'д.').replace('Кв.', 'кв.')
    passport_number = data.get('passport_number', '')
    passport_seria = data.get('passport_seria', '')
    snils = data.get('snils', '')
    comment = data.get('comment', '')
    purpose = data.get('purpose', '')

    individual_obj = Individual.objects.filter(tfoms_idp='idp').first()
    if not individual_obj:
        Individual.import_from_tfoms(
            {
                'enp': enp,
                'family': family,
                'name': name,
                'patronymic': patronymic,
                'gender': gender,
                'bdate': birthday,
                'address': address,
                'passport_number': passport_number,
                'passport_seria': passport_seria,
                'snils': snils,
                'idp': idp,
            }
        )

    individual_obj = Individual.objects.filter(tfoms_idp='idp').first()
    card = Card.objects.filter(individual=individual_obj, base__internal_type=True).first()
    research_pk = Researches.objects.filter(title='Обращение пациента').first().values('pk')

    date, comment, purpose, hospital = '', '', '', ''
    if int(hospital_id) > 0:
        hospital = Hospitals.objects.filter(code_tfoms=int(hospital_id)).first()

    DoctorCall.doctor_call_save(
        {
            'card': card,
            'research': research_pk,
            'address': fact_address,
            'district': -1,
            'date': date,
            'comment': comment,
            'phone': phone,
            'doc': -1,
            'purpose': purpose,
            'hospital': hospital,
            'extrnal': True,
            'external_num': book_num,
        }
    )

    return JsonResponse({"ok": True})
