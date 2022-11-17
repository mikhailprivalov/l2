import base64
import os
import html

from django.test import Client as TC
import datetime
import logging

import pytz_deprecation_shim as pytz
from django.utils.module_loading import import_string

from api.directions.sql_func import direction_by_card, get_lab_podr, get_confirm_direction_patient_year, get_type_confirm_direction, get_confirm_direction_patient_year_is_extract
from api.stationar.stationar_func import desc_to_data
from api.views import mkb10_dict
from clients.utils import find_patient
from contracts.models import PriceCategory
from directory.utils import get_researches_details, get_can_created_patient
from doctor_schedule.views import get_hospital_resource, get_available_hospital_plans, check_available_hospital_slot_before_save
from external_system.models import ArchiveMedicalDocuments, InstrumentalResearchRefbook
from integration_framework.authentication import can_use_schedule_only

from laboratory import settings
from plans.models import PlanHospitalization, PlanHospitalizationFiles, Messages
from podrazdeleniya.models import Podrazdeleniya
import random
from collections import defaultdict
import re
import time

import petrovna
import simplejson as json
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response

import directions.models as directions
from appconf.manager import SettingManager
from clients.models import Individual, Card
from clients.sql_func import last_results_researches_by_time_ago
from directory.models import Researches, Fractions, ReleationsFT, HospitalService, ParaclinicInputGroups, ParaclinicInputField
from doctor_call.models import DoctorCall
from hospitals.models import Hospitals
from laboratory.settings import (
    AFTER_DATE,
    CENTRE_GIGIEN_EPIDEMIOLOGY,
    MAX_DOC_CALL_EXTERNAL_REQUESTS_PER_DAY,
    REGION,
    SCHEDULE_AGE_LIMIT_LTE,
    LK_FORMS,
    LK_USER,
    LK_FILE_SIZE_BYTES,
    LK_FILE_COUNT,
    LK_DAY_MONTH_START_SHOW_RESULT,
    GISTOLOGY_RESEARCH_PK,
    REFERENCE_ODLI,
    ODII_METHODS_IEMK,
    ID_MED_DOCUMENT_TYPE_IEMK_N3,
    DEATH_RESEARCH_PK,
    REMD_EXCLUDE_RESEARCH,
    REMD_ONLY_RESEARCH,
)
from laboratory.utils import current_time, date_at_bound, strfdatetime
from refprocessor.result_parser import ResultRight
from researches.models import Tubes
from results.prepare_data import fields_result_only_title_fields
from results.sql_func import get_laboratory_results_by_directions, get_not_confirm_direction
from rmis_integration.client import Client
from slog.models import Log
from tfoms.integration import match_enp, match_patient, get_ud_info_by_enp, match_patient_by_snils, get_dn_info_by_enp
from users.models import DoctorProfile
from utils.common import values_as_structure_data
from utils.data_verification import data_parse
from utils.dates import normalize_date, valid_date, try_strptime, try_parse_range
from utils.xh import check_type_research, short_fio_dots
from . import sql_if
from directions.models import DirectionDocument, DocumentSign, Issledovaniya, Napravleniya
from .common_func import check_correct_hosp, get_data_direction_with_param, direction_pdf_result
from .models import CrieOrder, ExternalService
from laboratory.settings import COVID_RESEARCHES_PK
from .utils import get_json_protocol_data, get_json_labortory_data, check_type_file, legal_auth_get
from django.contrib.auth.models import User

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
    elif type_researches == 'gistology':
        researches = [x.pk for x in Researches.objects.filter(is_gistology=True)]
    elif type_researches == 'paraclinic':
        researches = [x.pk for x in Researches.objects.filter(is_paraclinic=True)]
    elif type_researches != '*':
        researches = [int(i) for i in type_researches.split(',')]
    else:
        is_research = -1
    dirs, dirs_eds = None, None

    if only_signed == '1':
        # TODO: вернуть только подписанные и как дату next_time использовать дату подписания, а не подтверждения
        # признак – eds_total_signed=True, датавремя полного подписания eds_total_signed_at
        dirs_eds = sql_if.direction_collect_date_signed(d_start, researches, is_research, next_n) or []
    else:
        dirs = sql_if.direction_collect(d_start, researches, is_research, next_n) or []

    next_time, naprs = None, None
    if dirs:
        naprs = [d[0] for d in dirs]
        next_time = dirs[-1][3]
    elif dirs_eds:
        naprs = list(set([d[0] for d in dirs_eds]))
        next_time = dirs_eds[-1][2]

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
    for i in iss:
        if len(REMD_ONLY_RESEARCH) > 0 and i.research.pk not in REMD_ONLY_RESEARCH:
            return Response({"ok": False})

    if not iss:
        return Response({"ok": False})

    iss_index = random.randrange(len(iss))

    signed_documents = []

    if direction.eds_total_signed:
        last_time_confirm = direction.last_time_confirm()
        for d in DirectionDocument.objects.filter(direction=direction, last_confirmed_at=last_time_confirm):
            if not d.file:
                continue
            document = {
                'type': d.file_type.upper(),
                'content': base64.b64encode(d.file.read()).decode('utf-8'),
                'signatures': [],
            }

            for s in DocumentSign.objects.filter(document=d):
                document['signatures'].append(
                    {
                        "content": s.sign_value.replace('\n', ''),
                        "type": s.sign_type,
                        "executor": s.executor.uploading_data,
                    }
                )

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
            "department_name": iss[iss_index].doc_confirmation.podrazdeleniye.nsi_title if iss[iss_index].doc_confirmation else None,
            "kind": iss[iss_index].research.oid_kind if iss[iss_index].doc_confirmation else None,
            "finSourceTitle": direction.istochnik_f.title if direction.istochnik_f else 'другое',
            "finSourceCode": direction.istochnik_f.get_n3_code() if direction.istochnik_f else '6',
            "finSourceEcpCode": direction.istochnik_f.get_ecp_code() if direction.istochnik_f else '380101000000023',
            "oldPk": direction.core_id,
            "isExternal": direction.is_external,
            "titleInitiator": direction.get_title_org_initiator(),
            "ogrnInitiator": direction.get_ogrn_org_initiator(),
            "titleLaboratory": direction.hospital_title.replace("\"", " "),
            "ogrnLaboratory": direction.hospital_ogrn,
            "hospitalN3Id": direction.hospital_n3id,
            "departmentN3Id": direction.department_n3id,
            "hospitalEcpId": direction.hospital_ecp_id,
            "signed": direction.eds_total_signed,
            "totalSignedAt": direction.eds_total_signed_at,
            "signedDocuments": signed_documents,
            "REGION": REGION,
            "DEPART": CENTRE_GIGIEN_EPIDEMIOLOGY,
            "hasN3IemkUploading": direction.n3_iemk_ok,
            "organizationOid": iss[iss_index].doc_confirmation.get_hospital().oid,
            "generatorName": direction.get_eds_generator(),
            "legalAuth": legal_auth_get({"id": iss[iss_index].doc_confirmation.get_hospital().legal_auth_doc_id}, as_uploading_data=True),
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
    results = directions.Result.objects.filter(issledovaniye=i).exclude(fraction__fsli__isnull=True).exclude(fraction__fsli='').exclude(fraction__not_send_odli=True)
    if (not ignore_sample and not sample) or (not results.exists() and not i.research.is_gistology and not i.research.is_paraclinic) or i.research.pk in REMD_EXCLUDE_RESEARCH:
        return Response(
            {"ok": False, "ignore_sample": ignore_sample, "sample": {"date": sample.time_get.date() if sample else i.time_confirmation.date()}, "results.exists": results.exists()}
        )

    results_data = []

    for r in results:
        if r.value in ["", None]:
            continue
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
        if not REFERENCE_ODLI:
            refs = ['']
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
            "code": i.research.code.upper().replace('А', 'A').replace('В', 'B').replace('С', 'C').strip(),
            "research": i.research.get_title(),
            "comments": i.lab_comment,
            "isGistology": i.research.is_gistology,
            "isParaclinic": i.research.is_paraclinic,
        }
    )


