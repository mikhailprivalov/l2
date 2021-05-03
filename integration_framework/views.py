import datetime
import logging
import random
from collections import defaultdict

import simplejson as json
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

import directions.models as directions
from appconf.manager import SettingManager
from clients.models import Individual, Card
from directory.models import Researches, Fractions, ReleationsFT
from doctor_call.models import DoctorCall
from hospitals.models import Hospitals
from laboratory.settings import AFTER_DATE, MAX_DOC_CALL_EXTERNAL_REQUESTS_PER_DAY
from laboratory.utils import current_time
from refprocessor.result_parser import ResultRight
from researches.models import Tubes
from rmis_integration.client import Client
from slog.models import Log
from tfoms.integration import match_enp, match_patient
from users.models import DoctorProfile
from utils.data_verification import data_parse
from utils.dates import normalize_date, valid_date
from . import sql_if
from directions.models import Napravleniya


logger = logging.getLogger("IF")


@api_view()
def next_result_direction(request):
    from_pk = request.GET.get("fromPk")
    after_date = request.GET.get("afterDate")
    if after_date == '0':
        after_date = AFTER_DATE
    next_n = int(request.GET.get("nextN", 1))
    type_researches = request.GET.get("research", '*')
    d_start = f'{after_date}'
    dirs = sql_if.direction_collect(d_start, type_researches, next_n) or []

    next_time = None
    naprs = [d[0] for d in dirs]
    if dirs:
        next_time = dirs[-1][3]

    return Response({"next": naprs, "next_time": next_time, "n": next_n, "fromPk": from_pk, "afterDate": after_date})


@api_view()
def get_dir_amd(request):
    next_n = int(request.GET.get("nextN", 5))
    dirs = sql_if.direction_resend_amd(next_n)
    result = {"ok": False, "next": []}
    if dirs:
        result = {"ok": True, "next": [i[0] for i in dirs]}

    return Response(result)


@api_view()
def get_dir_n3(request):
    next_n = int(request.GET.get("nextN", 5))
    dirs = sql_if.direction_resend_n3(next_n)
    result = {"ok": False, "next": []}
    if dirs:
        result = {"ok": True, "next": [i[0] for i in dirs]}

    return Response(result)


@api_view()
def resend_dir_l2(request):
    next_n = int(request.GET.get("nextN", 5))
    dirs = sql_if.direction_resend_l2(next_n)
    result = {"ok": False, "next": []}
    if dirs:
        result = {"ok": True, "next": [i[0] for i in dirs]}

    return Response(result)


@api_view()
def result_amd_send(request):
    result = json.loads(request.GET.get("result"))
    resp = {"ok": False}
    if result['error']:
        for i in result['error']:
            dir_pk = int(i.split(':')[0])
            directions.Napravleniya.objects.filter(pk=dir_pk).update(need_resend_amd=False, error_amd=True)
        resp = {"ok": True}
    if result['send']:
        for i in result['send']:
            data_amd = i.split(':')
            dir_pk = int(data_amd[0])
            amd_num = data_amd[1]
            directions.Napravleniya.objects.filter(pk=dir_pk).update(need_resend_amd=False, amd_number=amd_num, error_amd=False)
        resp = {"ok": True}

    return Response(resp)


@api_view()
def direction_data(request):
    pk = request.GET.get("pk")
    research_pks = request.GET.get("research", '*')
    direction = directions.Napravleniya.objects.select_related('istochnik_f', 'client', 'client__individual', 'client__base').get(pk=pk)
    card = direction.client
    individual = card.individual

    iss = directions.Issledovaniya.objects.filter(napravleniye=direction, time_confirmation__isnull=False).select_related('research', 'doc_confirmation')
    if research_pks != '*':
        iss = iss.filter(research__pk__in=research_pks.split(','))

    if not iss:
        return Response({"ok": False})

    iss_index = random.randrange(len(iss))

    return Response(
        {
            "ok": True,
            "pk": pk,
            "createdAt": direction.data_sozdaniya,
            "patient": {
                **card.get_data_individual(full_empty=True, only_json_serializable=True),
                "family": individual.family,
                "name": individual.name,
                "patronymic": individual.patronymic,
                "birthday": individual.birthday,
                "sex": individual.sex,
                "card": {"base": {"pk": card.base_id, "title": card.base.title, "short_title": card.base.short_title}, "pk": card.pk, "number": card.number},
            },
            "issledovaniya": [x.pk for x in iss],
            "timeConfirmation": iss[iss_index].time_confirmation,
            "docLogin": iss[iss_index].doc_confirmation.rmis_login if iss[iss_index].doc_confirmation else None,
            "docPassword": iss[iss_index].doc_confirmation.rmis_password if iss[iss_index].doc_confirmation else None,
            "department_oid": iss[iss_index].doc_confirmation.podrazdeleniye.oid if iss[iss_index].doc_confirmation else None,
            "finSourceTitle": direction.istochnik_f.title if direction.istochnik_f else 'ОМС',
            "oldPk": direction.core_id,
            "isExternal": direction.is_external,
        }
    )


