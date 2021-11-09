import base64
import datetime
import logging
from podrazdeleniya.models import Podrazdeleniya
import random
from collections import defaultdict
import re
import time

import petrovna
import simplejson as json
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

import directions.models as directions
from appconf.manager import SettingManager
from clients.models import Individual, Card
from clients.sql_func import last_results_researches_by_time_ago
from directory.models import Researches, Fractions, ReleationsFT
from doctor_call.models import DoctorCall
from hospitals.models import Hospitals
from laboratory.settings import AFTER_DATE, CENTRE_GIGIEN_EPIDEMIOLOGY, MAX_DOC_CALL_EXTERNAL_REQUESTS_PER_DAY, REGION
from laboratory.utils import current_time, strfdatetime
from refprocessor.result_parser import ResultRight
from researches.models import Tubes
from rmis_integration.client import Client
from slog.models import Log
from tfoms.integration import match_enp, match_patient, get_ud_info_by_enp, match_patient_by_snils, get_dn_info_by_enp
from users.models import DoctorProfile
from utils.data_verification import data_parse
from utils.dates import normalize_date, valid_date
from . import sql_if
from directions.models import DirectionDocument, DocumentSign, Napravleniya
from .models import CrieOrder, ExternalService
from laboratory.settings import COVID_RESEARCHES_PK

logger = logging.getLogger("IF")


@api_view()
def next_result_direction(request):
    from_pk = request.GET.get("fromPk")
    after_date = request.GET.get("afterDate")
    only_signed = request.GET.get("onlySigned")
    if after_date == '0':
        after_date = AFTER_DATE
    next_n = int(request.GET.get("nextN", 1))
    type_researches = request.GET.get("research", '*')
    d_start = f'{after_date}'
    is_research = 1
    researches = [-999]
    if type_researches == 'lab':
        researches = [x.pk for x in Researches.objects.filter(podrazdeleniye__p_type=Podrazdeleniya.LABORATORY)]
    elif type_researches != '*':
        researches = [int(i) for i in type_researches.split(',')]
    else:
        is_research = -1
    if only_signed == '1':
        # TODO: вернуть только подписанные и как дату next_time использовать дату подписания, а не подтверждения
        # признак – eds_total_signed=True, датавремя полного подписания eds_total_signed_at
        dirs = sql_if.direction_collect(d_start, researches, is_research, next_n) or []
    else:
        dirs = sql_if.direction_collect(d_start, researches, is_research, next_n) or []

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
def resend_dir_crie(request):
    next_n = int(request.GET.get("nextN", 5))
    dirs = sql_if.direction_resend_crie(next_n)
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
    direction: directions.Napravleniya = directions.Napravleniya.objects.select_related('istochnik_f', 'client', 'client__individual', 'client__base').get(pk=pk)
    card = direction.client
    individual = card.individual

    iss = directions.Issledovaniya.objects.filter(napravleniye=direction, time_confirmation__isnull=False).select_related('research', 'doc_confirmation')
    if research_pks != '*':
        iss = iss.filter(research__pk__in=research_pks.split(','))

    if not iss:
        return Response({"ok": False})

    iss_index = random.randrange(len(iss))

    signed_documents = []

    if direction.eds_total_signed:
        last_time_confirm = direction.last_time_confirm()
        for d in DirectionDocument.objects.filter(direction=direction, last_confirmed_at=last_time_confirm):
            document = {
                'type': d.file_type.upper(),
                'content': base64.b64encode(d.file.read()).decode('utf-8'),
                'signatures': [],
            }

            for s in DocumentSign.objects.filter(document=d):
                document['signatures'].append({
                    "content": s.sign_value.replace('\n', ''),
                    "type": s.sign_type,
                    "executor": s.executor.uploading_data,
                })

            signed_documents.append(document)

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
                "docs": card.get_n3_documents(),
                "sex": individual.sex,
                "card": {
                    "base": {"pk": card.base_id, "title": card.base.title, "short_title": card.base.short_title},
                    "pk": card.pk,
                    "number": card.number,
                    "n3Id": card.n3_id,
                    "numberWithType": card.number_with_type(),
                },
            },
            "issledovaniya": [x.pk for x in iss],
            "timeConfirmation": iss[iss_index].time_confirmation,
            "timeTube": iss[iss_index].material_date,
            "docLogin": iss[iss_index].doc_confirmation.rmis_login if iss[iss_index].doc_confirmation else None,
            "docPassword": iss[iss_index].doc_confirmation.rmis_password if iss[iss_index].doc_confirmation else None,
            "department_oid": iss[iss_index].doc_confirmation.podrazdeleniye.oid if iss[iss_index].doc_confirmation else None,
            "finSourceTitle": direction.istochnik_f.title if direction.istochnik_f else 'другое',
            "finSourceCode": direction.istochnik_f.get_n3_code() if direction.istochnik_f else '6',
            "oldPk": direction.core_id,
            "isExternal": direction.is_external,
            "titleInitiator": direction.get_title_org_initiator(),
            "ogrnInitiator": direction.get_ogrn_org_initiator(),
            "titleLaboratory": direction.hospital_title.replace("\"", " "),
            "ogrnLaboratory": direction.hospital_ogrn,
            "hospitalN3Id": direction.hospital_n3id,
            "signed": direction.eds_total_signed,
            "totalSignedAt": direction.eds_total_signed_at,
            "signedDocuments": signed_documents,
            "REGION": REGION,
            "DEPART": CENTRE_GIGIEN_EPIDEMIOLOGY,
            "hasN3IemkUploading": direction.n3_iemk_ok,
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
                    refs = refs_list
        else:
            refs = [r.calc_normal(only_ref=True) or '']

        norm = r.calc_normal()

        u = r.fraction.get_unit()

        results_data.append(
            {
                "pk": r.pk,
                "fsli": r.fraction.get_fsli_code(),
                "value": r.value.replace(',', '.'),
                "units": r.get_units(),
                "unitCode": u.code if u else None,
                "ref": refs,
                "interpretation": 'N' if norm and norm[0] == ResultRight.RESULT_MODE_NORMAL else 'A',
            }
        )

    time_confirmation = i.time_confirmation_local

    doctor_data = {}

    if i.doc_confirmation:
        doctor_data = i.doc_confirmation.uploading_data

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
            "doctorData": doctor_data,
            "results": results_data,
            "code": i.research.code,
            "comments": i.lab_comment,
        }
    )