@api_view()
def issledovaniye_data_simple(request):
    pk = request.GET.get("pk")
    i = directions.Issledovaniya.objects.get(pk=pk)

    doctor_data = {}

    if i.doc_confirmation:
        doctor_data = i.doc_confirmation.uploading_data
    type_res_instr_iemk = None
    id_med_document_type = None
    if i.research.is_paraclinic:
        nsi_res = InstrumentalResearchRefbook.objects.filter(code_nsi=i.research.nsi_id).first()
        type_res_instr_iemk = ODII_METHODS_IEMK.get(nsi_res.method)
        id_med_document_type = ID_MED_DOCUMENT_TYPE_IEMK_N3.get("is_paraclinic")

    mkb10 = None
    if i.research.pk == DEATH_RESEARCH_PK:
        id_med_document_type = ID_MED_DOCUMENT_TYPE_IEMK_N3.get("is_death")
        title_fields = [
            "а) Болезнь или состояние, непосредственно приведшее к смерти",
            "б) патологическое состояние, которое привело к возникновению вышеуказанной причины:",
            "в) первоначальная причина смерти:",
        ]
        data = {}
        result = fields_result_only_title_fields(i, title_fields, False)
        for r in result:
            data[r["title"]] = r["value"]
        data["а"] = json.loads(data["а) Болезнь или состояние, непосредственно приведшее к смерти"])
        result_a = data["а"]["rows"][0]
        data["б"] = json.loads(data["б) патологическое состояние, которое привело к возникновению вышеуказанной причины:"])
        result_b = data["б"]["rows"][0]
        data["в"] = json.loads(data["в) первоначальная причина смерти:"])
        result_v = data["в"]["rows"][0]
        if len(result_v[2]) > 1:
            start_diag = result_v
        elif len(result_b[2]) > 1:
            start_diag = result_b
        else:
            start_diag = result_a

        description_diag = start_diag[2]
        if len(description_diag) > 1:
            description_diag_json = json.loads(description_diag)
            if len(description_diag) > 1:
                mkb10 = description_diag_json["code"]

    if i.research.is_doc_refferal:
        id_med_document_type = ID_MED_DOCUMENT_TYPE_IEMK_N3.get("is_doc_refferal")

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
            "typeResInstr": type_res_instr_iemk,
            "activityCodeResearch": i.research.code,
            "IdMedDocumentType": id_med_document_type,
            "causeDeathCodeMcb": mkb10,
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

    pks_to_set_vi = [x for x in keys if x] if t in (60020,) else []
    pks_to_set_vi_fail = [x for x in keys if x] if t in (60021,) else []

    pks_to_set_ecp = [x for x in keys if x] if t in (60022,) else []
    pks_to_set_ecp_fail = [x for x in keys if x] if t in (60022,) else []

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

        for k in pks_to_set_vi_fail:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_vi:
            Log.log(key=k, type=t, body=body.get(k, {}))

            if str(k) in body and isinstance(body[k], dict) and body[str(k)]['id']:
                d = directions.Napravleniya.objects.get(pk=k)
                d.vi_id = body[str(k)]['id']
                d.save(update_fields=['vi_id'])

        for k in pks_to_set_iemk_fail:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_iemk:
            Log.log(key=k, type=t, body=body.get(k, {}))

            d = directions.Napravleniya.objects.get(pk=k)
            d.n3_iemk_ok = True
            d.save(update_fields=['n3_iemk_ok'])

        for k in pks_to_set_ecp_fail:
            Log.log(key=k, type=t, body=body.get(str(k), body.get(k, {})))

        for k in pks_to_set_ecp:
            Log.log(key=k, type=t, body=body.get(str(k), body.get(k, {})))

            d = directions.Napravleniya.objects.get(pk=k)
            d.ecp_ok = True
            d.save(update_fields=['ecp_ok'])

            iss: Issledovaniya
            for iss in Issledovaniya.objects.filter(napravleniye_id=k):
                if str(iss.pk) in body.get(k, {}):
                    if 'ecpServiceId' in body[k][str(iss.pk)]:
                        iss.ecp_evn_id = str(body[k][str(iss.pk)]['ecpServiceId'] or '') or None
                        iss.save(update_fields=['ecp_evn_id'])

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
    return Response({"ok": False})
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
        logger.exception(e)
        message = str(e)
    except Exception as e:
        logger.exception(e)
        message = 'Серверная ошибка'

    return Response({"ok": False, 'message': message})