def format_time_if_is_not_none(t):
    if not t:
        return None
    return "{:%Y-%m-%d %H:%M}".format(t)


@api_view()
def issledovaniye_data(request):
    pk = request.GET.get("pk")
    ignore_sample = request.GET.get("ignoreSample") == 'true'
    i = directions.Issledovaniya.objects.get(pk=pk)

    sample = directions.TubesRegistration.objects.filter(issledovaniya=i, time_get__isnull=False).first()
    results = directions.Result.objects.filter(issledovaniye=i, fraction__fsli__isnull=False)

    if (not ignore_sample and not sample) or not results.exists():
        return Response({"ok": False})

    results_data = []

    for r in results:
        refs = r.calc_normal(only_ref=True, raw_ref=False)

        if isinstance(refs, ResultRight):
            if refs.mode == ResultRight.MODE_CONSTANT:
                refs = [refs.const_orig]
            else:
                refs_list = [str(refs.range.val_from.value), str(refs.range.val_to.value)]
                if refs_list[0] == '-inf':
                    refs = [f'до {refs_list[1]}']
                elif refs_list[1] == 'inf':
                    refs = [f'от {refs_list[0]}']
                elif refs_list[0] == refs_list[1]:
                    refs = [refs.const_orig]
        else:
            refs = [r.calc_normal(only_ref=True) or '']

        results_data.append(
            {
                "pk": r.pk,
                "fsli": r.fraction.get_fsli_code(),
                "value": r.value.replace(',', '.'),
                "units": r.get_units(),
                "ref": refs,
            }
        )

    time_confirmation = i.time_confirmation_local

    return Response(
        {
            "ok": True,
            "pk": pk,
            "sample": {"date": sample.time_get.date() if sample else i.time_confirmation.date()},
            "date": time_confirmation.date(),
            "dateTimeGet": format_time_if_is_not_none(sample.time_get_local) if sample else None,
            "dateTimeReceive": format_time_if_is_not_none(sample.time_recive_local) if sample else None,
            "dateTimeConfirm": format_time_if_is_not_none(time_confirmation),
            "docConfirm": i.doc_confirmation_fio,
            "results": results_data,
            "code": i.research.code,
            "comments": i.lab_comment,
        }
    )


@api_view()
def issledovaniye_data_multi(request):
    pks = request.GET["pks"].split(",")
    ignore_sample = request.GET.get("ignoreSample") == 'true'
    iss = (
        directions.Issledovaniya.objects.filter(pk__in=pks)
        .select_related('doc_confirmation', 'research')
        .prefetch_related(Prefetch('result_set', queryset=(directions.Result.objects.filter(fraction__fsli__isnull=False).select_related('fraction'))))
        .prefetch_related(Prefetch('tubes', queryset=(directions.TubesRegistration.objects.filter(time_get__isnull=False))))
    )

    result = []

    i: directions.Issledovaniya

    for i in iss:
        sample = i.tubes.all().first()

        if (not ignore_sample and not sample) or not i.result_set.all().exists():
            continue

        results_data = []

        for r in i.result_set.all():
            refs = r.calc_normal(only_ref=True, raw_ref=False)

            if isinstance(refs, ResultRight):
                if refs.mode == ResultRight.MODE_CONSTANT:
                    refs = [refs.const]
                else:
                    refs = [str(refs.range.val_from.value), str(refs.range.val_to.value)]
                    if refs[0] == '-inf':
                        refs = [f'до {refs[1]}']
                    elif refs[1] == 'inf':
                        refs = [f'от {refs[0]}']
                    elif refs[0] == refs[1]:
                        refs = [refs[0]]
            else:
                refs = [r.calc_normal(only_ref=True) or '']

            results_data.append(
                {
                    "pk": r.pk,
                    "fsli": r.fraction.get_fsli_code(),
                    "value": r.value.replace(',', '.'),
                    "units": r.get_units(),
                    "ref": refs,
                }
            )

        time_confirmation = i.time_confirmation_local

        result.append(
            {
                "pk": i.pk,
                "sample": {"date": sample.time_get.date() if sample else i.time_confirmation.date()},
                "date": time_confirmation.date(),
                "dateTimeGet": format_time_if_is_not_none(sample.time_get_local) if sample else None,
                "dateTimeReceive": format_time_if_is_not_none(sample.time_recive_local) if sample else None,
                "dateTimeConfirm": format_time_if_is_not_none(time_confirmation),
                "docConfirm": i.doc_confirmation_fio,
                "results": results_data,
                "code": i.research.code,
                "comments": i.lab_comment,
            }
        )
    return Response(
        {
            "ok": len(result) > 0,
            "pks": pks,
            "results": result,
        }
    )