@api_view()
def issledovaniye_data_simple(request):
    pk = request.GET.get("pk")
    i = directions.Issledovaniya.objects.get(pk=pk)

    doctor_data = {}

    if i.doc_confirmation:
        doctor_data = i.doc_confirmation.uploading_data

    return Response(
        {
            "ok": True,
            "pk": pk,
            "date": i.time_confirmation_local,
            "docConfirm": i.doc_confirmation_fio,
            "doctorData": doctor_data,
            "outcome": (i.outcome_illness.n3_id if i.outcome_illness else None) or '3',
            "visitPlace": (i.place.n3_id if i.place else None) or '1',
            "visitPurpose": (i.purpose.n3_id if i.purpose else None) or '2',
            "typeFlags": i.research.get_flag_types_n3(),
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
                    "issTitle": i.research.title,
                    "title": r.fraction.title,
                    "fsli": r.fraction.get_fsli_code(),
                    "value": r.value.replace(',', '.'),
                    "units": r.get_units(),
                    "ref": refs,
                    "confirmed": i.time_confirmation,
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


@api_view(['GET', 'POST'])
def make_log(request):
    key = request.GET.get("key")
    keys = request.GET.get("keys", key).split(",")
    t = int(request.GET.get("type"))
    body = {}

    if request.method == "POST":
        body = json.loads(request.body)

    pks_to_resend_n3_false = [x for x in keys if x] if t in (60000, 60001, 60002, 60003) else []
    pks_to_resend_l2_false = [x for x in keys if x] if t in (60004, 60005) else []

    pks_to_set_odli_id = [x for x in keys if x] if t in (60007,) else []
    pks_to_set_odli_id_fail = [x for x in keys if x] if t in (60008,) else []

    pks_to_set_iemk = [x for x in keys if x] if t in (60009, 60011) else []
    pks_to_set_iemk_fail = [x for x in keys if x] if t in (60010,) else []

    with transaction.atomic():
        directions.Napravleniya.objects.filter(pk__in=pks_to_resend_n3_false).update(need_resend_n3=False)
        directions.Napravleniya.objects.filter(pk__in=pks_to_resend_l2_false).update(need_resend_l2=False)

        for k in pks_to_resend_n3_false:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_resend_l2_false:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_odli_id_fail:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_odli_id:
            Log.log(key=k, type=t, body=body.get(k, {}))

            if str(k) in body and isinstance(body[k], dict) and body[str(k)]['id']:
                d = directions.Napravleniya.objects.get(pk=k)
                d.n3_odli_id = body[str(k)]['id']
                d.save(update_fields=['n3_odli_id'])

        for k in pks_to_set_iemk_fail:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_iemk:
            Log.log(key=k, type=t, body=body.get(k, {}))

            d = directions.Napravleniya.objects.get(pk=k)
            d.n3_iemk_ok = True
            d.save(update_fields=['n3_iemk_ok'])

    return Response({"ok": True})


@api_view(['GET'])
def crie_status(request):
    pk = request.GET.get("direction")
    system_id = request.GET.get("system_id")
    status = request.GET.get("status") or 'null'
    error = request.GET.get("error") or ''

    direction = directions.Napravleniya.objects.filter(pk=pk).first()

    if direction:
        if direction.need_resend_crie:
            direction.need_resend_crie = False
            direction.save(update_fields=['need_resend_crie'])
        order = CrieOrder.objects.filter(local_direction=direction).first()
        if not order:
            order = CrieOrder.objects.create(local_direction=direction, system_id=system_id, status=status, error=error)
            updated = ['system_id', 'status', 'error', 'local_direction']
        else:
            updated = []
            if order.system_id != system_id:
                order.system_id = system_id
                updated.append('system_id')

            if order.status != status:
                order.status = status
                updated.append('status')

            if order.error != error:
                order.error = error
                updated.append('error')

            if updated:
                order.save(update_fields=updated)
        if updated:
            Log.log(key=pk, type=60006, body={'updated': updated, 'order_id': order.pk})
        return Response({"ok": True, "order": order.pk})
    return Response({"ok": False})


@api_view(['POST'])
def check_enp(request):
    enp, family, name, patronymic, bd, enp_mode, snils = data_parse(
        request.body,
        {'enp': str, 'family': str, 'name': str, 'patronymic': str, 'bd': str, 'check_mode': str, 'snils': str},
        {'check_mode': 'tfoms', 'bd': None, 'name': None, 'patronymic': None, 'family': None, 'enp': None, 'ud': None, 'snils': None},
    )
    if not enp:
        enp = ""
    enp = enp.replace(' ', '')

    logger.exception(f'enp_mode: {enp_mode}')

    if enp_mode == 'l2-enp':
        tfoms_data = match_enp(enp)
        if tfoms_data:
            return Response({"ok": True, 'patient_data': tfoms_data})
    elif enp_mode == 'l2-enp-ud':
        tfoms_data = get_ud_info_by_enp(enp)
        if tfoms_data:
            return Response({"ok": True, 'patient_data': tfoms_data})
    elif enp_mode == 'l2-enp-dn':
        tfoms_data = get_dn_info_by_enp(enp)
        if tfoms_data:
            return Response({"ok": True, 'patient_data': tfoms_data})
    elif enp_mode == 'l2-snils':
        tfoms_data = match_patient_by_snils(snils)
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
    elif enp_mode == 'local':
        logger.exception(f'enp: {enp}')
        card = Card.objects.filter(base__internal_type=True, is_archive=False, carddocusage__document__number=enp, carddocusage__document__document_type__title='Полис ОМС').first()

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
    days = 15
    results = []
    p_enp = data_parse(request.body, {'enp': str}, {'enp': ''})[0]
    if p_enp:
        logger.exception(f'patient_results_covid19 by enp: {p_enp}')
        card = Card.objects.filter(
            base__internal_type=True, is_archive=False, carddocusage__document__number=str(p_enp).replace(' ', ''), carddocusage__document__document_type__title='Полис ОМС'
        ).first()
        logger.exception(f'patient_results_covid19 by enp [CARD]: {card}')
        if card:
            date_end = current_time()
            date_start = date_end + relativedelta(days=-days)
            date_end = date_end + relativedelta(days=1)
            results_covid = last_results_researches_by_time_ago(card.pk, COVID_RESEARCHES_PK, date_start, date_end)
            logger.exception(f'patient_results_covid19 by enp params: {(card.pk, COVID_RESEARCHES_PK, date_start, date_end)}')
            logger.exception(f'patient_results_covid19 by enp results count: {len(results_covid)}')
            for i in results_covid:
                results.append({'date': i.confirm, 'result': i.value})
            if len(results) > 0:
                return Response({"ok": True, 'results': results})

    rmis_id = data_parse(request.body, {'rmis_id': str}, {'rmis_id': ''})[0]

    results = []

    if rmis_id:
        for i in range(3):
            results = []

            logger.exception(f'patient_results_covid19 by rmis id, try {i + 1}/3: {rmis_id}')

            try:
                c = Client(modules=['directions', 'rendered_services'])

                now = current_time().date()

                variants = ['РНК вируса SARS-CоV2 не обнаружена', 'РНК вируса SARS-CоV2 обнаружена']

                for i in range(days):
                    date = now - datetime.timedelta(days=i)
                    rendered_services = c.rendered_services.client.searchServiceRend(patientUid=rmis_id, dateFrom=date)
                    for rs in rendered_services[:5]:
                        protocol = c.directions.get_protocol(rs)
                        for v in variants:
                            if v in protocol:
                                results.append({'date': date.strftime('%d.%m.%Y'), 'result': v})
                                break
                break
            except Exception as e:
                logger.exception(e)
            time.sleep(2)

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

    count = DoctorCall.objects.filter(client=card, is_external=True, exec_at__date=date.date()).count()
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

    individual = individuals if isinstance(individuals, Individual) else individuals.first()
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
    org = body.get("org", {})
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

    initiator = org.get('initiator') or {}
    title_org_initiator = initiator.get('title')
    if title_org_initiator is not None:
        title_org_initiator = str(title_org_initiator)[:254]

    ogrn_org_initiator = initiator.get('ogrn')
    if ogrn_org_initiator is not None:
        ogrn_org_initiator = str(ogrn_org_initiator)

    if not title_org_initiator:
        title_org_initiator = None

    if not ogrn_org_initiator:
        ogrn_org_initiator = None

    if not title_org_initiator and ogrn_org_initiator:
        return Response({"ok": False, 'message': 'org.initiator: при передаче ogrn поле title обязательно'})

    if title_org_initiator and not ogrn_org_initiator:
        return Response({"ok": False, 'message': 'org.initiator: при передаче title поле ogrn обязательно'})

    if ogrn_org_initiator and not ogrn_org_initiator.isdigit():
        return Response({"ok": False, 'message': 'org.initiator.ogrn: в значении возможны только числа'})

    if ogrn_org_initiator and len(ogrn_org_initiator) != 13:
        return Response({"ok": False, 'message': 'org.initiator.ogrn: длина должна быть 13'})

    if ogrn_org_initiator and not petrovna.validate_ogrn(ogrn_org_initiator):
        return Response({"ok": False, 'message': 'org.initiator.ogrn: не прошёл валидацию'})

    patient = body.get("patient", {})

    enp = (patient.get("enp") or '').replace(' ', '')

    if enp and (len(enp) != 16 or not enp.isdigit()):
        return Response({"ok": False, 'message': 'Неверные данные полиса, должно быть 16 чисел'})

    passport_serial = (patient.get("passportSerial") or '').replace(' ', '')
    passport_number = (patient.get("passportNumber") or '').replace(' ', '')

    snils = (patient.get("snils") or '').replace(' ', '').replace('-', '')

    if not enp and (not passport_serial or not passport_number) and not snils:
        return Response({"ok": False, 'message': 'При пустом patient.enp должно быть передано patient.snils или patient.passportSerial+patient.passportNumber'})

    if passport_serial and len(passport_serial) != 4:
        return Response({"ok": False, 'message': 'Длина patient.passportSerial должна быть 4'})

    if passport_serial and not passport_serial.isdigit():
        return Response({"ok": False, 'message': 'patient.passportSerial должен содержать только числа'})

    if passport_number and len(passport_number) != 6:
        return Response({"ok": False, 'message': 'Длина patient.passportNumber должна быть 6'})

    if passport_number and not passport_number.isdigit():
        return Response({"ok": False, 'message': 'patient.passportNumber должен содержать только числа'})

    if snils and not petrovna.validate_snils(snils):
        return Response({"ok": False, 'message': 'patient.snils: не прошёл валидацию'})

    individual_data = patient.get("individual") or {}

    if not enp and not individual_data:
        return Response({"ok": False, 'message': 'При пустом patient.enp должно быть передано поле patient.individual'})

    lastname = str(individual_data.get("lastname") or '')
    firstname = str(individual_data.get('firstname') or '')
    patronymic = str(individual_data.get('patronymic') or '')
    birthdate = str(individual_data.get('birthdate') or '')
    sex = str(individual_data.get('sex') or '').lower()

    individual = None

    if lastname and not firstname:
        return Response({"ok": False, 'message': 'При передаче lastname должен быть передан и firstname'})

    if firstname and not lastname:
        return Response({"ok": False, 'message': 'При передаче firstname должен быть передан и lastname'})

    if firstname and lastname and not birthdate:
        return Response({"ok": False, 'message': 'При передаче firstname и lastname должно быть передано поле birthdate'})

    if birthdate and (not re.fullmatch(r'\d{4}-\d\d-\d\d', birthdate) or birthdate[0] not in ['1', '2']):
        return Response({"ok": False, 'message': 'birthdate должно соответствовать формату YYYY-MM-DD'})

    if birthdate and sex not in ['м', 'ж']:
        return Response({"ok": False, 'message': 'individual.sex должно быть "м" или "ж"'})

    individual_status = "unknown"

    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        if not individuals.exists():
            individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title='Полис ОМС') | Q(document__document_type__title='ЕНП'))
            individual = individuals.first()
            individual_status = "local_enp"
        if not individual:
            tfoms_data = match_enp(enp)
            if tfoms_data:
                individuals = Individual.import_from_tfoms(tfoms_data, need_return_individual=True)
                individual_status = "tfoms_match_enp"

            individual = individuals.first()

    if not individual and lastname:
        tfoms_data = match_patient(lastname, firstname, patronymic, birthdate)
        if tfoms_data:
            individual_status = "tfoms_match_patient"
            individual = Individual.import_from_tfoms(tfoms_data, need_return_individual=True)

    if not individual and passport_serial:
        individuals = Individual.objects.filter(document__serial=passport_serial, document__number=passport_number, document__document_type__title='Паспорт гражданина РФ')
        individual = individuals.first()
        individual_status = "passport"

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title='СНИЛС')
        individual = individuals.first()
        individual_status = "snils"

    if not individual and lastname:
        individual = Individual.import_from_tfoms(
            {
                "family": lastname,
                "given": firstname,
                "patronymic": patronymic,
                "gender": sex,
                "birthdate": birthdate,
                "enp": enp,
                "passport_serial": passport_serial,
                "passport_number": passport_number,
                "snils": snils,
            },
            need_return_individual=True,
        )
        individual_status = "new_local"

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
                direction.title_org_initiator = title_org_initiator
                direction.ogrn_org_initiator = ogrn_org_initiator
                direction.save()
                direction.issledovaniya_set.all().delete()
            else:
                direction = Napravleniya.objects.create(
                    client=card,
                    is_external=True,
                    istochnik_f=financing_source,
                    polis_who_give=card.polis.who_give if card.polis else None,
                    polis_n=card.polis.number if card.polis else None,
                    hospital=hospital,
                    id_in_hospital=id_in_hospital,
                    title_org_initiator=title_org_initiator,
                    ogrn_org_initiator=ogrn_org_initiator,
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
                        "individualStatus": individual_status,
                        "financingSource": body.get("financingSource"),
                        "resultsCount": len(body.get("results")),
                        "results": body.get("results"),
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

    return Response(
        {
            "ok": True,
            "userData": {
                "fio": doc.get_full_fio(),
                "department": doc.podrazdeleniye.title if doc.podrazdeleniye else None,
            },
        }
    )


def get_cda_data(pk):
    n: Napravleniya = Napravleniya.objects.get(pk=pk)
    card = n.client
    ind = n.client.individual

    return {
        "title": n.get_eds_title(),
        "patient": {
            'pk': card.number,
            'family': ind.family,
            'name': ind.name,
            'patronymic': ind.patronymic,
            'gender': ind.sex.lower(),
            'birthdate': ind.birthday.strftime("%Y%m%d"),
        },
    }


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def eds_get_cda_data(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    token = token.replace('Bearer ', '')

    if not token or not DoctorProfile.objects.filter(eds_token=token).exists():
        return Response({"ok": False})

    body = json.loads(request.body)

    pk = body.get("pk")

    return Response(get_cda_data(pk))


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def external_check_result(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    token = token.replace('Bearer ', '')
    external_service = ExternalService.objects.filter(token=token).first()

    if not token or not external_service:
        return Response(
            {
                "ok": False,
                "message": "Передан некорректный токен в заголовке HTTP_AUTHORIZATION",
            },
            status=403,
        )

    external_service: ExternalService = external_service
    if not external_service.is_active:
        return Response(
            {
                "ok": False,
                "message": "Доступ отключен",
            },
            status=403,
        )

    if 'qr_check_result' not in external_service.rights:
        return Response(
            {
                "ok": False,
                "message": "Нет доступа",
            },
            status=403,
        )

    body = json.loads(request.body)
    instance_id = body.get("instanceId")

    if SettingManager.instance_id() != instance_id:
        return Response(
            {
                "ok": False,
                "message": "Некорректный instance_id",
            }
        )

    pk = body.get("direction")
    direction = Napravleniya.objects.filter(pk=pk).first()
    if not direction:
        return Response(
            {
                "ok": False,
                "message": "Направление не найдено",
            }
        )

    direction: Napravleniya

    direction_token = body.get("directionToken")
    if str(direction.qr_check_token) != direction_token:
        return Response(
            {
                "ok": False,
                "message": "Некорректный токен направления",
            }
        )

    ind: Individual = direction.client.individual
    patient = {
        "family": f"{ind.family[0] if ind.family else ''}*****",
        "name": f"{ind.name[0] if ind.name else ''}*****",
        "patronymic": f"{ind.patronymic[0] if ind.patronymic else ''}*****",
        "birthdate": str(ind.birthday.year),
    }

    results = []

    i: directions.Issledovaniya
    for i in direction.issledovaniya_set.all():
        if not i.doc_confirmation:
            continue
        result = {
            "title": i.research.title,
            "datetime": strfdatetime(i.time_confirmation, "%d.%m.%Y %X"),
            "data": [],
        }
        fractions = Fractions.objects.filter(research=i.research).order_by("pk").order_by("sort_weight")
        f: Fractions
        for f in fractions:
            if not directions.Result.objects.filter(issledovaniye=i, fraction=f).exists():
                continue
            r: directions.Result = directions.Result.objects.filter(issledovaniye=i, fraction=f)[0]
            result["data"].append(
                {
                    "title": f.title,
                    "value": r.value,
                }
            )
        results.append(result)
    return Response(
        {
            "patient": patient,
            "results": results,
        }
    )