@api_view(['POST'])
def external_direction_create(request):
    if not hasattr(request.user, 'hospitals'):
        return Response({"ok": False, 'message': 'Некорректный auth токен'})

    body = json.loads(request.body)

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

    patient = body.get("patient", {})

    enp = (patient.get("enp") or '').replace(' ', '')

    if enp and (len(enp) != 16 or not enp.isdigit()):
        return Response({"ok": False, 'message': 'Неверные данные полиса, должно быть 16 чисел'})

    snils = (patient.get("snils") or '').replace(' ', '').replace('-', '')

    if not enp and not snils:
        return Response({"ok": False, 'message': 'При пустом patient.enp должно быть передано patient.snils или patient.passportSerial+patient.passportNumber'})

    if snils and not petrovna.validate_snils(snils):
        return Response({"ok": False, 'message': 'patient.snils: не прошёл валидацию'})

    lastname = str(patient.get("lastName") or '')
    firstname = str(patient.get('firstName') or '')
    patronymic = str(patient.get('patronymicName') or '')
    birthdate = str(patient.get('birthDate') or '')
    sex = patient.get('sex') or ''
    if sex == 1:
        sex = "м"
    else:
        sex = "ж"

    if not enp and not (lastname and firstname and birthdate and birthdate):
        return Response({"ok": False, 'message': 'При пустом patient.enp должно быть передано поле patient.individual'})

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

    individual = None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        if not individuals.exists():
            individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title='Полис ОМС') | Q(document__document_type__title='ЕНП'))
            individual = individuals.first()
        if not individual:
            tfoms_data = match_enp(enp)
            if tfoms_data:
                individuals = Individual.import_from_tfoms(tfoms_data, need_return_individual=True)

            individual = individuals.first()

    if not individual and lastname:
        tfoms_data = match_patient(lastname, firstname, patronymic, birthdate)
        if tfoms_data:
            individual = Individual.import_from_tfoms(tfoms_data, need_return_individual=True)

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title='СНИЛС')
        individual = individuals.first()

    if not individual and lastname:
        individual = Individual.import_from_tfoms(
            {
                "family": lastname,
                "given": firstname,
                "patronymic": patronymic,
                "gender": sex,
                "birthdate": birthdate,
                "enp": enp,
                "snils": snils,
            },
            need_return_individual=True,
        )

    if not individual:
        return Response({"ok": False, 'message': 'Физлицо не найдено'})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    if not card:
        card = Card.add_l2_card(individual)

    if not card:
        return Response({"ok": False, 'message': 'Карта не найдена'})

    financing_source_title = body.get("financingSource", '')
    if financing_source_title.lower() not in ["омс", "бюджет", "платно"]:
        return Response({"ok": False, 'message': 'Некорректный источник финансирования'})

    financing_source = directions.IstochnikiFinansirovaniya.objects.filter(title__iexact=financing_source_title, base__internal_type=True).first()
    financing_category_code = body.get("financingCategory", '')
    price_category = PriceCategory.objects.filter(title__startswith=financing_category_code).first()

    if not financing_source:
        return Response({"ok": False, 'message': 'Некорректный источник финансирования'})

    message = None

    id_in_hospital = body.get("internalId", '')
    if id_in_hospital is not None:
        id_in_hospital = limit_str(id_in_hospital, 15)

    department = body.get("department", '')
    additiona_info = body.get("additionalInfo", '')
    last_result_data = body.get("lastResultData", '')

    diag_text = body.get("diagText", '')  # обязательно
    if not diag_text:
        return Response({"ok": False, 'message': 'Диагноз описание не заполнено'})

    diag_mkb10 = body.get("diagMKB10", '')  # обязательно
    if not diag_mkb10:
        return Response({"ok": False, 'message': 'Диагноз по МКБ10 не заполнен (не верно)'})
    open_skob = "{"
    close_skob = "}"

    diag_mcb10_data = directions.Diagnoses.objects.filter(d_type="mkb10.4", code=diag_mkb10, hide=False).order_by("code").first()
    diag_mkb10 = f'{open_skob}"code": "{diag_mcb10_data.code}", "title": "{diag_mcb10_data.title}", "id":"{diag_mcb10_data.pk}"{close_skob}'
    obtain_material = {
        1: "эндоскопическая биопсия—1",
        2: "пункционная биопсия—2",
        3: "аспирационная биопсия—3",
        4: "инцизионная биопсия—4",
        5: "операционная биопсия—5",
        6: "операционный материал—6",
        7: "самопроизвольно отделившиеся фрагменты тканей—7",
    }
    method_obtain_material = body.get("methodObtainMaterial", '')  # обязательно code из НСИ 1.2.643.5.1.13.13.99.2.33"
    if not method_obtain_material or method_obtain_material not in [1, 2, 3, 4, 5, 6, 7]:
        return Response({"ok": False, 'message': 'Способо забора не верно заполнено'})

    resident_code = patient.get("residentCode", '')  # обязательно code из НСИ 1.2.643.5.1.13.13.11.1042"
    if not resident_code or resident_code not in [1, 2]:
        return Response({"ok": False, 'message': 'Не указан вид жительства'})
    if resident_code == 1:
        resident_data = f'{open_skob}"code": "1", "title": "Город"{close_skob}'
    else:
        resident_data = f'{open_skob}"code": "2", "title": "Село"{close_skob}'

    solution10 = body.get("solution10", '')  # обязательно
    if not solution10 or solution10 not in ["true", "false"]:
        return Response({"ok": False, 'message': 'Не указано помещен в 10% раствор'})

    doctor_fio = body.get("doctorFio", '')  # обязательно
    if not doctor_fio:
        return Response({"ok": False, 'message': 'Не указан врач производивший забор материала'})
    material_mark = body.get("materialMark", '')
    numbers_vial = []
    for k in material_mark:
        result_check = check_valid_material_mark(k, numbers_vial)
        if not result_check:
            return Response({"ok": False, 'message': 'Не верная маркировка материала'})
        numbers_vial = result_check
    if len(numbers_vial) != sorted(numbers_vial)[-1]:
        return Response({"ok": False, 'message': 'Не верная маркировка флаконов (порядок 1,2,3,4...)'})

    try:
        with transaction.atomic():
            direction = Napravleniya.objects.create(
                client=card,
                is_external=True,
                istochnik_f=financing_source,
                polis_who_give=card.polis.who_give if card.polis else None,
                polis_n=card.polis.number if card.polis else None,
                hospital=hospital,
                id_in_hospital=id_in_hospital,
                price_category=price_category,
            )

            time_get = str(body.get("dateTimeGet", "") or "") or None
            if time_get and not valid_date(time_get) or not time_get:
                raise InvalidData('Содержит некорректное поле dateTimeGet. Оно должно соответствовать шаблону YYYY-MM-DD HH:MM')

            directions.Issledovaniya.objects.create(
                napravleniye=direction,
                research_id=GISTOLOGY_RESEARCH_PK,
            )
            research = Researches.objects.filter(pk=GISTOLOGY_RESEARCH_PK).first()
            direction_params = research.direction_params
            data_marked = {
                "columns": {
                    "titles": ["Номер флакона", "Локализация патологического процесса (орган, топография)", "Характер патологического процесса", "Количество объектов", "Описание"],
                    "settings": [{"type": "rowNumber", "width": "7%"}, {"type": 0, "width": "25%"}, {"type": 10, "width": "20%"}, {"type": 18, "width": "10%"}, {"type": 0, "width": "38%"}],
                }
            }

            result_table_field = []
            pathological_process = {1: "1-Внешне неизмененная ткань", 2: "2-Узел", 3: "3-Пятно", 4: "4-Полип", 5: "5-Эрозия", 6: "6-Язва", 7: "7-Прочие"}
            for m_m in material_mark:
                result_table_field.append(
                    [str(m_m["numberVial"]), m_m.get("localization", ""), pathological_process[m_m["pathologicalProcess"]], str(m_m["objectValue"]), m_m.get("description", "")]
                )
            data_marked["rows"] = result_table_field
            match_keys = {
                "Диагноз основной": diag_text,
                "Код по МКБ": diag_mkb10,
                "Дополнительные клинические сведения": additiona_info,
                "Результаты предыдущие": last_result_data,
                "Способ получения биопсийного (операционного) материала": obtain_material[method_obtain_material],
                "Материал помещен в 10%-ный раствор нейтрального формалина": "Да" if solution10.lower() == "true" else "Нет",
                "Дата забора материала": time_get.split(" ")[0],
                "Время забора материала": time_get.split(" ")[1],
                "Маркировка материала": json.dumps(data_marked),
                "отделение": department,
                "ФИО врача": doctor_fio,
                "Вид места жительства": resident_data,
            }

            for group in ParaclinicInputGroups.objects.filter(research=direction_params):
                for f in ParaclinicInputField.objects.filter(group=group):
                    if match_keys.get(f.title, None):
                        directions.DirectionParamsResult(napravleniye=direction, title=f.title, field=f, field_type=f.field_type, value=match_keys[f.title], order=f.order).save()

            try:
                Log.log(
                    str(direction.pk),
                    122001,
                    body={"data": body},
                )
            except Exception as e:
                logger.exception(e)
            return Response({"ok": True, 'id': str(direction.pk)})

    except InvalidData as e:
        logger.exception(e)
        message = str(e)
    except Exception as e:
        logger.exception(e)
        message = 'Серверная ошибка'

    return Response({"ok": False, 'message': message})