@api_view(['GET'])
def make_log(request):
    key = request.GET.get("key")
    keys = request.GET.get("keys", key).split(",")
    t = int(request.GET.get("type"))
    body = {}

    if request.method == "POST":
        body = json.loads(request.body)

    pks_to_resend_n3_false = [x for x in keys if x] if t in (60000, 60001, 60002, 60003) else []
    pks_to_resend_l2_false = [x for x in keys if x] if t in (60004, 60005) else []

    with transaction.atomic():
        directions.Napravleniya.objects.filter(pk__in=pks_to_resend_n3_false).update(need_resend_n3=False)
        directions.Napravleniya.objects.filter(pk__in=pks_to_resend_l2_false).update(need_resend_l2=False)

        for k in pks_to_resend_n3_false:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_resend_l2_false:
            Log.log(key=k, type=t, body=body.get(k, {}))

    return Response({"ok": True})


@api_view(['POST'])
def check_enp(request):
    enp, family, name, patronymic, bd, enp_mode =\
        data_parse(
            request.body,
            {'enp': str, 'family': str, 'name': str, 'patronymic': str, 'bd': str, 'check_mode': str},
            {'check_mode': 'tfoms', 'bd': None, 'name': None, 'patronymic': None, 'family': None, 'enp': None}
        )
    enp = enp.replace(' ', '')

    logger.exception(f'enp_mode: {enp_mode}')

    if enp_mode == 'l2-enp':
        tfoms_data = match_enp(enp)

        if tfoms_data:
            return Response({"ok": True, 'patient_data': tfoms_data})
    elif enp_mode == 'l2-enp-full':
        patronymic = patronymic if patronymic != 'None' else None
        logger.exception(f'data: {(family, name, patronymic, bd)}')
        tfoms_data = match_patient(family, name, patronymic, bd)

        if tfoms_data:
            return Response({"ok": True, 'list': tfoms_data})
    elif enp_mode == 'tfoms':
        tfoms_data = match_enp(enp)

        logger.exception(f'tfoms data: {json.dumps(tfoms_data)}')

        if tfoms_data:
            bdate = tfoms_data.get('birthdate', '').split(' ')[0]
            if normalize_date(bd) == normalize_date(bdate):
                return Response({"ok": True, 'patient_data': tfoms_data})
    elif enp_mode == 'rmis':
        logger.exception(f'enp: {enp}')
        c = Client(modules=['patients'])
        card = c.patients.get_l2_card_by_enp(enp)
        if card:
            logger.exception(f'card: {card}')
            i: Individual = card.individual
            bd_orig = f"{i.birthday:%Y-%m-%d}"
            logger.exception(f'{bd_orig} == {bd}')
            if bd_orig == bd:
                return Response(
                    {
                        "ok": True,
                        'patient_data': {
                            "rmis_id": card.individual.get_rmis_uid_fast(),
                        },
                    }
                )

    return Response({"ok": False, 'message': 'Неверные данные или нет прикрепления к поликлинике'})