@api_view(['POST'])
def get_directions(request):
    if not hasattr(request.user, 'hospitals'):
        return Response({"ok": False, 'message': 'Некорректный auth токен'})

    body = json.loads(request.body)
    oid_org = body.get(("oid") or '')
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, 'message': check_result["message"]})
    else:
        hospital = check_result["hospital"]
        create_from = body.get(("createFrom") or '')
        create_to = body.get(('createTo') or '')
        directions_data = Napravleniya.objects.values_list('pk', flat=True).filter(hospital=hospital, data_sozdaniya__gte=create_from, data_sozdaniya__lte=create_to)
        return Response({"ok": True, 'data': directions_data})


@api_view(['POST'])
def get_direction_data_by_num(request):
    if not hasattr(request.user, 'hospitals'):
        return Response({"ok": False, 'message': 'Некорректный auth токен'})
    body = json.loads(request.body)
    oid_org = body.get(("oid") or '')
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, 'message': check_result["message"]})

    pk = int(body.get(("directionNum") or ''))
    data_result = get_data_direction_with_param(pk)
    if not data_result:
        return Response({"ok": False})
    return Response({"ok": True, 'data': data_result})


@api_view(['POST'])
def get_direction_data_by_period(request):
    if not hasattr(request.user, 'hospitals'):
        return Response({"ok": False, 'message': 'Некорректный auth токен'})

    body = json.loads(request.body)
    oid_org = body.get(("oid") or '')
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, 'message': check_result["message"]})
    hospital = check_result["hospital"]
    create_from = body.get(("createFrom") or '')
    create_to = body.get(('createTo') or '')
    dot_format_create_from = normalize_date(create_from.split(" ")[0])
    dot_format_create_to = normalize_date(create_to.split(" ")[0])
    date_start, date_end = try_parse_range(dot_format_create_from, dot_format_create_to)
    if date_start and date_end:
        delta = date_end - date_start
        if abs(delta.days) > 2:
            return Response({"ok": False, 'message': 'Период между датами не более 48 часов'})

    directions_data = Napravleniya.objects.values_list('pk', flat=True).filter(hospital=hospital, data_sozdaniya__gte=create_from, data_sozdaniya__lte=create_to)
    result = []
    for direction_number in directions_data:
        data_result = get_data_direction_with_param(direction_number)
        if not data_result:
            continue
        result.append(data_result)
    return Response({"ok": True, 'data': result})


@api_view(['POST'])
def external_get_pdf_result(request):
    if not hasattr(request.user, 'hospitals'):
        return Response({"ok": False, 'message': 'Некорректный auth токен'})

    body = json.loads(request.body)
    oid_org = body.get(("oid") or '')
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, 'message': check_result["message"]})
    hospital = check_result["hospital"]
    pk = int(body.get(("directionNum") or ''))
    direction = directions.Napravleniya.objects.filter(hospital=hospital, pk=pk).first()
    if not direction:
        return Response({"ok": False, 'message': 'Номер направления не принадлежит организации'})
    pdf_data = direction_pdf_result(direction.pk)
    return JsonResponse({"result": pdf_data})


def check_valid_material_mark(current_material_data, current_numbers_vial):
    for k, v in current_material_data.items():
        if k == "numberVial" and not isinstance(v, int):  # обязательно число
            return False
        if k == "pathologicalProcess" and v not in [1, 2, 3, 4, 5, 6, 7]:  # "code из НСИ 1.2.643.5.1.13.13.99.2.34" обязательно
            return False
        if k == "objectValue" and not isinstance(v, int):  # обязательно число
            return False
        if k == "description" and v and not isinstance(v, str):
            return False
        if k == "localization" and v and not isinstance(v, str):
            return False
    if current_material_data["numberVial"] in current_numbers_vial:
        return False
    else:
        current_numbers_vial.append(current_material_data["numberVial"])
    return current_numbers_vial


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
    if check_type_research(pk) == "is_refferal":
        data = get_json_protocol_data(pk)
    elif check_type_research(pk) == "is_lab":
        data = get_json_labortory_data(pk)
    elif check_type_research(pk) == "is_paraclinic":
        data = get_json_protocol_data(pk, is_paraclinic=True)
    else:
        data = {}
    data_individual = card.get_data_individual()
    p_enp_re = re.compile(r'^[0-9]{16}$')
    p_enp = bool(re.search(p_enp_re, card.get_data_individual()['oms']['polis_num']))
    if p_enp:
        return {
            "title": n.get_eds_title(),
            "generatorName": n.get_eds_generator(),
            "rawResponse": True,
            "data": {
                "oidMo": data["oidMo"],
                "document": data,
                "patient": {
                    'id': card.number,
                    'snils': data_individual["snils"],
                    'name': {'family': ind.family, 'name': ind.name, 'patronymic': ind.patronymic},
                    'gender': ind.sex.lower(),
                    'birthdate': ind.birthday.strftime("%Y%m%d"),
                    'oms': {'number': card.get_data_individual()['oms']['polis_num'], 'issueOrgName': '', 'issueOrgCode': ''},
                },
                "organization": data["organization"],
            },
        }
    return {}


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


@api_view(['POST'])
def get_protocol_result(request):
    body = json.loads(request.body)
    pk = body.get("pk")
    n: Napravleniya = Napravleniya.objects.get(pk=pk)
    card = n.client
    ind = n.client.individual
    if check_type_research(pk) == "is_refferal":
        data = get_json_protocol_data(pk)
        return Response(
            {
                "title": n.get_eds_title(),
                "generatorName": n.get_eds_generator(),
                "data": {
                    "oidMo": data["oidMo"],
                    "document": data,
                    "patient": {
                        'id': card.number,
                        'snils': card.get_data_individual()["snils"],
                        'name': {'family': ind.family, 'name': ind.name, 'patronymic': ind.patronymic},
                        'gender': ind.sex.lower(),
                        'birthdate': ind.birthday.strftime("%Y%m%d"),
                    },
                    "organization": data["organization"],
                },
            }
        )
    elif check_type_research(pk) == "is_lab":
        data = get_json_labortory_data(pk)
        return Response(
            {
                "generatorName": "Laboratory_min",
                "data": {
                    "oidMo": data["oidMo"],
                    "document": data,
                    "patient": {
                        'id': card.number,
                        'snils': card.get_data_individual()["snils"],
                        'name': {'family': ind.family, 'name': ind.name, 'patronymic': ind.patronymic},
                        'gender': ind.sex.lower(),
                        'birthdate': ind.birthday.strftime("%Y%m%d"),
                    },
                    "organization": data["organization"],
                },
            }
        )
    elif check_type_research(pk) == "is_paraclinic":
        data = get_json_protocol_data(pk, is_paraclinic=True)
        return Response(
            {
                "title": n.get_eds_title(),
                "generatorName": n.get_eds_generator(),
                "data": {
                    "oidMo": data["oidMo"],
                    "document": data,
                    "patient": {
                        'id': card.number,
                        'snils': card.get_data_individual()["snils"],
                        'name': {'family': ind.family, 'name': ind.name, 'patronymic': ind.patronymic},
                        'gender': ind.sex.lower(),
                        'birthdate': ind.birthday.strftime("%Y%m%d"),
                    },
                    "organization": data["organization"],
                },
            }
        )

    return Response({})


@api_view(['POST', 'GET'])
def get_hosp_services(request):
    services = []
    r: Researches
    for r in Researches.objects.filter(is_hospital=True):
        services.append(
            {
                "pk": r.pk,
                "title": r.get_title(),
            }
        )
    return Response({"services": services})


@api_view(['GET'])
def mkb10(request):
    return Response({"rows": mkb10_dict(request, True)})


@api_view(['POST', 'PUT'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@can_use_schedule_only
def hosp_record(request):
    files = []
    if request.method == 'PUT':
        for kf in request.data:
            if kf != 'document':
                files.append(request.data[kf])
        form = request.data['document']
    else:
        form = request.body

    data = data_parse(
        form,
        {
            'snils': 'str_strip',
            'enp': 'str_strip',
            'family': 'str_strip',
            'name': 'str_strip',
            'patronymic': 'str_strip',
            'sex': 'str_strip',
            'birthdate': 'str_strip',
            'comment': 'str_strip',
            'date': 'str_strip',
            'service': int,
            'phone': 'str_strip',
            'diagnosis': 'str_strip',
        },
    )

    if len(files) > LK_FILE_COUNT:
        return Response({"ok": False, 'message': 'Слишком много файлов'})

    for f in files:
        if f.size > LK_FILE_SIZE_BYTES:
            return Response({"ok": False, 'message': 'Файл слишком большой'})
        if not check_type_file(file_in_memory=f):
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Поддерживаются PDF и JPEG файлы",
                }
            )

    snils: str = data[0]
    enp: str = data[1]
    family: str = data[2]
    name: str = data[3]
    patronymic: str = data[4]
    sex: str = data[5].lower()
    birthdate: str = data[6]
    comment: str = data[7]
    date: str = data[8]
    service: int = data[9]
    phone: str = data[10]
    diagnosis: str = data[11]

    if sex == 'm':
        sex = 'м'

    if sex == 'f':
        sex = 'ж'

    snils = ''.join(ch for ch in snils if ch.isdigit())

    individual = None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        individual = individuals.first()

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title='СНИЛС')
        individual = individuals.first()

    if not individual and family and name:
        individual = Individual.import_from_tfoms(
            {
                "family": family,
                "given": name,
                "patronymic": patronymic,
                "gender": sex,
                "birthdate": birthdate,
                "enp": enp,
                "snils": snils,
            },
            need_return_individual=True,
        )
    if not individual:
        return Response({"ok": False, 'message': 'Физлицо не найдено'})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    if not card:
        card = Card.add_l2_card(individual)

    if not card:
        return Response({"ok": False, 'message': 'Карта не найдена'})

    if SCHEDULE_AGE_LIMIT_LTE:
        age = card.individual.age()
        if age > SCHEDULE_AGE_LIMIT_LTE:
            return Response({"ok": False, 'message': f'Пациент должен быть не старше {SCHEDULE_AGE_LIMIT_LTE} лет'})

    hospital_research: Researches = Researches.objects.filter(pk=service, is_hospital=True).first()

    if not hospital_research:
        return Response({"ok": False, 'message': 'Услуга не найдена'})

    has_free_slots = check_available_hospital_slot_before_save(hospital_research.pk, None, date)
    if not has_free_slots:
        return JsonResponse({"ok": False, "message": "Нет свободных слотов"})

    hosp_department_id = hospital_research.podrazdeleniye.pk
    with transaction.atomic():
        plan_pk = PlanHospitalization.plan_hospitalization_save(
            {
                'card': card,
                'research': hospital_research.pk,
                'date': date,
                'comment': comment[:256],
                'phone': phone,
                'action': 0,
                'hospital_department_id': hosp_department_id,
                'diagnos': diagnosis,
                'files': files,
            },
            None,
        )
        for f in files:
            plan_files: PlanHospitalizationFiles = PlanHospitalizationFiles(plan_id=plan_pk)

            plan_files.uploaded_file = f
            plan_files.save()
    y, m, d = date.split('-')
    return Response({"ok": True, "message": f"Запись создана — {hospital_research.get_title()} {d}.{m}.{y}"})