@api_view(['POST'])
def patient_results_covid19(request):
    rmis_id = data_parse(request.body, {'rmis_id': str})[0]

    logger.exception(f'patient_results_covid19: {rmis_id}')

    c = Client(modules=['directions', 'rendered_services'])

    now = current_time().date()
    days = 15
    variants = ['РНК вируса SARS-CоV2 не обнаружена', 'РНК вируса SARS-CоV2 обнаружена']

    results = []

    for i in range(days):
        date = now - datetime.timedelta(days=i)
        rendered_services = c.rendered_services.client.searchServiceRend(patientUid=rmis_id, dateFrom=date)

        for rs in rendered_services[:5]:
            protocol = c.directions.get_protocol(rs)
            for v in variants:
                if v in protocol:
                    results.append({'date': date.strftime('%d.%m.%Y'), 'result': v})
                    break

    return Response({"ok": True, 'results': results})


@api_view(['POST'])
def external_doc_call_create(request):
    data = json.loads(request.body)
    org_id = data.get('org_id')
    patient_data = data.get('patient_data')
    form = data.get('form')
    idp = patient_data.get('idp')
    enp = patient_data.get('enp')
    comment = form.get('comment')
    purpose = form.get('purpose')
    email = form.get('email')
    external_num = form.get('external_num')
    is_main_external = form.get('is_main_external')

    if email == 'undefined':
        email = None

    logger.exception(f'external_doc_call_create: {org_id} {json.dumps(patient_data)} {json.dumps(form)} {idp} {enp} {comment} {purpose} {email} {external_num}')

    Individual.import_from_tfoms(patient_data)
    individuals = Individual.objects.filter(Q(tfoms_enp=enp or '###$fakeenp$###') | Q(tfoms_idp=idp or '###$fakeidp$###'))

    individual_obj = individuals.first()
    if not individual_obj:
        return JsonResponse({"ok": False, "number": None})

    card = Card.objects.filter(individual=individual_obj, base__internal_type=True).first()
    research = Researches.objects.filter(title='Обращение пациента').first()
    hospital = Hospitals.objects.filter(code_tfoms=org_id).first()

    if not card or not research or not hospital:
        return JsonResponse({"ok": False, "number": None})

    date = current_time()

    count = DoctorCall.objects.filter(
        client=card, is_external=True,
        exec_at__date=date.date()
    ).count()
    if count >= MAX_DOC_CALL_EXTERNAL_REQUESTS_PER_DAY:
        logger.exception(f'TOO MANY REQUESTS PER DAY: already have {count} calls at {date:%d.%m.%Y}')
        return JsonResponse({"ok": False, "number": None, "tooManyRequests": True})

    research_pk = research.pk

    doc_call = DoctorCall.doctor_call_save(
        {
            'card': card,
            'research': research_pk,
            'address': card.main_address,
            'district': -1,
            'date': date,
            'comment': comment,
            'phone': form.get('phone'),
            'doc': -1,
            'purpose': int(purpose),
            'hospital': hospital.pk,
            'external': True,
            'email': email,
            'external_num': external_num,
            'is_main_external': bool(is_main_external),
        }
    )
    if is_main_external:
        doc_call.external_num = doc_call.num
    elif SettingManager.l2('send_doc_calls'):
        doc_call.external_num = f"{org_id}{doc_call.pk}"
    doc_call.save()

    return Response({"ok": True, "number": doc_call.external_num})