@api_view(['POST'])
@can_use_schedule_only
def hosp_record_list(request):
    data = data_parse(
        request.body,
        {
            'snils': 'str_strip',
            'enp': 'str_strip',
        },
    )
    snils: str = data[0]
    enp: str = data[1]

    snils = ''.join(ch for ch in snils if ch.isdigit())

    individual = None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        individual = individuals.first()

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title='СНИЛС')
        individual = individuals.first()

    if not individual:
        return Response({"rows": [], 'message': 'Физлицо не найдено'})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()

    if not card:
        return Response({"rows": [], 'message': 'Карта не найдена'})

    rows = []

    plan: PlanHospitalization
    for plan in PlanHospitalization.objects.filter(client=card, research__isnull=False, action=0).order_by('-exec_at'):
        status_description = ""
        if plan.work_status == 2:
            status_description = plan.why_cancel
        if plan.work_status == 3:
            slot_plan = plan.slot_fact.plan
            status_description = slot_plan.datetime.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%d.%m.%Y %H:%M')
        rows_files = []
        row_file: PlanHospitalizationFiles
        for row_file in PlanHospitalizationFiles.objects.filter(plan=plan).order_by('-created_at'):
            rows_files.append(
                {
                    'pk': row_file.pk,
                    'fileName': os.path.basename(row_file.uploaded_file.name) if row_file.uploaded_file else None,
                }
            )
        messages_data = Messages.get_messages_by_plan_hosp(plan.pk, last=True)
        rows.append(
            {
                "pk": plan.pk,
                "service": plan.research.get_title(),
                "date": plan.exec_at.strftime('%d.%m.%Y'),
                "phone": plan.phone,
                "diagnosis": plan.diagnos,
                "comment": plan.comment,
                "status": plan.get_work_status_display(),
                "status_description": status_description,
                "files": rows_files,
                "messages": messages_data,
            }
        )

    return Response({"rows": rows})


@api_view(['POST'])
def get_all_messages_by_plan_id(request):
    data = data_parse(request.body, {'pk': int})
    pk: int = data[0]
    messages = Messages.get_messages_by_plan_hosp(pk, last=False)
    return Response({"rows": messages})


@api_view(['POST'])
def direction_records(request):
    data = data_parse(
        request.body,
        {'snils': 'str_strip', 'enp': 'str_strip', 'date_year': int},
    )
    snils: str = data[0]
    enp: str = data[1]
    date_year: int = data[2]

    card: Card = find_patient(snils, enp)
    if not card:
        return Response({"rows": [], 'message': 'Карта не найдена'})
    d1 = try_strptime(f"{date_year}-01-01", formats=('%Y-%m-%d',))
    d2 = try_strptime(f"{date_year}-12-31", formats=('%Y-%m-%d',))
    start_date = datetime.datetime.combine(d1, datetime.time.min)
    end_date = datetime.datetime.combine(d2, datetime.time.max)
    rows = {}
    collect_direction = direction_by_card(start_date, end_date, card.pk)
    prev_direction = None
    unique_direction = set([i.napravleniye_id for i in collect_direction])
    not_confirm_direction = get_not_confirm_direction(list(unique_direction))
    not_confirm_direction = [i[0] for i in not_confirm_direction]
    confirm_direction = list(unique_direction - set(not_confirm_direction))
    for dr in collect_direction:
        if dr.napravleniye_id in confirm_direction:
            status = 2
            date_confirm = dr.date_confirm
        elif dr.cancel:
            date_confirm = ""
            status = -1
        else:
            date_confirm = ""
            status = 0
        if dr.napravleniye_id != prev_direction:
            rows[dr.napravleniye_id] = {"createdAt": dr.date_create, "services": [], "status": status, "confirmedAt": date_confirm}
        temp_research = rows.get(dr.napravleniye_id, None)
        temp_research["services"].append(dr.research_title)
        rows[dr.napravleniye_id] = temp_research.copy()
        prev_direction = dr.napravleniye_id

    category_directions = get_type_confirm_direction(tuple(confirm_direction))
    lab_podr = get_lab_podr()
    lab_podr = [i[0] for i in lab_podr]
    count_paraclinic = 0
    count_doc_refferal = 0
    count_laboratory = 0
    for dr in category_directions:
        if dr.is_doc_refferal:
            count_paraclinic += 1
        elif dr.is_paraclinic:
            count_doc_refferal += 1
        elif dr.podrazdeleniye_id in lab_podr:
            count_laboratory += 1

    return Response({"rows": rows, "count_paraclinic": count_paraclinic, "count_doc_refferal": count_doc_refferal, "count_laboratory": count_laboratory})


@api_view(['POST'])
def directions_by_category_result_year(request):
    request_data = json.loads(request.body)
    mode = request_data.get('mode')
    is_lab = request_data.get('isLab', mode == 'laboratory')
    is_paraclinic = request_data.get('isParaclinic', mode == 'paraclinic')
    is_doc_refferal = request_data.get('isDocReferral', mode == 'docReferral')
    is_extract = request_data.get('isExtract', mode == 'extract')
    is_user_forms = request_data.get('isUserForms', mode == 'forms')
    year = request_data['year']

    card: Card = find_patient(request_data.get('snils'), request_data.get('enp'))
    if not card:
        return Response({"results": [], 'message': 'Карта не найдена'})

    d1 = datetime.datetime.strptime(f'{LK_DAY_MONTH_START_SHOW_RESULT}{year}', '%d.%m.%Y')
    start_date = datetime.datetime.combine(d1, datetime.time.min)
    d2 = datetime.datetime.strptime(f'31.12.{year}', '%d.%m.%Y')
    end_date = datetime.datetime.combine(d2, datetime.time.max)

    if not is_lab and not is_doc_refferal and not is_paraclinic and not is_extract and not is_user_forms:
        return JsonResponse({"results": []})

    if is_lab:
        lab_podr = get_lab_podr()
        lab_podr = [i[0] for i in lab_podr]
    else:
        lab_podr = [-1]

    confirmed_directions = None
    if is_extract:
        extract_research_pks = tuple(HospitalService.objects.values_list('slave_research__id', flat=True).filter(site_type=7))
        if extract_research_pks:
            confirmed_directions = get_confirm_direction_patient_year_is_extract(start_date, end_date, card.pk, extract_research_pks)

    if not is_extract and not confirmed_directions:
        confirmed_directions = get_confirm_direction_patient_year(start_date, end_date, lab_podr, card.pk, is_lab, is_paraclinic, is_doc_refferal, is_user_forms)

    if not confirmed_directions:
        return JsonResponse({"results": []})

    directions = {}

    for d in confirmed_directions:
        if d.direction not in directions:
            directions[d.direction] = {'pk': d.direction, 'confirmedAt': d.ch_time_confirmation, 'services': [], 'study': d.study_instance_uid_tag}
        directions[d.direction]['services'].append(d.research_title)
    return JsonResponse({"results": list(directions.values())})


@api_view(['POST'])
def results_by_direction(request):
    request_data = json.loads(request.body)
    if not hasattr(request.user, 'hospitals'):
        return Response({"ok": False, 'message': 'Некорректный auth токен'})
    oid_org = request_data.get(("oid") or '')
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, 'message': check_result["message"]})
    hospital = check_result["hospital"]
    mode = request_data.get('mode')
    is_lab = request_data.get('isLab', mode == 'laboratory')
    is_paraclinic = request_data.get('isParaclinic', mode == 'paraclinic')
    is_doc_refferal = request_data.get('isDocReferral', mode == 'docReferral')
    is_user_forms = request_data.get('isUserFroms', mode == 'forms')
    direction = request_data.get('pk')
    directions = request_data.get('directions', [])
    if is_lab and not directions:
        directions = [direction]
    else:
        directions = [direction]
    for d in directions:
        direction_obj = Napravleniya.objects.filter(hospital=hospital, pk=d).first()
        if not direction_obj:
            return Response({"ok": False, 'message': 'Номер направления не принадлежит организации'})

    objs_result = {}
    if is_lab:
        direction_result = get_laboratory_results_by_directions(directions)

        for r in direction_result:
            if r.direction not in objs_result:
                objs_result[r.direction] = {'pk': r.direction, 'confirmedAt': r.date_confirm, 'services': {}}

            if r.iss_id not in objs_result[r.direction]['services']:
                objs_result[r.direction]['services'][r.iss_id] = {'title': r.research_title, 'fio': short_fio_dots(r.fio), 'confirmedAt': r.date_confirm, 'fractions': []}

            objs_result[r.direction]['services'][r.iss_id]['fractions'].append({'title': r.fraction_title, 'value': r.value, 'units': r.units})

    if is_paraclinic or is_doc_refferal or is_user_forms:
        results = desc_to_data(directions, force_all_fields=True)
        for i in results:
            direction_data = i['result'][0]["date"].split(' ')
            if direction_data[1] not in objs_result:
                objs_result[direction_data[1]] = {'pk': direction_data[1], 'confirmedAt': direction_data[0], 'services': {}}
            if i['result'][0]["iss_id"] not in objs_result[direction_data[1]]['services']:
                objs_result[direction_data[1]]['services'][i['result'][0]["iss_id"]] = {
                    'title': i['title_research'],
                    'fio': short_fio_dots(i['result'][0]["docConfirm"]),
                    'confirmedAt': direction_data[0],
                    'fractions': [],
                }

            values = values_as_structure_data(i['result'][0]["data"])
            objs_result[direction_data[1]]['services'][i['result'][0]["iss_id"]]["fractions"].extend(values)

    return JsonResponse({"results": list(objs_result.values())})


@api_view(['POST'])
@can_use_schedule_only
def check_employee(request):
    data = json.loads(request.body)
    snils = data.get('snils')
    date_now = current_time(only_date=True)
    doctor_profile = DoctorProfile.objects.filter(snils=snils, external_access=True, date_stop_external_access__gte=date_now).first()
    if doctor_profile:
        return Response({"ok": True})
    return Response({"ok": False})


@api_view(['GET'])
@can_use_schedule_only
def hospitalization_plan_research(request):
    return Response({"services": get_hospital_resource()})


@api_view(['POST'])
@can_use_schedule_only
def available_hospitalization_plan(request):
    data = json.loads(request.body)
    research_pk = data.get('research_pk')
    resource_id = data.get('resource_id')
    date_start = data.get('date_start')
    date_end = data.get('date_end')

    result, _ = get_available_hospital_plans(research_pk, resource_id, date_start, date_end)
    return Response({"data": result})


@api_view(['POST'])
@can_use_schedule_only
def check_hosp_slot_before_save(request):
    data = json.loads(request.body)
    research_pk = data.get('research_pk')
    resource_id = data.get('resource_id')
    date = data.get('date')

    result = check_available_hospital_slot_before_save(research_pk, resource_id, date)
    return JsonResponse({"result": result})


@api_view(['POST'])
@can_use_schedule_only
def get_pdf_result(request):
    data = json.loads(request.body)
    pk = data.get('pk')
    pdf_content = direction_pdf_result(pk)
    return JsonResponse({"result": pdf_content})


@api_view(['POST'])
@can_use_schedule_only
def get_pdf_direction(request):
    data = json.loads(request.body)
    pk = data.get('pk')
    localclient = TC(enforce_csrf_checks=False)
    addr = "/directions/pdf"
    params = {"napr_id": json.dumps([pk]), 'token': "8d63a9d6-c977-4c7b-a27c-64f9ba8086a7"}
    result = localclient.get(addr, params).content
    pdf_content = base64.b64encode(result).decode('utf-8')
    return JsonResponse({"result": pdf_content})


@api_view(['POST'])
@can_use_schedule_only
def documents_lk(request):
    return Response({"documents": get_can_created_patient()})


@api_view(['POST'])
@can_use_schedule_only
def details_document_lk(request):
    data = data_parse(
        request.body,
        {'pk': int},
    )
    pk: int = data[0]
    response = get_researches_details(pk)
    return Response(response)


@api_view(['POST'])
@can_use_schedule_only
def forms_lk(request):
    response = {"forms": LK_FORMS}
    return Response(response)


@api_view(['POST'])
@can_use_schedule_only
def pdf_form_lk(request):
    data = data_parse(
        request.body,
        {'type_form': str, 'snils': str, 'enp': str, 'agent': {'snils': str, 'enp': str}},
    )
    type_form: str = data[0]
    snils: str = data[1]
    enp: str = data[2]

    card: Card = find_patient(snils, enp)
    if not card:
        return Response({"results": [], 'message': 'Карта не найдена'})

    f = import_string('forms.forms' + type_form[0:3] + '.form_' + type_form[4:6])
    user = User.objects.get(pk=LK_USER)
    result = f(
        request_data={
            "card_pk": card,
            "user": user,
            "hospital": user.doctorprofile.get_hospital(),
        }
    )
    pdf_content = base64.b64encode(result).decode('utf-8')
    return Response({"result": pdf_content})


@api_view(['POST', 'PUT'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@can_use_schedule_only
def add_file_hospital_plan(request):
    file = request.data.get('file-add')
    data = data_parse(request.data.get('document'), {'pk': int})
    pk: int = data[0]

    with transaction.atomic():
        plan: PlanHospitalization = PlanHospitalization.objects.select_for_update().get(pk=pk)

        if file.size > LK_FILE_SIZE_BYTES:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Файл слишком большой",
                }
            )

        if PlanHospitalizationFiles.get_count_files_by_plan(plan) >= LK_FILE_COUNT:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Вы добавили слишком много файлов в одну заявку",
                }
            )

        if not check_type_file(file_in_memory=file):
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Поддерживаются PDF и JPEG файлы",
                }
            )

        plan_files: PlanHospitalizationFiles = PlanHospitalizationFiles(plan=plan)

        plan_files.uploaded_file = file
        plan_files.save()

    return Response(
        {
            "ok": True,
            "message": "Файл добавлен",
        }
    )


@api_view(['POST'])
@can_use_schedule_only
def get_limit_download_files(request):
    return Response({"lk_file_count": LK_FILE_COUNT, "lk_file_size_bytes": LK_FILE_SIZE_BYTES})