@api_view(['POST'])
def external_doc_call_update_status(request):
    if not hasattr(request.user, 'hospitals'):
        return Response({"ok": False, 'message': 'Некорректный auth токен'})

    body = json.loads(request.body)

    external_num = body.get("externalNum")
    status = body.get("status")
    org = body.get("org")
    code_tfoms = org.get("codeTFOMS")
    oid_org = org.get("oid")

    if not external_num:
        return Response({"ok": False, 'message': 'externalNum не указан'})

    if not status:
        return Response({"ok": False, 'message': 'status не указан'})

    if not code_tfoms and not oid_org:
        return Response({"ok": False, 'message': 'Должно быть указано хотя бы одно значение из org.codeTFOMS или org.oid'})

    if code_tfoms:
        hospital = Hospitals.objects.filter(code_tfoms=code_tfoms).first()
    else:
        hospital = Hospitals.objects.filter(oid=oid_org).first()

    if not hospital:
        return Response({"ok": False, 'message': 'Организация не найдена'})

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return Response({"ok": False, 'message': 'Нет доступа в переданную организацию'})

    if not hospital:
        return Response({"ok": False, 'message': 'Организация не найдена'})

    status = str(status)
    if not status.isdigit():
        return Response({"ok": False, 'message': 'Некорректный status'})

    status = int(status)
    if status not in [x[0] for x in DoctorCall.STATUS]:
        return Response({"ok": False, 'message': 'Некорректный status'})

    num = str(external_num)
    if not num.startswith('XR'):
        return Response({"ok": False, 'message': 'Некорректный externalNum'})

    num = num.replace('XR', '')
    if not num.isdigit():
        return Response({"ok": False, 'message': 'Некорректный externalNum'})

    call: DoctorCall = DoctorCall.objects.filter(pk=num).first()
    if not call:
        return Response({"ok": False, 'message': f'Заявка с номером {num} не найдена'})

    call.status = status
    call.save(update_fields=['status'])
    return Response({"ok": True})


@api_view(['POST'])
def external_doc_call_send(request):
    data = json.loads(request.body)
    patient_data = data.get('patient_data')
    form = data.get('form')
    enp = patient_data.get('enp')
    address = patient_data.get('address')
    comment = form.get('comment')
    purpose = form.get('purpose_id')
    email = form.get('email')
    external_num = form.get('num')

    logger.exception(f'external_doc_call_send: {json.dumps(patient_data)} {json.dumps(form)} {enp} {comment} {purpose} {email} {external_num}')

    individuals = Individual.objects.filter(tfoms_enp=enp)
    if not individuals.exists():
        individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title='Полис ОМС') | Q(document__document_type__title='ЕНП'))
    if not individuals.exists():
        tfoms_data = match_enp(enp)
        if not tfoms_data:
            return Response({"ok": False, 'message': 'Неверные данные полиса, в базе ТФОМС нет такого пациента'})
        Individual.import_from_tfoms(tfoms_data)
        individuals = Individual.objects.filter(tfoms_enp=enp)

    individual = individuals.first()
    if not individual:
        return Response({"ok": False, 'message': 'Физлицо не найдено'})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    research = Researches.objects.filter(title='Обращение пациента').first()
    hospital = Hospitals.get_default_hospital()

    if not card or not research or not hospital:
        return JsonResponse({"ok": False, "number": None})

    research_pk = research.pk

    doc_call = DoctorCall.doctor_call_save(
        {
            'card': card,
            'research': research_pk,
            'address': address,
            'district': -1,
            'date': current_time(),
            'comment': comment,
            'phone': form.get('phone'),
            'doc': -1,
            'purpose': int(purpose),
            'hospital': hospital.pk,
            'external': True,
            'email': email,
            'external_num': external_num,
            'is_main_external': False,
        }
    )

    return Response({"ok": True, "number": doc_call.num})


@api_view(['POST'])
def set_core_id(request):
    data = json.loads(request.body)
    pk = data.get('pk')
    core_id = data.get('coreId')
    n = directions.Napravleniya.objects.get(pk=pk)
    n.core_id = core_id
    n.save(update_fields=['core_id'])
    return Response({"ok": True})


class InvalidData(Exception):
    pass


def limit_str(s: str, limit=500):
    return str(s)[:limit]


@api_view(['POST'])
def external_research_create(request):
    if not hasattr(request.user, 'hospitals'):
        return Response({"ok": False, 'message': 'Некорректный auth токен'})

    body = json.loads(request.body)

    old_pk = body.get("oldId")
    org = body.get("org")
    code_tfoms = org.get("codeTFOMS")
    oid_org = org.get("oid")

    if not code_tfoms and not oid_org:
        return Response({"ok": False, 'message': 'Должно быть указано хотя бы одно значение из org.codeTFOMS или org.oid'})

    if code_tfoms:
        hospital = Hospitals.objects.filter(code_tfoms=code_tfoms).first()
    else:
        hospital = Hospitals.objects.filter(oid=oid_org).first()

    if not hospital:
        return Response({"ok": False, 'message': 'Организация не найдена'})

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return Response({"ok": False, 'message': 'Нет доступа в переданную организацию'})

    patient = body.get("patient", {})
    enp = patient.get("enp", '').replace(' ', '')

    if len(enp) != 16 or not enp.isdigit():
        return Response({"ok": False, 'message': 'Неверные данные полиса, должно быть 16 чисел'})

    individuals = Individual.objects.filter(tfoms_enp=enp)
    if not individuals.exists():
        individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title='Полис ОМС') | Q(document__document_type__title='ЕНП'))
    if not individuals.exists():
        tfoms_data = match_enp(enp)
        if not tfoms_data:
            return Response({"ok": False, 'message': 'Неверные данные полиса, в базе ТФОМС нет такого пациента'})
        Individual.import_from_tfoms(tfoms_data)
        individuals = Individual.objects.filter(tfoms_enp=enp)

    individual = individuals.first()
    if not individual:
        return Response({"ok": False, 'message': 'Физлицо не найдено'})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    if not card:
        card = Card.add_l2_card(individual)

    if not card:
        return Response({"ok": False, 'message': 'Карта не найдена'})

    financing_source_title = body.get("financingSource", '')

    financing_source = directions.IstochnikiFinansirovaniya.objects.filter(title__iexact=financing_source_title, base__internal_type=True).first()

    if not financing_source:
        return Response({"ok": False, 'message': 'Некорректный источник финансирования'})

    results = body.get("results")
    if not results or not isinstance(results, list):
        return Response({"ok": False, 'message': 'Некорректное значение results'})

    results = results[:40]

    message = None

    id_in_hospital = body.get("internalId", '')

    if id_in_hospital is not None:
        id_in_hospital = limit_str(id_in_hospital, 15)

    try:
        with transaction.atomic():
            if old_pk and Napravleniya.objects.filter(pk=old_pk, hospital=hospital).exists():
                direction = Napravleniya.objects.get(pk=old_pk)
                direction.is_external = True
                direction.istochnik_f = financing_source
                direction.polis_who_give = card.polis.who_give if card.polis else None
                direction.polis_n = card.polis.number if card.polis else None
                direction.id_in_hospital = id_in_hospital
                direction.save()
                direction.issledovaniya_set.all().delete()
                print('Replacing all data for', old_pk)  # noqa: T001
            else:
                direction = Napravleniya.objects.create(
                    client=card,
                    is_external=True,
                    istochnik_f=financing_source,
                    polis_who_give=card.polis.who_give if card.polis else None,
                    polis_n=card.polis.number if card.polis else None,
                    hospital=hospital,
                    id_in_hospital=id_in_hospital,
                )

            research_to_filter = defaultdict(lambda: False)

            for r in results:
                code_research = r.get("codeResearch", "unknown")
                research = Researches.objects.filter(code=code_research).first()
                if not research:
                    raise InvalidData(f'Исследование с кодом {code_research} не найдено')

                if research_to_filter[code_research]:
                    raise InvalidData(f'Исследование с кодом {code_research} отправлено повторно в одном направлении')

                tests = r.get("tests")
                if not tests or not isinstance(tests, list):
                    raise InvalidData(f'Исследование {code_research} содержит некорректное поле tests')

                comments = str(r.get("comments", "") or "") or None

                time_confirmation = r.get("dateTimeConfirm")
                if not time_confirmation or not valid_date(time_confirmation):
                    raise InvalidData(f'{code_research}: содержит некорректное поле dateTimeConfirm. Оно должно быть заполнено и соответствовать шаблону YYYY-MM-DD HH:MM')

                time_get = str(r.get("dateTimeGet", "") or "") or None
                if time_get and not valid_date(time_confirmation):
                    raise InvalidData(f'{code_research}: содержит некорректное поле dateTimeGet. Оно должно быть пустым или соответствовать шаблону YYYY-MM-DD HH:MM')

                time_receive = str(r.get("dateTimeReceive", "") or "") or None
                if time_receive and not valid_date(time_confirmation):
                    raise InvalidData(f'{code_research}: содержит некорректное поле dateTimeReceive. Оно должно быть пустым или соответствовать шаблону YYYY-MM-DD HH:MM')

                doc_confirm = str(r.get("docConfirm", "") or "") or None

                if doc_confirm is not None:
                    doc_confirm = limit_str(doc_confirm, 64)

                iss = directions.Issledovaniya.objects.create(
                    napravleniye=direction,
                    research=research,
                    lab_comment=comments,
                    time_confirmation=time_confirmation,
                    time_save=timezone.now(),
                    doc_confirmation_string=doc_confirm or f'Врач {hospital.short_title or hospital.title}',
                )
                tube = Tubes.objects.filter(title='Универсальная пробирка').first()
                if not tube:
                    tube = Tubes.objects.create(title='Универсальная пробирка', color='#049372')

                ft = ReleationsFT.objects.filter(tube=tube).first()
                if not ft:
                    ft = ReleationsFT.objects.create(tube=tube)

                tr = iss.tubes.create(type=ft)
                tr.time_get = time_get
                tr.time_recive = time_receive
                tr.save(update_fields=['time_get', 'time_recive'])

                tests_to_filter = defaultdict(lambda: False)

                for t in tests[:30]:
                    fsli_code = t.get("idFsli", "unknown")
                    fraction = Fractions.objects.filter(fsli=fsli_code).first()
                    if not fraction:
                        raise InvalidData(f'В исследовании {code_research} не найден тест {fsli_code}')

                    if tests_to_filter[code_research]:
                        raise InvalidData(f'Тест с кодом {fsli_code} отправлен повторно в одном направлении в {code_research}')

                    value = limit_str(t.get("valueString", "") or "", 500)
                    units = limit_str(str(t.get("units", "") or ""), 50)

                    reference_value = t.get("referenceValue") or None
                    reference_range = t.get("referenceRange") or None

                    if reference_value and not isinstance(reference_value, str):
                        raise InvalidData(f'{code_research} -> {fsli_code}: поле referenceValue должно быть строкой или null')
                    if reference_range and not isinstance(reference_range, dict):
                        raise InvalidData(f'{code_research} -> {fsli_code}: поле referenceRange должно быть объектом {{low, high}} или null')

                    if reference_range and ('low' not in reference_range or 'high' not in reference_range):
                        raise InvalidData(f'{code_research} -> {fsli_code}: поле referenceRange должно быть объектом с полями {{low, high}} или null')

                    ref_str = reference_value

                    if not ref_str and reference_range:
                        ref_str = f"{reference_range['low']} – {reference_range['high']}"

                    if ref_str:
                        ref_str = limit_str(ref_str.replace("\"", "'"), 120)
                        ref_str = f'{{"Все": "{ref_str}"}}'

                    directions.Result(
                        issledovaniye=iss,
                        fraction=fraction,
                        value=value,
                        units=units,
                        ref_f=ref_str,
                        ref_m=ref_str,
                    ).save()
            try:
                Log.log(
                    str(direction.pk),
                    90000,
                    body={
                        "org": body.get("org"),
                        "patient": body.get("patient"),
                        "financingSource": body.get("financingSource"),
                        "resultsCount": len(body.get("results")),
                    },
                )
            except Exception as e:
                logger.exception(e)
            return Response({"ok": True, 'id': str(direction.pk)})

    except InvalidData as e:
        message = str(e)
    except Exception as e:
        logger.exception(e)
        message = 'Серверная ошибка'

    return Response({"ok": False, 'message': message})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def eds_get_user_data(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    token = token.replace('Bearer ', '')

    if not token or not DoctorProfile.objects.filter(eds_token=token).exists():
        return Response({"ok": False})

    doc = DoctorProfile.objects.filter(eds_token=token)[0]

    return Response({
        "ok": True,
        "fio": doc.fio,
        "department": doc.podrazdeleniye.title if doc.podrazdeleniye else None,
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def eds_get_cda_data(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    token = token.replace('Bearer ', '')

    if not token or not DoctorProfile.objects.filter(eds_token=token).exists():
        return Response({"ok": False})

    body = json.loads(request.body)

    pk = body.get("oldId")

    n = Napravleniya.objects.get(pk=pk)
    i: directions.Issledovaniya = n.issledovaniya_set.all()[0]
    card = n.client
    ind = n.client.individual

    return Response({
        "title": i.research.title,
        "patient": {
            'pk': card.number,
            'family': ind.family,
            'name': ind.name,
            'patronymic': ind.patronymic,
            'gender': ind.sex.lower(),
            'birthdate': ind.birthday.strftime("%Y%m%d"),
        },
    })