@api_view(['POST'])
@can_use_schedule_only
def document_lk_save(request):
    form = request.body

    data = data_parse(
        form,
        {
            'snils': 'str_strip',
            'enp': 'str_strip',
            'family': 'str_strip',
            'name': 'str_strip',
            'patronymic': 'str_strip',
            'sex': 'str_strip',
            'birthdate': 'str_strip',
            'service': int,
            'groups': list,
            'phone': 'str_strip',
        },
        {
            'phone': '',
        },
    )

    snils: str = data[0]
    enp: str = data[1]
    family: str = data[2]
    name: str = data[3]
    patronymic: str = data[4]
    sex: str = data[5].lower()
    birthdate: str = data[6]
    service: int = data[7]
    groups: dict = data[8]
    phone: str = data[9]

    if sex == 'm':
        sex = 'м'

    if sex == 'f':
        sex = 'ж'

    snils = ''.join(ch for ch in snils if ch.isdigit())

    individual = None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        individual = individuals.first()

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title='СНИЛС')
        individual = individuals.first()

    if not individual and family and name:
        individual = Individual.import_from_tfoms(
            {
                "family": family,
                "given": name,
                "patronymic": patronymic,
                "gender": sex,
                "birthdate": birthdate,
                "enp": enp,
                "snils": snils,
            },
            need_return_individual=True,
        )
    if not individual:
        return Response({"ok": False, 'message': 'Физлицо не найдено'})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    if not card:
        card = Card.add_l2_card(individual)

    if not card:
        return Response({"ok": False, 'message': 'Карта не найдена'})

    if SCHEDULE_AGE_LIMIT_LTE:
        age = card.individual.age()
        if age > SCHEDULE_AGE_LIMIT_LTE:
            return Response({"ok": False, 'message': f'Пациент должен быть не старше {SCHEDULE_AGE_LIMIT_LTE} лет'})

    service: Researches = Researches.objects.filter(pk=service, can_created_patient=True).first()

    if not service:
        return Response({"ok": False, 'message': 'Услуга не найдена'})

    date = timezone.now()
    date_start = date_at_bound(date)

    user = User.objects.get(pk=LK_USER).doctorprofile

    if Napravleniya.objects.filter(client=card, issledovaniya__research=service, data_sozdaniya__gte=date_start).count() > 1:
        return Response({"ok": False, 'message': 'Вы сегодня уже заполняли эту форму два раза!\nПопробуйте позднее.'})

    with transaction.atomic():
        result = Napravleniya.gen_napravleniya_by_issledovaniya(
            card.pk,
            "",
            "ОМС",
            "",
            None,
            user,
            {-1: [service.pk]},
            {},
            False,
            {},
            vich_code="",
            count=1,
            discount=0,
            parent_iss=None,
        )

        direction = result["list_id"][0]

        iss = Issledovaniya.objects.filter(napravleniye_id=direction)[0]

        iss.doc_save = user
        iss.time_save = date
        iss.doc_confirmation = user
        iss.time_confirmation = date
        iss.save()
        if iss.napravleniye:
            iss.napravleniye.sync_confirmed_fields()
            iss.napravleniye.visit_who_mark = user
            iss.napravleniye.visit_date = date
            iss.napravleniye.save()

        fields_count = 0

        comment_lines = []

        for g in groups[:50]:
            if g['title'] and g['show_title']:
                comment_lines.append(f"{g['title']}:")

            for f in g['fields'][:50]:
                if not f['new_value']:
                    continue
                fields_count += 1
                f_result = directions.ParaclinicResult(issledovaniye=iss, field_id=f['pk'], field_type=f['field_type'], value=html.escape(f['new_value'][:400]))

                f_result.save()

                line = ""
                if f_result.field.title:
                    line = f"{f_result.field.title}: "
                line += f_result.value
                comment_lines.append(line)

        if fields_count == 0:
            transaction.set_rollback(True)
            return Response({"ok": False})
        elif service.convert_to_doc_call:
            if not phone:
                return Response({"ok": False, "message": "Телефон должен быть заполнен"})
            hospital = Hospitals.get_default_hospital()
            DoctorCall.doctor_call_save(
                {
                    'card': card,
                    'research': service.pk,
                    'address': card.main_address,
                    'district': -1,
                    'date': current_time(),
                    'comment': '\n'.join(comment_lines),
                    'phone': phone,
                    'doc': -1,
                    'purpose': 24,
                    'hospital': hospital.pk,
                    'external': True,
                    'external_num': str(direction),
                    'is_main_external': False,
                    'direction': direction,
                }
            )
            return Response({"ok": True, "message": f"Заявка {direction} зарегистрирована"})

    return Response({"ok": True, "message": f"Форма \"{service.get_title()}\" ({direction}) сохранена"})


@api_view(['POST'])
def amd_save(request):
    data = json.loads(request.body)
    local_uid = data.get('localUid')
    direction_pk = data.get('pk')
    status = data.get('status')
    message_id = data.get('messageId')
    message = data.get('message')
    kind = data.get('kind')
    organization_oid = data.get('organizationOid')
    hospital = Hospitals.objects.filter(oid=organization_oid).first()

    emdr_id = data.get('emdrId')
    registration_date = data.get('registrationDate')
    if registration_date:
        registration_date = datetime.datetime.strptime(registration_date, '%Y-%m-%d %H:%M:%S')

    type = data.get('type')
    if type and type == "registerDocument":
        time_exec = data.get('timeExec')
        time_exec = datetime.datetime.strptime(time_exec, '%Y-%m-%d %H:%M:%S')
        department_oid = data.get('departmentOid')
        podrazdeleniye = Podrazdeleniya.objects.filter(oid=department_oid).first()
        amd = ArchiveMedicalDocuments(
            local_uid=local_uid,
            direction_id=direction_pk,
            status=status,
            message_id=message_id,
            hospital=hospital,
            department=podrazdeleniye,
            message=message,
            kind=kind,
            time_exec=time_exec,
        )
        amd.save()
    elif type and type == "getDocumentFile":
        amd = ArchiveMedicalDocuments.objects.get(hospital=hospital, local_uid=local_uid, direction_id=direction_pk)
        amd.emdr_id = emdr_id
        amd.registration_date = registration_date
        amd.save()
    elif type and type == "sendRegisterDocumentResult":
        amd = ArchiveMedicalDocuments.objects.get(message_id=message_id)
        amd.emdr_id = emdr_id
        amd.registration_date = registration_date
        code = data.get('code')
        amd.message = f"{code}@{message}"
        amd.save()
    return Response({"ok": True})


@api_view(['POST'])
def register_emdr_id(request):
    data = json.loads(request.body)
    emdr_id = data.get('localUid')
    direction_pk = data.get('pk')
    direction = Napravleniya.objects.get(pk=direction_pk)
    direction.emdr_id = emdr_id
    direction.save(update_fields=['emdr_id'])
    return Response({"ok": True})


@api_view(['POST'])
def get_direction_pk_by_emdr_id(request):
    data = json.loads(request.body)
    emdr_id = data.get('emdrId')
    direction = Napravleniya.objects.get(emdr_id=emdr_id)
    return Response({"pk": direction.pk})
