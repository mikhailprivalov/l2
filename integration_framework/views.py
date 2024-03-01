import base64
import collections
import hashlib
import os
import html
import uuid
import zlib

from django.core.paginator import Paginator
from django.test import Client as TC
import datetime
import logging

import pytz_deprecation_shim as pytz
from django.utils.module_loading import import_string

from api.dicom import check_dicom_study
from api.directions.sql_func import direction_by_card, get_lab_podr, get_confirm_direction_patient_year, get_type_confirm_direction, get_confirm_direction_patient_year_is_extract
from api.models import Application
from api.patients.views import patients_search_card
from api.stationar.stationar_func import desc_to_data, hosp_get_data_direction
from api.views import mkb10_dict
from clients.utils import find_patient
from contracts.models import PriceCategory, PriceCoast, PriceName
from directory.utils import get_researches_details, get_can_created_patient
from doctor_schedule.views import get_hospital_resource, get_available_hospital_plans, check_available_hospital_slot_before_save
from external_system.models import ArchiveMedicalDocuments, InstrumentalResearchRefbook
from ftp_orders.main import ServiceNotFoundException, InvalidOrderNumberException, FailedCreatingDirectionsException
from integration_framework.authentication import can_use_schedule_only, IndividualAuthentication

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
from django.http import JsonResponse, HttpRequest
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response

import directions.models as directions
from appconf.manager import SettingManager
from clients.models import Individual, Card, CardBase, Phones
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
    HOSPITAL_PKS_NOT_CONTROL_DOCUMENT_EXTERNAL_CREATE_DIRECTION,
    DICOM_SERVERS,
    DICOM_SERVER,
)
from laboratory.utils import current_time, date_at_bound, strfdatetime
from refprocessor.result_parser import ResultRight
from researches.models import Tubes
from results.prepare_data import fields_result_only_title_fields
from results.sql_func import get_laboratory_results_by_directions, get_not_confirm_direction
from results_feed.models import ResultFeed
from rmis_integration.client import Client
from slog.models import Log
from tfoms.integration import match_enp, match_patient, get_ud_info_by_enp, match_patient_by_snils, get_dn_info_by_enp
from users.models import DoctorProfile
from utils.common import values_as_structure_data
from utils.data_verification import data_parse
from utils.dates import normalize_date, valid_date, try_strptime, try_parse_range, normalize_dots_date
from utils.nsi_directories import NSI
from utils.response import status_response
from utils.xh import check_type_research, short_fio_dots
from . import sql_if
from directions.models import DirectionDocument, DocumentSign, Issledovaniya, Napravleniya
from .common_func import check_correct_hosp, get_data_direction_with_param, direction_pdf_result, check_correct_hospital_company, check_correct_hospital_company_for_price
from .models import CrieOrder, ExternalService, IndividualAuth, IPLimitter
from laboratory.settings import COVID_RESEARCHES_PK
from .tasks import send_code_cascade, stop_code_cascade
from .utils import get_json_protocol_data, get_json_labortory_data, check_type_file, legal_auth_get, author_doctor
from django.contrib.auth.models import User
from directory.sql_func import get_lab_research_reference_books

logger = logging.getLogger("IF")


@api_view()
def next_result_direction(request):
    from_pk = request.GET.get("fromPk")
    after_date = request.GET.get("afterDate")
    only_signed = request.GET.get("onlySigned")
    if after_date == "0":
        after_date = AFTER_DATE
    next_n = int(request.GET.get("nextN", 1))
    type_researches = request.GET.get("research", "*")
    d_start = f"{after_date}"
    is_research = 1
    researches = [-999]
    if type_researches == "lab":
        researches = [x.pk for x in Researches.objects.filter(podrazdeleniye__p_type=Podrazdeleniya.LABORATORY)]
    elif type_researches == "gistology":
        researches = [x.pk for x in Researches.objects.filter(is_gistology=True)]
    elif type_researches == "paraclinic":
        researches = [x.pk for x in Researches.objects.filter(is_paraclinic=True)]
    elif type_researches == "is_extract":
        researches_hosp = [x for x in Researches.objects.filter(is_hospital=True)]
        researches = [x.pk for x in researches_hosp if x.is_extract()]
    elif type_researches != "*":
        researches = [int(i) for i in type_researches.split(",")]
    else:
        is_research = -1
    dirs, dirs_eds = None, None
    if only_signed == "1":
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
def get_dir_cpp(request):
    next_n = int(request.GET.get("nextN", 5))
    direction_pk = request.GET.get("idDirection", None)
    dirs = None
    if not direction_pk:
        dirs = sql_if.direction_resend_cpp(next_n)
    result = {"ok": False, "next": []}
    data_direction = []
    if dirs:
        result = {"ok": True}
        dirs_data = [i.id for i in dirs]
    else:
        dirs_data = [i for i in json.loads(direction_pk)]
    direction_document = DirectionDocument.objects.filter(direction__in=dirs_data, file_type="cpp")
    for d in direction_document:
        with open(d.file.name, "rb") as f:
            digest = hashlib.file_digest(f, "md5")
            md5_file = digest.hexdigest()
            f.close()
        zip_file = d.file.open(mode="rb")
        bs64_zip = base64.b64encode(zip_file.read())
        md5_checksum_file = base64.b64encode(md5_file.encode("utf-8"))
        data_direction.append({"directionNumbrer": d.direction_id, "bs64Zip": bs64_zip, "md5file": md5_checksum_file})
    result["next"] = data_direction
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
    if result["error"]:
        for i in result["error"]:
            dir_pk = int(i.split(":")[0])
            directions.Napravleniya.objects.filter(pk=dir_pk).update(need_resend_amd=False, error_amd=True)
        resp = {"ok": True}
    if result["send"]:
        for i in result["send"]:
            data_amd = i.split(":")
            dir_pk = int(data_amd[0])
            amd_num = data_amd[1]
            directions.Napravleniya.objects.filter(pk=dir_pk).update(need_resend_amd=False, amd_number=amd_num, error_amd=False)
        resp = {"ok": True}
    return Response(resp)


@api_view()
def result_cpp_send(request):
    result = json.loads(request.GET.get("result"))
    resp = {"ok": False}
    if result["send"]:
        for i in result["send"]:
            data_amd = i.split(":")
            dir_pk = int(data_amd[0])
            cpp_upload_id = data_amd[1]
            directions.Napravleniya.objects.filter(pk=dir_pk).update(need_resend_cpp=False, cpp_upload_id=cpp_upload_id)
        resp = {"ok": True}
    return Response(resp)


@api_view()
def direction_data(request):
    pk = request.GET.get("pk")
    research_pks = request.GET.get("research", "*")
    only_cda = request.GET.get("onlyCDA", False)
    direction: directions.Napravleniya = directions.Napravleniya.objects.select_related("istochnik_f", "client", "client__individual", "client__base").get(pk=pk)
    card = direction.client
    individual = card.individual

    iss = directions.Issledovaniya.objects.filter(napravleniye=direction, time_confirmation__isnull=False).select_related("research", "doc_confirmation")
    if research_pks != "*":
        iss = iss.filter(research__pk__in=research_pks.split(","))
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
            if only_cda and d.file_type.upper() != "CDA":
                continue
            document = {
                "type": d.file_type.upper(),
                "content": base64.b64encode(d.file.read()).decode("utf-8"),
                "signatures": [],
            }

            for s in DocumentSign.objects.filter(document=d):
                document["signatures"].append(
                    {
                        "content": s.sign_value.replace("\n", ""),
                        "type": s.sign_type,
                        "executor": s.executor.uploading_data,
                        "crc32": zlib.crc32(base64.b64decode(s.sign_value.replace("\n", "").encode())),
                    }
                )

            signed_documents.append(document)

    return Response(
        {
            "ok": True,
            "pk": pk,
            "createdAt": direction.data_sozdaniya,
            "patient": {
                "id": card.pk,
                **card.get_data_individual(full_empty=True, only_json_serializable=True),
                "family": individual.family,
                "name": individual.name,
                "patronymic": individual.patronymic,
                "birthday": individual.birthday,
                "docs": card.get_n3_documents(),
                "sex": individual.sex,
                "gender": individual.sex.lower(),
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
            "researchName": iss[iss_index].research.oid_title if iss[iss_index].doc_confirmation else None,
            "finSourceTitle": direction.istochnik_f.title if direction.istochnik_f else "другое",
            "finSourceCode": direction.istochnik_f.get_n3_code() if direction.istochnik_f else "6",
            "finSourceEcpCode": direction.istochnik_f.get_ecp_code() if direction.istochnik_f else "380101000000023",
            "oldPk": direction.core_id,
            "isExternal": direction.is_external,
            "titleInitiator": direction.get_title_org_initiator(),
            "ogrnInitiator": direction.get_ogrn_org_initiator(),
            "titleLaboratory": direction.hospital_title.replace('"', " "),
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
            "author": author_doctor(iss[iss_index].doc_confirmation) if iss[iss_index].doc_confirmation else None,
            "legalAuthenticator": legal_auth_get({"id": iss[iss_index].doc_confirmation.get_hospital().legal_auth_doc_id}, as_uploading_data=True),
        }
    )


def format_time_if_is_not_none(t):
    if not t:
        return None
    return "{:%Y-%m-%d %H:%M}".format(t)


@api_view()
def issledovaniye_data(request):
    pk = request.GET.get("pk")
    ignore_sample = request.GET.get("ignoreSample") == "true"
    i = directions.Issledovaniya.objects.get(pk=pk)
    sample = directions.TubesRegistration.objects.filter(issledovaniya=i, time_get__isnull=False).first()
    results = directions.Result.objects.filter(issledovaniye=i).exclude(fraction__fsli__isnull=True).exclude(fraction__fsli="").exclude(fraction__not_send_odli=True)
    if (
        (not ignore_sample and not sample)
        or (not results.exists() and not i.research.is_gistology and not i.research.is_paraclinic and not i.research.is_slave_hospital)
        or i.research.pk in REMD_EXCLUDE_RESEARCH
    ):
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
                if refs_list[0] == "-inf":
                    refs = [f"до {refs_list[1]}"]
                elif refs_list[1] == "inf":
                    refs = [f"от {refs_list[0]}"]
                elif refs_list[0] == refs_list[1]:
                    refs = [refs.const_orig]
                else:
                    refs = refs_list
        else:
            refs = [r.calc_normal(only_ref=True) or ""]

        norm = r.calc_normal()

        u = r.fraction.get_unit()
        if not REFERENCE_ODLI:
            refs = [""]
        results_data.append(
            {
                "pk": r.pk,
                "fsli": r.fraction.get_fsli_code(),
                "value": r.value.replace(",", "."),
                "units": r.get_units(),
                "unitCode": u.code if u else None,
                "ref": refs,
                "interpretation": "N" if norm and norm[0] == ResultRight.RESULT_MODE_NORMAL else "A",
                "ecpId": r.fraction.get_ecp_code(),
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
            "code": i.research.code.upper().replace("А", "A").replace("В", "B").replace("С", "C").strip(),
            "research": i.research.get_title(),
            "comments": i.lab_comment,
            "isGistology": i.research.is_gistology,
            "isParaclinic": i.research.is_paraclinic,
            "ecpResearchId": i.research.ecp_id,
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
    if i.research.is_extract:
        id_med_document_type = ID_MED_DOCUMENT_TYPE_IEMK_N3.get("is_extract")
    if i.research.is_form:
        id_med_document_type = i.research.n3_id_med_document_type
    return Response(
        {
            "ok": True,
            "pk": pk,
            "date": i.time_confirmation_local,
            "docConfirm": i.doc_confirmation_fio,
            "doctorData": doctor_data,
            "outcome": (i.outcome_illness.n3_id if i.outcome_illness else None) or "3",
            "visitPlace": (i.place.n3_id if i.place else None) or "1",
            "visitPurpose": (i.purpose.n3_id if i.purpose else None) or "2",
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
    ignore_sample = request.GET.get("ignoreSample") == "true"
    iss = (
        directions.Issledovaniya.objects.filter(pk__in=pks)
        .select_related("doc_confirmation", "research")
        .prefetch_related(Prefetch("result_set", queryset=(directions.Result.objects.filter(fraction__fsli__isnull=False).select_related("fraction"))))
        .prefetch_related(Prefetch("tubes", queryset=(directions.TubesRegistration.objects.filter(time_get__isnull=False))))
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
                    if refs[0] == "-inf":
                        refs = [f"до {refs[1]}"]
                    elif refs[1] == "inf":
                        refs = [f"от {refs[0]}"]
                    elif refs[0] == refs[1]:
                        refs = [refs[0]]
            else:
                refs = [r.calc_normal(only_ref=True) or ""]

            results_data.append(
                {
                    "pk": r.pk,
                    "issTitle": i.research.title,
                    "title": r.fraction.title,
                    "fsli": r.fraction.get_fsli_code(),
                    "value": r.value.replace(",", "."),
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


@api_view(["GET", "POST"])
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
    pks_to_set_ecp_fail = [x for x in keys if x] if t in (60023,) else []

    pks_to_set_emdr = [x for x in keys if x] if t in (60024,) else []
    pks_to_set_emdr_fail = [x for x in keys if x] if t in (60025,) else []

    pks_to_set_onkor = [x for x in keys if x] if t in (60026,) else []
    pks_to_set_onkor_fail = [x for x in keys if x] if t in (60027,) else []

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

            if str(k) in body and isinstance(body[k], dict) and body[str(k)]["id"]:
                d = directions.Napravleniya.objects.get(pk=k)
                d.n3_odli_id = body[str(k)]["id"]
                d.save(update_fields=["n3_odli_id"])

        for k in pks_to_set_vi_fail:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_vi:
            Log.log(key=k, type=t, body=body.get(k, {}))

            if str(k) in body and isinstance(body[k], dict) and body[str(k)]["id"]:
                d = directions.Napravleniya.objects.get(pk=k)
                d.vi_id = body[str(k)]["id"]
                d.save(update_fields=["vi_id"])

        for k in pks_to_set_iemk_fail:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_iemk:
            Log.log(key=k, type=t, body=body.get(k, {}))

            d = directions.Napravleniya.objects.get(pk=k)
            d.n3_iemk_ok = True
            d.save(update_fields=["n3_iemk_ok"])

        for k in pks_to_set_onkor_fail:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_onkor:
            Log.log(key=k, type=t, body=body.get(k, {}))

            d = directions.Napravleniya.objects.get(pk=k)
            d.onkor_message_id = body[str(k)]["messageId"]
            d.save(update_fields=["onkor_message_id"])

        for k in pks_to_set_emdr_fail:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_emdr:
            Log.log(key=k, type=t, body=body.get(k, {}))

        for k in pks_to_set_ecp_fail:
            Log.log(key=k, type=t, body=body.get(str(k), body.get(k, {})))

        for k in pks_to_set_ecp:
            Log.log(key=k, type=t, body=body.get(str(k), body.get(k, {})))

            d = directions.Napravleniya.objects.get(pk=k)
            d.ecp_ok = True
            d.save(update_fields=["ecp_ok"])

            iss: Issledovaniya
            for iss in Issledovaniya.objects.filter(napravleniye_id=k):
                if str(iss.pk) in body.get(k, {}):
                    if "ecpServiceId" in body[k][str(iss.pk)]:
                        iss.ecp_evn_id = str(body[k][str(iss.pk)]["ecpServiceId"] or "") or None
                        iss.save(update_fields=["ecp_evn_id"])

    return Response({"ok": True})


@api_view(["GET"])
def crie_status(request):
    pk = request.GET.get("direction")
    system_id = request.GET.get("system_id")
    status = request.GET.get("status") or "null"
    error = request.GET.get("error") or ""

    direction = directions.Napravleniya.objects.filter(pk=pk).first()

    if direction:
        if direction.need_resend_crie:
            direction.need_resend_crie = False
            direction.save(update_fields=["need_resend_crie"])
        order = CrieOrder.objects.filter(local_direction=direction).first()
        if not order:
            order = CrieOrder.objects.create(local_direction=direction, system_id=system_id, status=status, error=error)
            updated = ["system_id", "status", "error", "local_direction"]
        else:
            updated = []
            if order.system_id != system_id:
                order.system_id = system_id
                updated.append("system_id")

            if order.status != status:
                order.status = status
                updated.append("status")

            if order.error != error:
                order.error = error
                updated.append("error")

            if updated:
                order.save(update_fields=updated)
        if updated:
            Log.log(key=pk, type=60006, body={"updated": updated, "order_id": order.pk})
        return Response({"ok": True, "order": order.pk})
    return Response({"ok": False})


@api_view(["POST"])
def check_enp(request):
    enp, family, name, patronymic, bd, enp_mode, snils = data_parse(
        request.body,
        {"enp": str, "family": str, "name": str, "patronymic": str, "bd": str, "check_mode": str, "snils": str},
        {"check_mode": "tfoms", "bd": None, "name": None, "patronymic": None, "family": None, "enp": None, "ud": None, "snils": None},
    )
    if not enp:
        enp = ""
    enp = enp.replace(" ", "")

    logger.exception(f"enp_mode: {enp_mode}")

    if enp_mode == "l2-enp":
        tfoms_data = match_enp(enp)
        if tfoms_data:
            return Response({"ok": True, "patient_data": tfoms_data})
        else:
            params = json.dumps(
                {
                    "type": CardBase.objects.get(internal_type=True).pk,
                    "extendedSearch": True,
                    "form": {
                        "enp_n": enp,
                        "archive": False,
                    },
                    "limit": 1,
                }
            )
            request_obj = HttpRequest()
            request_obj._body = params
            request_obj.user = request.user
            data = patients_search_card(request_obj)
            results_json = json.loads(data.content.decode("utf-8"))
            if len(results_json["results"]) > 0:
                data_patient = results_json["results"][0]
                docs_patinet = data_patient["docs"]
                snils = ""
                for d in docs_patinet:
                    if d["type_title"] == "СНИЛС":
                        snils = d["number"]
                patient_data = {
                    "family": data_patient["family"],
                    "given": data_patient["name"],
                    "patronymic": data_patient["twoname"],
                    "gender": data_patient["sex"],
                    "birthdate": normalize_dots_date(data_patient["birthday"]),
                    "enp": enp,
                    "birthyear": f"{normalize_dots_date(data_patient['birthday']).split('-')[0]}",
                    "country": "RUS",
                    "polis_seria": "",
                    "polis_number": "",
                    "polis_type": "",
                    "polis_dognumber": "",
                    "polis_dogdate": "",
                    "polis_datebegin": "",
                    "snils": snils,
                    "status_code": "",
                    "status_name": "",
                    "unit_code": "",
                    "unit_name": "",
                    "unit_date": "",
                    "document_type": "",
                    "document_seria": "",
                    "document_number": "",
                    "insurer_code": "",
                    "insurer_name": "",
                    "address": "",
                    "codestreet": "",
                    "house": "",
                    "block": "",
                    "flat": "",
                    "idt": "",
                    "insurer_full_code": "",
                }
                return Response({"ok": True, "patient_data": patient_data, "1": results_json["results"]})
    elif enp_mode == "l2-enp-ud":
        tfoms_data = get_ud_info_by_enp(enp)
        if tfoms_data:
            return Response({"ok": True, "patient_data": tfoms_data})
    elif enp_mode == "l2-enp-dn":
        tfoms_data = get_dn_info_by_enp(enp)
        if tfoms_data:
            return Response({"ok": True, "patient_data": tfoms_data})
    elif enp_mode == "l2-snils":
        tfoms_data = match_patient_by_snils(snils)
        if tfoms_data:
            return Response({"ok": True, "patient_data": tfoms_data})
        else:
            params = json.dumps(
                {
                    "type": CardBase.objects.get(internal_type=True).pk,
                    "extendedSearch": True,
                    "form": {
                        "snils": snils,
                        "archive": False,
                    },
                    "limit": 1,
                }
            )
            request_obj = HttpRequest()
            request_obj._body = params
            request_obj.user = request.user
            data = patients_search_card(request_obj)
            results_json = json.loads(data.content.decode("utf-8"))
            if len(results_json["results"]) > 0:
                data_patient = results_json["results"][0]
                docs_patinet = data_patient["docs"]
                snils = ""
                for d in docs_patinet:
                    if d["type_title"] == "СНИЛС":
                        snils = d["number"]
                patient_data = {
                    "card": data_patient["pk"],
                    "family": data_patient["family"],
                    "given": data_patient["name"],
                    "patronymic": data_patient["twoname"],
                    "gender": data_patient["sex"],
                    "birthdate": normalize_dots_date(data_patient["birthday"]),
                    "enp": enp,
                    "birthyear": f"{normalize_dots_date(data_patient['birthday']).split('-')[0]}",
                    "country": "RUS",
                    "polis_seria": "",
                    "polis_number": "",
                    "polis_type": "",
                    "polis_dognumber": "",
                    "polis_dogdate": "",
                    "polis_datebegin": "",
                    "snils": snils,
                    "status_code": "",
                    "status_name": "",
                    "unit_code": "",
                    "unit_name": "",
                    "unit_date": "",
                    "document_type": "",
                    "document_seria": "",
                    "document_number": "",
                    "insurer_code": "",
                    "insurer_name": "",
                    "address": "",
                    "codestreet": "",
                    "house": "",
                    "block": "",
                    "flat": "",
                    "idt": "",
                    "insurer_full_code": "",
                }
                return Response({"ok": True, "patient_data": patient_data})
    elif enp_mode == "l2-enp-full":
        patronymic = patronymic if patronymic != "None" else None
        logger.exception(f"data: {(family, name, patronymic, bd)}")
        tfoms_data = match_patient(family, name, patronymic, bd)

        if tfoms_data:
            return Response({"ok": True, "list": tfoms_data})
    elif enp_mode == "tfoms":
        tfoms_data = match_enp(enp)

        logger.exception(f"tfoms data: {json.dumps(tfoms_data)}")

        if tfoms_data:
            bdate = tfoms_data.get("birthdate", "").split(" ")[0]
            if normalize_date(bd) == normalize_date(bdate):
                return Response({"ok": True, "patient_data": tfoms_data})
    elif enp_mode == "rmis":
        logger.exception(f"enp: {enp}")
        c = Client(modules=["patients"])
        card = c.patients.get_l2_card_by_enp(enp)
        if card:
            logger.exception(f"card: {card}")
            i: Individual = card.individual
            bd_orig = f"{i.birthday:%Y-%m-%d}"
            logger.exception(f"{bd_orig} == {bd}")
            if bd_orig == bd:
                return Response(
                    {
                        "ok": True,
                        "patient_data": {
                            "rmis_id": card.individual.get_rmis_uid_fast(),
                        },
                    }
                )
    elif enp_mode == "local":
        logger.exception(f"enp: {enp}")
        card = Card.objects.filter(base__internal_type=True, is_archive=False, carddocusage__document__number=enp, carddocusage__document__document_type__title="Полис ОМС").first()

        if card:
            logger.exception(f"card: {card}")
            i: Individual = card.individual
            bd_orig = f"{i.birthday:%Y-%m-%d}"
            logger.exception(f"{bd_orig} == {bd}")
            if bd_orig == bd:
                return Response(
                    {
                        "ok": True,
                        "patient_data": {
                            "rmis_id": card.individual.get_rmis_uid_fast(),
                        },
                    }
                )

    return Response({"ok": False, "message": "Неверные данные или нет прикрепления к поликлинике"})


@api_view(["POST"])
def patient_results_covid19(request):
    return Response({"ok": False})
    days = 15
    results = []
    p_enp = data_parse(request.body, {"enp": str}, {"enp": ""})[0]
    if p_enp:
        logger.exception(f"patient_results_covid19 by enp: {p_enp}")
        card = Card.objects.filter(
            base__internal_type=True, is_archive=False, carddocusage__document__number=str(p_enp).replace(" ", ""), carddocusage__document__document_type__title="Полис ОМС"
        ).first()
        logger.exception(f"patient_results_covid19 by enp [CARD]: {card}")
        if card:
            date_end = current_time()
            date_start = date_end + relativedelta(days=-days)
            date_end = date_end + relativedelta(days=1)
            results_covid = last_results_researches_by_time_ago(card.pk, COVID_RESEARCHES_PK, date_start, date_end)
            logger.exception(f"patient_results_covid19 by enp params: {(card.pk, COVID_RESEARCHES_PK, date_start, date_end)}")
            logger.exception(f"patient_results_covid19 by enp results count: {len(results_covid)}")
            for i in results_covid:
                results.append({"date": i.confirm, "result": i.value})
            if len(results) > 0:
                return Response({"ok": True, "results": results})

    rmis_id = data_parse(request.body, {"rmis_id": str}, {"rmis_id": ""})[0]

    results = []

    if rmis_id:
        for i in range(3):
            results = []

            logger.exception(f"patient_results_covid19 by rmis id, try {i + 1}/3: {rmis_id}")

            try:
                c = Client(modules=["directions", "rendered_services"])

                now = current_time().date()

                variants = ["РНК вируса SARS-CоV2 не обнаружена", "РНК вируса SARS-CоV2 обнаружена"]

                for i in range(days):
                    date = now - datetime.timedelta(days=i)
                    rendered_services = c.rendered_services.client.searchServiceRend(patientUid=rmis_id, dateFrom=date)
                    for rs in rendered_services[:5]:
                        protocol = c.directions.get_protocol(rs)
                        for v in variants:
                            if v in protocol:
                                results.append({"date": date.strftime("%d.%m.%Y"), "result": v})
                                break
                break
            except Exception as e:
                logger.exception(e)
            time.sleep(2)

    return Response({"ok": True, "results": results})


@api_view(["POST"])
def external_doc_call_create(request):
    data = json.loads(request.body)
    org_id = data.get("org_id")
    patient_data = data.get("patient_data")
    form = data.get("form")
    idp = patient_data.get("idp")
    enp = patient_data.get("enp")
    comment = form.get("comment")
    purpose = form.get("purpose")
    email = form.get("email")
    external_num = form.get("external_num")
    is_main_external = form.get("is_main_external")

    if email == "undefined":
        email = None

    logger.exception(f"external_doc_call_create: {org_id} {json.dumps(patient_data)} {json.dumps(form)} {idp} {enp} {comment} {purpose} {email} {external_num}")

    Individual.import_from_tfoms(patient_data)
    individuals = Individual.objects.filter(Q(tfoms_enp=enp or "###$fakeenp$###") | Q(tfoms_idp=idp or "###$fakeidp$###"))

    individual_obj = individuals.first()
    if not individual_obj:
        return JsonResponse({"ok": False, "number": None})

    card = Card.objects.filter(individual=individual_obj, base__internal_type=True).first()
    research = Researches.objects.filter(title="Обращение пациента").first()
    hospital = Hospitals.objects.filter(code_tfoms=org_id).first()

    if not card or not research or not hospital:
        return JsonResponse({"ok": False, "number": None})

    date = current_time()

    count = DoctorCall.objects.filter(client=card, is_external=True, exec_at__date=date.date()).count()
    if count >= MAX_DOC_CALL_EXTERNAL_REQUESTS_PER_DAY:
        logger.exception(f"TOO MANY REQUESTS PER DAY: already have {count} calls at {date:%d.%m.%Y}")
        return JsonResponse({"ok": False, "number": None, "tooManyRequests": True})

    research_pk = research.pk

    doc_call = DoctorCall.doctor_call_save(
        {
            "card": card,
            "research": research_pk,
            "address": card.main_address,
            "district": -1,
            "date": date,
            "comment": comment,
            "phone": form.get("phone"),
            "doc": -1,
            "purpose": int(purpose),
            "hospital": hospital.pk,
            "external": True,
            "email": email,
            "external_num": external_num,
            "is_main_external": bool(is_main_external),
        }
    )
    if is_main_external:
        doc_call.external_num = doc_call.num
    elif SettingManager.l2("send_doc_calls"):
        doc_call.external_num = f"{org_id}{doc_call.pk}"
    doc_call.save()

    return Response({"ok": True, "number": doc_call.external_num})


@api_view(["POST"])
def external_doc_call_update_status(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)

    external_num = body.get("externalNum")
    status = body.get("status")
    org = body.get("org")
    code_tfoms = org.get("codeTFOMS")
    oid_org = org.get("oid")

    if not external_num:
        return Response({"ok": False, "message": "externalNum не указан"})

    if not status:
        return Response({"ok": False, "message": "status не указан"})

    if not code_tfoms and not oid_org:
        return Response({"ok": False, "message": "Должно быть указано хотя бы одно значение из org.codeTFOMS или org.oid"})

    if code_tfoms:
        hospital = Hospitals.objects.filter(code_tfoms=code_tfoms).first()
    else:
        hospital = Hospitals.objects.filter(oid=oid_org).first()

    if not hospital:
        return Response({"ok": False, "message": "Организация не найдена"})

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return Response({"ok": False, "message": "Нет доступа в переданную организацию"})

    if not hospital:
        return Response({"ok": False, "message": "Организация не найдена"})

    status = str(status)
    if not status.isdigit():
        return Response({"ok": False, "message": "Некорректный status"})

    status = int(status)
    if status not in [x[0] for x in DoctorCall.STATUS]:
        return Response({"ok": False, "message": "Некорректный status"})

    num = str(external_num)
    if not num.startswith("XR"):
        return Response({"ok": False, "message": "Некорректный externalNum"})

    num = num.replace("XR", "")
    if not num.isdigit():
        return Response({"ok": False, "message": "Некорректный externalNum"})

    call: DoctorCall = DoctorCall.objects.filter(pk=num).first()
    if not call:
        return Response({"ok": False, "message": f"Заявка с номером {num} не найдена"})

    call.status = status
    call.save(update_fields=["status"])
    return Response({"ok": True})


@api_view(["POST"])
def external_doc_call_send(request):
    data = json.loads(request.body)
    patient_data = data.get("patient_data")
    form = data.get("form")
    enp = patient_data.get("enp")
    address = patient_data.get("address")
    comment = form.get("comment")
    purpose = form.get("purpose_id")
    email = form.get("email")
    external_num = form.get("num")

    logger.exception(f"external_doc_call_send: {json.dumps(patient_data)} {json.dumps(form)} {enp} {comment} {purpose} {email} {external_num}")

    individuals = Individual.objects.filter(tfoms_enp=enp)
    if not individuals.exists():
        individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title="Полис ОМС") | Q(document__document_type__title="ЕНП"))
    if not individuals.exists():
        tfoms_data = match_enp(enp)
        if not tfoms_data:
            return Response({"ok": False, "message": "Неверные данные полиса, в базе ТФОМС нет такого пациента"})
        Individual.import_from_tfoms(tfoms_data)
        individuals = Individual.objects.filter(tfoms_enp=enp)

    individual = individuals if isinstance(individuals, Individual) else individuals.first()
    if not individual:
        return Response({"ok": False, "message": "Физлицо не найдено"})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    research = Researches.objects.filter(title="Обращение пациента").first()
    hospital = Hospitals.get_default_hospital()

    if not card or not research or not hospital:
        return JsonResponse({"ok": False, "number": None})

    research_pk = research.pk

    doc_call = DoctorCall.doctor_call_save(
        {
            "card": card,
            "research": research_pk,
            "address": address,
            "district": -1,
            "date": current_time(),
            "comment": comment,
            "phone": form.get("phone"),
            "doc": -1,
            "purpose": int(purpose),
            "hospital": hospital.pk,
            "external": True,
            "email": email,
            "external_num": external_num,
            "is_main_external": False,
        }
    )

    return Response({"ok": True, "number": doc_call.num})


@api_view(["POST"])
def set_core_id(request):
    data = json.loads(request.body)
    pk = data.get("pk")
    core_id = data.get("coreId")
    n = directions.Napravleniya.objects.get(pk=pk)
    n.core_id = core_id
    n.save(update_fields=["core_id"])
    return Response({"ok": True})


class InvalidData(Exception):
    pass


def limit_str(s: str, limit=500):
    return str(s)[:limit]


@api_view(["POST"])
def external_research_create(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)

    old_pk = body.get("oldId")
    org = body.get("org", {})
    code_tfoms = org.get("codeTFOMS")
    oid_org = org.get("oid")

    if not code_tfoms and not oid_org:
        return Response({"ok": False, "message": "Должно быть указано хотя бы одно значение из org.codeTFOMS или org.oid"})

    if code_tfoms:
        hospital = Hospitals.objects.filter(code_tfoms=code_tfoms).first()
    else:
        hospital = Hospitals.objects.filter(oid=oid_org).first()

    if not hospital:
        return Response({"ok": False, "message": "Организация не найдена"})

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return Response({"ok": False, "message": "Нет доступа в переданную организацию"})

    initiator = org.get("initiator") or {}
    title_org_initiator = initiator.get("title")
    if title_org_initiator is not None:
        title_org_initiator = str(title_org_initiator)[:254]

    ogrn_org_initiator = initiator.get("ogrn")
    if ogrn_org_initiator is not None:
        ogrn_org_initiator = str(ogrn_org_initiator)

    if not title_org_initiator:
        title_org_initiator = None

    if not ogrn_org_initiator:
        ogrn_org_initiator = None

    if not title_org_initiator and ogrn_org_initiator:
        return Response({"ok": False, "message": "org.initiator: при передаче ogrn поле title обязательно"})

    if title_org_initiator and not ogrn_org_initiator:
        return Response({"ok": False, "message": "org.initiator: при передаче title поле ogrn обязательно"})

    if ogrn_org_initiator and not ogrn_org_initiator.isdigit():
        return Response({"ok": False, "message": "org.initiator.ogrn: в значении возможны только числа"})

    if ogrn_org_initiator and len(ogrn_org_initiator) != 13:
        return Response({"ok": False, "message": "org.initiator.ogrn: длина должна быть 13"})

    if ogrn_org_initiator and not petrovna.validate_ogrn(ogrn_org_initiator):
        return Response({"ok": False, "message": "org.initiator.ogrn: не прошёл валидацию"})

    patient = body.get("patient", {})

    enp = (patient.get("enp") or "").replace(" ", "")

    if enp and (len(enp) != 16 or not enp.isdigit()):
        return Response({"ok": False, "message": "Неверные данные полиса, должно быть 16 чисел"})

    passport_serial = (patient.get("passportSerial") or "").replace(" ", "")
    passport_number = (patient.get("passportNumber") or "").replace(" ", "")

    snils = (patient.get("snils") or "").replace(" ", "").replace("-", "")

    if not enp and (not passport_serial or not passport_number) and not snils:
        return Response({"ok": False, "message": "При пустом patient.enp должно быть передано patient.snils или patient.passportSerial+patient.passportNumber"})

    if passport_serial and len(passport_serial) != 4:
        return Response({"ok": False, "message": "Длина patient.passportSerial должна быть 4"})

    if passport_serial and not passport_serial.isdigit():
        return Response({"ok": False, "message": "patient.passportSerial должен содержать только числа"})

    if passport_number and len(passport_number) != 6:
        return Response({"ok": False, "message": "Длина patient.passportNumber должна быть 6"})

    if passport_number and not passport_number.isdigit():
        return Response({"ok": False, "message": "patient.passportNumber должен содержать только числа"})

    if snils and not petrovna.validate_snils(snils):
        return Response({"ok": False, "message": "patient.snils: не прошёл валидацию"})

    individual_data = patient.get("individual") or {}

    if not enp and not individual_data:
        return Response({"ok": False, "message": "При пустом patient.enp должно быть передано поле patient.individual"})

    lastname = str(individual_data.get("lastname") or "")
    firstname = str(individual_data.get("firstname") or "")
    patronymic = str(individual_data.get("patronymic") or "")
    birthdate = str(individual_data.get("birthdate") or "")
    sex = str(individual_data.get("sex") or "").lower()

    individual = None

    if lastname and not firstname:
        return Response({"ok": False, "message": "При передаче lastname должен быть передан и firstname"})

    if firstname and not lastname:
        return Response({"ok": False, "message": "При передаче firstname должен быть передан и lastname"})

    if firstname and lastname and not birthdate:
        return Response({"ok": False, "message": "При передаче firstname и lastname должно быть передано поле birthdate"})

    if birthdate and (not re.fullmatch(r"\d{4}-\d\d-\d\d", birthdate) or birthdate[0] not in ["1", "2"]):
        return Response({"ok": False, "message": "birthdate должно соответствовать формату YYYY-MM-DD"})

    if birthdate and sex not in ["м", "ж"]:
        return Response({"ok": False, "message": 'individual.sex должно быть "м" или "ж"'})

    individual_status = "unknown"

    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        if not individuals.exists():
            individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title="Полис ОМС") | Q(document__document_type__title="ЕНП"))
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
        individuals = Individual.objects.filter(document__serial=passport_serial, document__number=passport_number, document__document_type__title="Паспорт гражданина РФ")
        individual = individuals.first()
        individual_status = "passport"

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title="СНИЛС")
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
        return Response({"ok": False, "message": "Физлицо не найдено"})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    if not card:
        card = Card.add_l2_card(individual)

    if not card:
        return Response({"ok": False, "message": "Карта не найдена"})

    financing_source_title = body.get("financingSource", "")

    financing_source = directions.IstochnikiFinansirovaniya.objects.filter(title__iexact=financing_source_title, base__internal_type=True).first()

    if not financing_source:
        return Response({"ok": False, "message": "Некорректный источник финансирования"})

    results = body.get("results")
    if not results or not isinstance(results, list):
        return Response({"ok": False, "message": "Некорректное значение results"})

    results = results[:40]

    message = None

    id_in_hospital = body.get("internalId", "")

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
                    raise InvalidData(f"Исследование с кодом {code_research} не найдено")

                if research_to_filter[code_research]:
                    raise InvalidData(f"Исследование с кодом {code_research} отправлено повторно в одном направлении")

                tests = r.get("tests")
                if not tests or not isinstance(tests, list):
                    raise InvalidData(f"Исследование {code_research} содержит некорректное поле tests")

                comments = str(r.get("comments", "") or "") or None

                time_confirmation = r.get("dateTimeConfirm")
                if not time_confirmation or not valid_date(time_confirmation):
                    raise InvalidData(f"{code_research}: содержит некорректное поле dateTimeConfirm. Оно должно быть заполнено и соответствовать шаблону YYYY-MM-DD HH:MM")

                time_get = str(r.get("dateTimeGet", "") or "") or None
                if time_get and not valid_date(time_confirmation):
                    raise InvalidData(f"{code_research}: содержит некорректное поле dateTimeGet. Оно должно быть пустым или соответствовать шаблону YYYY-MM-DD HH:MM")

                time_receive = str(r.get("dateTimeReceive", "") or "") or None
                if time_receive and not valid_date(time_confirmation):
                    raise InvalidData(f"{code_research}: содержит некорректное поле dateTimeReceive. Оно должно быть пустым или соответствовать шаблону YYYY-MM-DD HH:MM")

                doc_confirm = str(r.get("docConfirm", "") or "") or None

                if doc_confirm is not None:
                    doc_confirm = limit_str(doc_confirm, 64)

                iss = directions.Issledovaniya.objects.create(
                    napravleniye=direction,
                    research=research,
                    lab_comment=comments,
                    time_confirmation=time_confirmation,
                    time_save=timezone.now(),
                    doc_confirmation_string=doc_confirm or f"Врач {hospital.short_title or hospital.title}",
                )
                tube = Tubes.objects.filter(title="Универсальная пробирка").first()
                if not tube:
                    tube = Tubes.objects.create(title="Универсальная пробирка", color="#049372")

                ft = ReleationsFT.objects.filter(tube=tube).first()
                if not ft:
                    ft = ReleationsFT.objects.create(tube=tube)

                with transaction.atomic():
                    try:
                        generator_pk = directions.TubesRegistration.get_tube_number_generator_pk(hospital)
                        generator = directions.NumberGenerator.objects.select_for_update().get(pk=generator_pk)
                        number = generator.get_next_value()
                    except directions.NoGenerator as e:
                        return status_response(False, str(e))
                    except directions.GeneratorValuesAreOver as e:
                        return status_response(False, str(e))
                    tr = iss.tubes.create(type=ft, number=number)
                    tr.time_get = time_get
                    tr.time_recive = time_receive
                    tr.save(update_fields=["time_get", "time_recive"])

                tests_to_filter = defaultdict(lambda: False)

                for t in tests[:30]:
                    fsli_code = t.get("idFsli", "unknown")
                    fraction = Fractions.objects.filter(fsli=fsli_code).first()
                    if not fraction:
                        raise InvalidData(f"В исследовании {code_research} не найден тест {fsli_code}")

                    if tests_to_filter[code_research]:
                        raise InvalidData(f"Тест с кодом {fsli_code} отправлен повторно в одном направлении в {code_research}")

                    value = limit_str(t.get("valueString", "") or "", 500)
                    units = limit_str(str(t.get("units", "") or ""), 50)

                    reference_value = t.get("referenceValue") or None
                    reference_range = t.get("referenceRange") or None

                    if reference_value and not isinstance(reference_value, str):
                        raise InvalidData(f"{code_research} -> {fsli_code}: поле referenceValue должно быть строкой или null")
                    if reference_range and not isinstance(reference_range, dict):
                        raise InvalidData(f"{code_research} -> {fsli_code}: поле referenceRange должно быть объектом {{low, high}} или null")

                    if reference_range and ("low" not in reference_range or "high" not in reference_range):
                        raise InvalidData(f"{code_research} -> {fsli_code}: поле referenceRange должно быть объектом с полями {{low, high}} или null")

                    ref_str = reference_value

                    if not ref_str and reference_range:
                        ref_str = f"{reference_range['low']} – {reference_range['high']}"

                    if ref_str:
                        ref_str = limit_str(ref_str.replace('"', "'"), 120)
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
            return Response({"ok": True, "id": str(direction.pk)})

    except InvalidData as e:
        logger.exception(e)
        message = str(e)
    except Exception as e:
        logger.exception(e)
        message = "Серверная ошибка"

    return Response({"ok": False, "message": message})


@api_view(["POST"])
def external_direction_create(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)

    org = body.get("org", {})
    code_tfoms = org.get("codeTFOMS")
    oid_org = org.get("oid")

    if not code_tfoms and not oid_org:
        return Response({"ok": False, "message": "Должно быть указано хотя бы одно значение из org.codeTFOMS или org.oid"})

    if code_tfoms:
        hospital = Hospitals.objects.filter(code_tfoms=code_tfoms).first()
    else:
        hospital = Hospitals.objects.filter(oid=oid_org).first()

    if not hospital:
        return Response({"ok": False, "message": "Организация не найдена"})

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return Response({"ok": False, "message": "Нет доступа в переданную организацию"})

    is_exclude_contorl_documnets = False
    if hospital.pk in HOSPITAL_PKS_NOT_CONTROL_DOCUMENT_EXTERNAL_CREATE_DIRECTION:
        is_exclude_contorl_documnets = True

    patient = body.get("patient", {})

    enp = (patient.get("enp") or "").replace(" ", "")

    if enp and (len(enp) != 16 or not enp.isdigit()):
        return Response({"ok": False, "message": "Неверные данные полиса, должно быть 16 чисел"})

    snils = (patient.get("snils") or "").replace(" ", "").replace("-", "")

    if not enp and not snils and not is_exclude_contorl_documnets:
        return Response({"ok": False, "message": "При пустом patient.enp должно быть передано patient.snils или patient.passportSerial+patient.passportNumber"})

    if snils and not petrovna.validate_snils(snils):
        return Response({"ok": False, "message": "patient.snils: не прошёл валидацию"})

    lastname = str(patient.get("lastName") or "")
    firstname = str(patient.get("firstName") or "")
    patronymic = str(patient.get("patronymicName") or "")
    birthdate = str(patient.get("birthDate") or "")
    sex = patient.get("sex") or ""
    if sex == 1:
        sex = "м"
    else:
        sex = "ж"

    if not enp and not (lastname and firstname and birthdate and birthdate):
        return Response({"ok": False, "message": "При пустом patient.enp должно быть передано поле patient.individual"})

    if lastname and not firstname:
        return Response({"ok": False, "message": "При передаче lastname должен быть передан и firstname"})

    if firstname and not lastname:
        return Response({"ok": False, "message": "При передаче firstname должен быть передан и lastname"})

    if firstname and lastname and not birthdate:
        return Response({"ok": False, "message": "При передаче firstname и lastname должно быть передано поле birthdate"})

    if birthdate and (not re.fullmatch(r"\d{4}-\d\d-\d\d", birthdate) or birthdate[0] not in ["1", "2"]):
        return Response({"ok": False, "message": "birthdate должно соответствовать формату YYYY-MM-DD"})

    if birthdate and sex not in ["м", "ж"]:
        return Response({"ok": False, "message": 'individual.sex должно быть "м" или "ж"'})

    individual = None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        if not individuals.exists():
            individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title="Полис ОМС") | Q(document__document_type__title="ЕНП"))
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
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title="СНИЛС")
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
        return Response({"ok": False, "message": "Физлицо не найдено"})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    if not card:
        card = Card.add_l2_card(individual)

    if not card:
        return Response({"ok": False, "message": "Карта не найдена"})

    financing_source_title = body.get("financingSource", "")
    if financing_source_title.lower() not in ["омс", "бюджет", "платно"]:
        return Response({"ok": False, "message": "Некорректный источник финансирования"})

    financing_source = directions.IstochnikiFinansirovaniya.objects.filter(title__iexact=financing_source_title, base__internal_type=True).first()
    financing_category_code = body.get("financingCategory", "")
    price_category = PriceCategory.objects.filter(title__startswith=financing_category_code).first()

    if not financing_source:
        return Response({"ok": False, "message": "Некорректный источник финансирования"})

    message = None

    id_in_hospital = body.get("internalId", "")
    if id_in_hospital is not None:
        id_in_hospital = limit_str(id_in_hospital, 15)

    department = body.get("department", "")
    additiona_info = body.get("additionalInfo", "")
    last_result_data = body.get("lastResultData", "")

    diag_text = body.get("diagText", "")  # обязательно
    if not diag_text:
        return Response({"ok": False, "message": "Диагноз описание не заполнено"})

    diag_mkb10 = body.get("diagMKB10", "")  # обязательно
    if not diag_mkb10:
        return Response({"ok": False, "message": "Диагноз по МКБ10 не заполнен (не верно)"})
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
    method_obtain_material = body.get("methodObtainMaterial", "")  # обязательно code из НСИ 1.2.643.5.1.13.13.99.2.33"
    if not method_obtain_material or method_obtain_material not in [1, 2, 3, 4, 5, 6, 7]:
        return Response({"ok": False, "message": "Способо забора не верно заполнено"})

    resident_code = patient.get("residentCode", "")  # обязательно code из НСИ 1.2.643.5.1.13.13.11.1042"
    if not resident_code or resident_code not in [1, 2]:
        return Response({"ok": False, "message": "Не указан вид жительства"})
    if resident_code == 1:
        resident_data = f'{open_skob}"code": "1", "title": "Город"{close_skob}'
    else:
        resident_data = f'{open_skob}"code": "2", "title": "Село"{close_skob}'

    solution10 = body.get("solution10", "")  # обязательно
    if not solution10 or solution10 not in ["true", "false"]:
        return Response({"ok": False, "message": "Не указано помещен в 10% раствор"})

    doctor_fio = body.get("doctorFio", "")  # обязательно
    if not doctor_fio:
        return Response({"ok": False, "message": "Не указан врач производивший забор материала"})
    material_mark = body.get("materialMark", "")
    numbers_vial = []
    for k in material_mark:
        result_check = check_valid_material_mark(k, numbers_vial)
        if not result_check:
            return Response({"ok": False, "message": "Не верная маркировка материала"})
        numbers_vial = result_check
    if len(numbers_vial) != sorted(numbers_vial)[-1]:
        return Response({"ok": False, "message": "Не верная маркировка флаконов (порядок 1,2,3,4...)"})

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
                raise InvalidData("Содержит некорректное поле dateTimeGet. Оно должно соответствовать шаблону YYYY-MM-DD HH:MM")

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
            return Response({"ok": True, "id": str(direction.pk)})

    except InvalidData as e:
        logger.exception(e)
        message = str(e)
    except Exception as e:
        logger.exception(e)
        message = "Серверная ошибка"

    return Response({"ok": False, "message": message})


@api_view(["POST"])
def get_directions(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    oid_org = body.get(("oid") or "")
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, "message": check_result["message"]})
    else:
        hospital = check_result["hospital"]
        create_from = body.get(("createFrom") or "")
        create_to = body.get(("createTo") or "")
        directions_data = Napravleniya.objects.values_list("pk", flat=True).filter(hospital=hospital, data_sozdaniya__gte=create_from, data_sozdaniya__lte=create_to)
        return Response({"ok": True, "data": directions_data})


@api_view(["POST"])
def get_direction_data_by_num(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})
    body = json.loads(request.body)
    oid_org = body.get(("oid") or "")
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, "message": check_result["message"]})

    pk = int(body.get(("directionNum") or ""))
    data_result = get_data_direction_with_param(pk)
    if not data_result:
        return Response({"ok": False})
    return Response({"ok": True, "data": data_result})


@api_view(["POST"])
def get_direction_data_by_period(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    oid_org = body.get(("oid") or "")
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, "message": check_result["message"]})
    hospital = check_result["hospital"]
    create_from = body.get(("createFrom") or "")
    create_to = body.get(("createTo") or "")
    dot_format_create_from = normalize_date(create_from.split(" ")[0])
    dot_format_create_to = normalize_date(create_to.split(" ")[0])
    date_start, date_end = try_parse_range(dot_format_create_from, dot_format_create_to)
    if date_start and date_end:
        delta = date_end - date_start
        if abs(delta.days) > 2:
            return Response({"ok": False, "message": "Период между датами не более 48 часов"})

    directions_data = Napravleniya.objects.values_list("pk", flat=True).filter(hospital=hospital, data_sozdaniya__gte=create_from, data_sozdaniya__lte=create_to)
    result = []
    for direction_number in directions_data:
        data_result = get_data_direction_with_param(direction_number)
        if not data_result:
            continue
        result.append(data_result)
    return Response({"ok": True, "data": result})


@api_view(["POST"])
def external_get_pdf_result(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    oid_org = body.get(("oid") or "")
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, "message": check_result["message"]})
    hospital = check_result["hospital"]
    pk = int(body.get(("directionNum") or ""))
    direction = directions.Napravleniya.objects.filter(hospital=hospital, pk=pk).first()
    if not direction:
        return Response({"ok": False, "message": "Номер направления не принадлежит организации"})
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


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def eds_get_user_data(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    token = token.replace("Bearer ", "")

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
    p_enp_re = re.compile(r"^[0-9]{16}$")
    p_enp = bool(re.search(p_enp_re, card.get_data_individual()["oms"]["polis_num"]))
    insurer_full_code = card.get_data_individual()["insurer_full_code"]
    if not insurer_full_code:
        pass
        # card.individual.sync_with_tfoms()
    insurer_full_code = card.get_data_individual()["insurer_full_code"]
    smo_title = ""
    smo_id = ""
    if insurer_full_code:
        smo = NSI.get("1.2.643.5.1.13.13.99.2.183_smo_code", {}).get("values", {})
        smo_title = smo.get(insurer_full_code, "")
        smo_ids = NSI.get("1.2.643.5.1.13.13.99.2.183_smo_id", {}).get("values", {})
        smo_id = smo_ids.get(insurer_full_code, "")

    if SettingManager.get("eds_control_enp", default="true", default_type="b") and not p_enp:
        return {}
    else:
        return {
            "title": n.get_eds_title(),
            "generatorName": n.get_eds_generator(),
            "rawResponse": True,
            "data": {
                "oidMo": data["oidMo"],
                "document": data,
                "patient": {
                    "id": card.pk,
                    "snils": data_individual["snils"],
                    "name": {"family": ind.family, "name": ind.name, "patronymic": ind.patronymic},
                    "gender": ind.sex.lower(),
                    "gender_code": 2 if ind.sex.lower() == "ж" else 1,
                    "gender_title": "Женский" if ind.sex.lower() == "ж" else "Мужской",
                    "birthdate": ind.birthday.strftime("%Y%m%d"),
                    "birthdate_dots": ind.birthday.strftime("%d.%m.%Y"),
                    "oms": {"number": card.get_data_individual()["oms"]["polis_num"], "issueOrgName": smo_title, "issueOrgCode": insurer_full_code, "smoId": smo_id},
                    "address": data_individual["main_address"],
                },
                "organization": data["organization"],
            },
        }


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def eds_get_cda_data(request):
    token = request.headers.get("Authorization").split(" ")[1]
    token_obj = Application.objects.filter(key=token).first()
    if not token_obj.unlimited_access:
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    pk = body.get("pk")
    is_extract = body.get("isExtract") == "1"
    if is_extract:
        result = hosp_get_data_direction(pk, site_type=7, type_service='None', level=2)
        if len(result) > 0:
            pk = result[0].get("direction")
    return Response(get_cda_data(pk))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def external_check_result(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    token = token.replace("Bearer ", "")
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

    if "qr_check_result" not in external_service.rights:
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


@api_view(["POST"])
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
                        "id": card.number,
                        "snils": card.get_data_individual()["snils"],
                        "name": {"family": ind.family, "name": ind.name, "patronymic": ind.patronymic},
                        "gender": ind.sex.lower(),
                        "birthdate": ind.birthday.strftime("%Y%m%d"),
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
                        "id": card.number,
                        "snils": card.get_data_individual()["snils"],
                        "name": {"family": ind.family, "name": ind.name, "patronymic": ind.patronymic},
                        "gender": ind.sex.lower(),
                        "birthdate": ind.birthday.strftime("%Y%m%d"),
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
                        "id": card.number,
                        "snils": card.get_data_individual()["snils"],
                        "name": {"family": ind.family, "name": ind.name, "patronymic": ind.patronymic},
                        "gender": ind.sex.lower(),
                        "birthdate": ind.birthday.strftime("%Y%m%d"),
                    },
                    "organization": data["organization"],
                },
            }
        )

    return Response({})


@api_view(["POST", "GET"])
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


@api_view(["GET"])
def mkb10(request):
    return Response({"rows": mkb10_dict(request, True)})


@api_view(["POST", "PUT"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@can_use_schedule_only
def hosp_record(request):
    files = []
    if request.method == "PUT":
        for kf in request.data:
            if kf != "document":
                files.append(request.data[kf])
        form = request.data["document"]
    else:
        form = request.body

    data = data_parse(
        form,
        {
            "snils": "str_strip",
            "enp": "str_strip",
            "family": "str_strip",
            "name": "str_strip",
            "patronymic": "str_strip",
            "sex": "str_strip",
            "birthdate": "str_strip",
            "comment": "str_strip",
            "date": "str_strip",
            "service": int,
            "phone": "str_strip",
            "diagnosis": "str_strip",
        },
    )

    if len(files) > LK_FILE_COUNT:
        return Response({"ok": False, "message": "Слишком много файлов"})

    for f in files:
        if f.size > LK_FILE_SIZE_BYTES:
            return Response({"ok": False, "message": "Файл слишком большой"})
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

    if sex == "m":
        sex = "м"

    if sex == "f":
        sex = "ж"

    snils = "".join(ch for ch in snils if ch.isdigit())

    individual = None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        individual = individuals.first()

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title="СНИЛС")
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
        return Response({"ok": False, "message": "Физлицо не найдено"})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    if not card:
        card = Card.add_l2_card(individual)

    if not card:
        return Response({"ok": False, "message": "Карта не найдена"})

    if SCHEDULE_AGE_LIMIT_LTE:
        age = card.individual.age()
        if age > SCHEDULE_AGE_LIMIT_LTE:
            return Response({"ok": False, "message": f"Пациент должен быть не старше {SCHEDULE_AGE_LIMIT_LTE} лет"})

    hospital_research: Researches = Researches.objects.filter(pk=service, is_hospital=True).first()

    if not hospital_research:
        return Response({"ok": False, "message": "Услуга не найдена"})

    has_free_slots = check_available_hospital_slot_before_save(hospital_research.pk, None, date)
    if not has_free_slots:
        return JsonResponse({"ok": False, "message": "Нет свободных слотов"})

    hosp_department_id = hospital_research.podrazdeleniye.pk
    with transaction.atomic():
        plan_pk = PlanHospitalization.plan_hospitalization_save(
            {
                "card": card,
                "research": hospital_research.pk,
                "date": date,
                "comment": comment[:256],
                "phone": phone,
                "action": 0,
                "hospital_department_id": hosp_department_id,
                "diagnos": diagnosis,
                "files": files,
            },
            None,
        )
        for f in files:
            plan_files: PlanHospitalizationFiles = PlanHospitalizationFiles(plan_id=plan_pk)

            plan_files.uploaded_file = f
            plan_files.save()
    y, m, d = date.split("-")
    return Response({"ok": True, "message": f"Запись создана — {hospital_research.get_title()} {d}.{m}.{y}"})


@api_view(["POST"])
@can_use_schedule_only
def hosp_record_list(request):
    data = data_parse(
        request.body,
        {
            "snils": "str_strip",
            "enp": "str_strip",
        },
    )
    snils: str = data[0]
    enp: str = data[1]

    snils = "".join(ch for ch in snils if ch.isdigit())

    individual = None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        individual = individuals.first()

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title="СНИЛС")
        individual = individuals.first()

    if not individual:
        return Response({"rows": [], "message": "Физлицо не найдено"})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()

    if not card:
        return Response({"rows": [], "message": "Карта не найдена"})

    rows = []

    plan: PlanHospitalization
    for plan in PlanHospitalization.objects.filter(client=card, research__isnull=False, action=0).order_by("-exec_at"):
        status_description = ""
        if plan.work_status == 2:
            status_description = plan.why_cancel
        if plan.work_status == 3:
            slot_plan = plan.slot_fact.plan
            status_description = slot_plan.datetime.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%d.%m.%Y %H:%M")
        rows_files = []
        row_file: PlanHospitalizationFiles
        for row_file in PlanHospitalizationFiles.objects.filter(plan=plan).order_by("-created_at"):
            rows_files.append(
                {
                    "pk": row_file.pk,
                    "fileName": os.path.basename(row_file.uploaded_file.name) if row_file.uploaded_file else None,
                }
            )
        messages_data = Messages.get_messages_by_plan_hosp(plan.pk, last=True)
        rows.append(
            {
                "pk": plan.pk,
                "service": plan.research.get_title(),
                "date": plan.exec_at.strftime("%d.%m.%Y"),
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


@api_view(["POST"])
def get_all_messages_by_plan_id(request):
    data = data_parse(request.body, {"pk": int})
    pk: int = data[0]
    messages = Messages.get_messages_by_plan_hosp(pk, last=False)
    return Response({"rows": messages})


@api_view(["POST"])
def direction_records(request):
    data = data_parse(
        request.body,
        {"snils": "str_strip", "enp": "str_strip", "date_year": int},
    )
    snils: str = data[0]
    enp: str = data[1]
    date_year: int = data[2]

    card: Card = find_patient(snils, enp)
    if not card:
        return Response({"rows": [], "message": "Карта не найдена"})
    d1 = try_strptime(f"{date_year}-01-01", formats=("%Y-%m-%d",))
    d2 = try_strptime(f"{date_year}-12-31", formats=("%Y-%m-%d",))
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


@api_view(["POST"])
def directions_by_category_result_year(request):
    request_data = json.loads(request.body)
    mode = request_data.get("mode")
    is_lab = request_data.get("isLab", mode == "laboratory")
    is_paraclinic = request_data.get("isParaclinic", mode == "paraclinic")
    is_doc_refferal = request_data.get("isDocReferral", mode == "docReferral")
    is_extract = request_data.get("isExtract", mode == "extract")
    is_user_forms = request_data.get("isUserForms", mode == "forms")
    year = request_data["year"]

    card: Card = find_patient(request_data.get("snils"), request_data.get("enp"))
    if not card:
        return Response({"results": [], "message": "Карта не найдена"})

    d1 = datetime.datetime.strptime(f"{LK_DAY_MONTH_START_SHOW_RESULT}{year}", "%d.%m.%Y")
    start_date = datetime.datetime.combine(d1, datetime.time.min)
    d2 = datetime.datetime.strptime(f"31.12.{year}", "%d.%m.%Y")
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
        extract_research_pks = tuple(HospitalService.objects.values_list("slave_research__id", flat=True).filter(site_type=7))
        if extract_research_pks:
            confirmed_directions = get_confirm_direction_patient_year_is_extract(start_date, end_date, card.pk, extract_research_pks)

    if not is_extract and not confirmed_directions:
        confirmed_directions = get_confirm_direction_patient_year(start_date, end_date, lab_podr, card.pk, is_lab, is_paraclinic, is_doc_refferal, is_user_forms)

    if not confirmed_directions:
        return JsonResponse({"results": []})

    directions = {}

    for d in confirmed_directions:
        if d.direction not in directions:
            dicom_server_url = None
            if d.study_instance_uid_tag:
                data = {"Level": "Study", "Query": {"StudyInstanceUID": d.study_instance_uid_tag}, "Expand": True}
                if len(DICOM_SERVERS) > 1:
                    is_dicom_study = check_dicom_study(DICOM_SERVERS, data)
                    if is_dicom_study.get("server"):
                        dicom_server_url = is_dicom_study.get("server")
                else:
                    dicom_server_url = DICOM_SERVER
            directions[d.direction] = {"pk": d.direction, "confirmedAt": d.ch_time_confirmation, "services": [], "study": d.study_instance_uid_tag, "server": dicom_server_url}
        directions[d.direction]["services"].append(d.research_title)

    return JsonResponse({"results": list(directions.values())})


@api_view(["POST"])
def results_by_direction(request):
    request_data = json.loads(request.body)
    token = request.headers.get("Authorization").split(" ")[1]
    token_obj = Application.objects.filter(key=token).first()
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})
    oid_org = request_data.get(("oid") or "")
    check_result = check_correct_hosp(request, oid_org)
    if not check_result["OK"]:
        return Response({"ok": False, "message": check_result["message"]})
    hospital = check_result["hospital"]
    mode = request_data.get("mode")
    is_lab = request_data.get("isLab", mode == "laboratory")
    is_paraclinic = request_data.get("isParaclinic", mode == "paraclinic")
    is_doc_refferal = request_data.get("isDocReferral", mode == "docReferral")
    is_user_forms = request_data.get("isUserFroms", mode == "forms")
    direction = request_data.get("pk")
    external_add_order = request_data.get("externalOrder")
    directions_data = request_data.get("directions")
    if is_lab and not directions_data:
        if external_add_order:
            ext_add_order_obj = directions.ExternalAdditionalOrder.objects.filter(external_add_order=external_add_order).first()
            iss_data = directions.Issledovaniya.objects.filter(external_add_order=ext_add_order_obj).first()
            direction = iss_data.napravleniye_id
        directions_data = [direction]
    else:
        directions_data = [direction]
    if not token_obj.unlimited_access:
        for d in directions_data:
            direction_obj = Napravleniya.objects.filter(hospital=hospital, pk=d).first()
            if not direction_obj:
                return Response({"ok": False, "message": "Номер направления не принадлежит организации"})

    objs_result = {}
    if is_lab:
        direction_result = get_laboratory_results_by_directions(tuple(directions_data))
        for r in direction_result:
            if r.direction not in objs_result:
                objs_result[r.direction] = {"pk": r.direction, "confirmedAt": r.date_confirm, "services": {}}

            if r.iss_id not in objs_result[r.direction]["services"]:
                objs_result[r.direction]["services"][r.iss_id] = {
                    "title": r.research_title,
                    "internalCode": r.research_internal_code,
                    "fio": short_fio_dots(r.fio) if r.fio else r.doc_confirmation_string,
                    "confirmedAt": r.date_confirm,
                    "fractions": [],
                }

            objs_result[r.direction]["services"][r.iss_id]["fractions"].append(
                {
                    "title": r.fraction_title,
                    "value": r.value,
                    "units": r.units,
                    "fsli": r.fraction_fsli,
                    "ref_m": r.ref_m,
                    "ref_f": r.ref_f,
                }
            )

    if is_paraclinic or is_doc_refferal or is_user_forms:
        results = desc_to_data(directions_data, force_all_fields=True)
        for i in results:
            direction_data = i["result"][0]["date"].split(" ")
            if direction_data[1] not in objs_result:
                objs_result[direction_data[1]] = {"pk": direction_data[1], "confirmedAt": direction_data[0], "services": {}}
            if i["result"][0]["iss_id"] not in objs_result[direction_data[1]]["services"]:
                objs_result[direction_data[1]]["services"][i["result"][0]["iss_id"]] = {
                    "title": i["title_research"],
                    "fio": short_fio_dots(i["result"][0]["docConfirm"]),
                    "confirmedAt": direction_data[0],
                    "fractions": [],
                }

            values = values_as_structure_data(i["result"][0]["data"])
            objs_result[direction_data[1]]["services"][i["result"][0]["iss_id"]]["fractions"].extend(values)

    return JsonResponse({"results": list(objs_result.values())})


@api_view(["POST"])
@can_use_schedule_only
def check_employee(request):
    data = json.loads(request.body)
    snils = data.get("snils")
    date_now = current_time(only_date=True)
    doctor_profile = DoctorProfile.objects.filter(snils=snils, external_access=True, date_stop_external_access__gte=date_now).first()
    if doctor_profile:
        return Response({"ok": True})
    return Response({"ok": False})


@api_view(["GET"])
@can_use_schedule_only
def hospitalization_plan_research(request):
    return Response({"services": get_hospital_resource()})


@api_view(["POST"])
@can_use_schedule_only
def available_hospitalization_plan(request):
    data = json.loads(request.body)
    research_pk = data.get("research_pk")
    resource_id = data.get("resource_id")
    date_start = data.get("date_start")
    date_end = data.get("date_end")

    result, _ = get_available_hospital_plans(research_pk, resource_id, date_start, date_end)
    return Response({"data": result})


@api_view(["POST"])
@can_use_schedule_only
def check_hosp_slot_before_save(request):
    data = json.loads(request.body)
    research_pk = data.get("research_pk")
    resource_id = data.get("resource_id")
    date = data.get("date")

    result = check_available_hospital_slot_before_save(research_pk, resource_id, date)
    return JsonResponse({"result": result})


@api_view(["POST"])
@can_use_schedule_only
def get_pdf_result(request):
    data = json.loads(request.body)
    pk = data.get("pk")
    pdf_content = direction_pdf_result(pk)
    return JsonResponse({"result": pdf_content})


@api_view(["POST"])
@can_use_schedule_only
def get_pdf_direction(request):
    data = json.loads(request.body)
    pk = data.get("pk")
    localclient = TC(enforce_csrf_checks=False)
    addr = "/directions/pdf"
    params = {"napr_id": json.dumps([pk]), "token": "8d63a9d6-c977-4c7b-a27c-64f9ba8086a7"}
    result = localclient.get(addr, params).content
    pdf_content = base64.b64encode(result).decode("utf-8")
    return JsonResponse({"result": pdf_content})


@api_view(["POST"])
@can_use_schedule_only
def documents_lk(request):
    return Response({"documents": get_can_created_patient()})


@api_view(["POST"])
@can_use_schedule_only
def details_document_lk(request):
    data = data_parse(
        request.body,
        {"pk": int},
    )
    pk: int = data[0]
    response = get_researches_details(pk)
    return Response(response)


@api_view(["POST"])
@can_use_schedule_only
def forms_lk(request):
    response = {"forms": LK_FORMS}
    return Response(response)


@api_view(["POST"])
@can_use_schedule_only
def pdf_form_lk(request):
    data = data_parse(
        request.body,
        {"type_form": str, "snils": str, "enp": str, "agent": {"snils": str, "enp": str}},
    )
    type_form: str = data[0]
    snils: str = data[1]
    enp: str = data[2]

    card: Card = find_patient(snils, enp)
    if not card:
        return Response({"results": [], "message": "Карта не найдена"})

    f = import_string("forms.forms" + type_form[0:3] + ".form_" + type_form[4:6])
    user = User.objects.get(pk=LK_USER)
    result = f(
        request_data={
            "card_pk": card,
            "user": user,
            "hospital": user.doctorprofile.get_hospital(),
        }
    )
    pdf_content = base64.b64encode(result).decode("utf-8")
    return Response({"result": pdf_content})


@api_view(["POST", "PUT"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@can_use_schedule_only
def add_file_hospital_plan(request):
    file = request.data.get("file-add")
    data = data_parse(request.data.get("document"), {"pk": int})
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


@api_view(["POST"])
@can_use_schedule_only
def get_limit_download_files(request):
    return Response({"lk_file_count": LK_FILE_COUNT, "lk_file_size_bytes": LK_FILE_SIZE_BYTES})


@api_view(["POST"])
@can_use_schedule_only
def document_lk_save(request):
    form = request.body
    request_data = json.loads(form)
    ogrn = request_data.get("ogrn" or "")
    hospital = None
    if not request.user.unlimited_access:
        check_permissions = check_correct_hospital_company(request, ogrn)
        if not check_permissions["OK"]:
            return Response({"ok": False, "message": check_permissions["message"]})
        hospital = check_permissions["hospital"]

    data = data_parse(
        form,
        {
            "snils": "str_strip",
            "enp": "str_strip",
            "family": "str_strip",
            "name": "str_strip",
            "patronymic": "str_strip",
            "sex": "str_strip",
            "birthdate": "str_strip",
            "service": int,
            "groups": list,
            "phone": "str_strip",
        },
        {
            "phone": "",
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

    if sex == "m":
        sex = "м"

    if sex == "f":
        sex = "ж"

    snils = "".join(ch for ch in snils if ch.isdigit())

    individual = None
    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        individual = individuals.first()

    if not individual and snils:
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title="СНИЛС")
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
        return Response({"ok": False, "message": "Физлицо не найдено"})

    card = Card.objects.filter(individual=individual, base__internal_type=True).first()
    if not card:
        card = Card.add_l2_card(individual)

    if not card:
        return Response({"ok": False, "message": "Карта не найдена"})

    if SCHEDULE_AGE_LIMIT_LTE:
        age = card.individual.age()
        if age > SCHEDULE_AGE_LIMIT_LTE:
            return Response({"ok": False, "message": f"Пациент должен быть не старше {SCHEDULE_AGE_LIMIT_LTE} лет"})

    service: Researches = Researches.objects.filter(pk=service, can_created_patient=True).first()

    if not service:
        return Response({"ok": False, "message": "Услуга не найдена"})

    date = timezone.now()
    date_start = date_at_bound(date)
    fields_data = []
    if not request_data.get("externalProtocol"):
        user = User.objects.get(pk=LK_USER).doctorprofile
    else:
        login = request_data.get("login")
        user = User.objects.get(username=login).doctorprofile
        if user.hospital != hospital:
            return Response({"ok": False, "message": "Логин не соответствует организации"})
        fields_data = request_data.get("fieldsData")

    if Napravleniya.objects.filter(client=card, issledovaniya__research=service, data_sozdaniya__gte=date_start).count() > 1:
        return Response({"ok": False, "message": "Вы сегодня уже заполняли эту форму два раза!\nПопробуйте позднее."})

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

        if not request_data.get("externalProtocol"):
            for g in groups[:50]:
                if g["title"] and g["show_title"]:
                    comment_lines.append(f"{g['title']}:")

                for f in g["fields"][:50]:
                    if not f["new_value"]:
                        continue
                    fields_count += 1
                    f_result = directions.ParaclinicResult(issledovaniye=iss, field_id=f["pk"], field_type=f["field_type"], value=html.escape(f["new_value"][:400]))
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
                        "card": card,
                        "research": service.pk,
                        "address": card.main_address,
                        "district": -1,
                        "date": current_time(),
                        "comment": "\n".join(comment_lines),
                        "phone": phone,
                        "doc": -1,
                        "purpose": 24,
                        "hospital": hospital.pk,
                        "external": True,
                        "external_num": str(direction),
                        "is_main_external": False,
                        "direction": direction,
                    }
                )
                return Response({"ok": True, "message": f"Заявка {direction} зарегистрирована"})
        else:
            for field_data in fields_data:
                f_result = directions.ParaclinicResult(issledovaniye=iss, field_id=field_data.get("fieldId"), field_type=field_data.get("fieldTypeId"), value=field_data.get("fieldValue"))
                f_result.save()

    return Response({"ok": True, "message": f'Форма "{service.get_title()}" ({direction}) сохранена'})


@api_view(["POST"])
def amd_save(request):
    data = json.loads(request.body)
    local_uid = data.get("localUid")
    direction_pk = data.get("pk")
    status = data.get("status")
    message_id = data.get("messageId")
    message = data.get("message")
    kind = data.get("kind")
    organization_oid = data.get("organizationOid")
    hospital = Hospitals.objects.filter(oid=organization_oid).first()

    emdr_id = data.get("emdrId")
    registration_date = data.get("registrationDate")
    if registration_date:
        registration_date = datetime.datetime.strptime(registration_date, "%Y-%m-%d %H:%M:%S")

    type = data.get("type")
    if type and type == "registerDocument":
        time_exec = data.get("timeExec")
        time_exec = datetime.datetime.strptime(time_exec, "%Y-%m-%d %H:%M:%S")
        department_oid = data.get("departmentOid")
        podrazdeleniye = Podrazdeleniya.objects.filter(oid=department_oid).first()
        amd = ArchiveMedicalDocuments(
            local_uid=local_uid,
            direction_id=direction_pk,
            status=status,
            message_id=message_id,
            organization=hospital,
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
        code = data.get("code")
        amd.message = f"{code}@{message}"
        amd.save()
    return Response({"ok": True})


@api_view(["POST"])
def register_emdr_id(request):
    data = json.loads(request.body)
    emdr_id = data.get("localUid")
    direction_pk = data.get("pk")
    direction = Napravleniya.objects.get(pk=direction_pk)
    direction.emdr_id = emdr_id
    direction.save(update_fields=["emdr_id"])
    return Response({"ok": True})


@api_view(["POST"])
def get_direction_pk_by_emdr_id(request):
    data = json.loads(request.body)
    emdr_id = data.get("emdrId")
    direction = Napravleniya.objects.get(emdr_id=emdr_id)
    return Response({"pk": direction.pk})


@api_view(["POST"])
def get_value_field(request):
    data = json.loads(request.body)
    research_id = data.get("researchId")
    field_id = data.get("fieldId")
    date = data.get("date")
    type_period = data.get("typePeriod")
    research_obj = Researches.objects.filter(pk=research_id).first()
    data = []
    if research_obj and research_obj.is_monitoring:
        query_data = directions.MonitoringResult.objects.filter(type_period=type_period, period_date=date, field_id=int(field_id), research_id=research_id)
        data = [
            {
                "hospitalTitle": i.hospital.title,
                "hospitalOid": i.hospital.oid,
                "valueAggregate": i.value_aggregate,
                "valueText": i.value_text,
                "period_param_hour": i.period_param_hour,
                "period_param_day": i.period_param_day,
                "period_param_week_description": i.period_param_week_description,
                "period_param_week_date_start": i.period_param_week_date_start,
                "period_param_week_date_end": i.period_param_week_date_end,
                "period_param_month": i.period_param_month,
                "period_param_year": i.period_param_year,
            }
            for i in query_data
        ]
    return Response({"data": data})


@api_view(["POST"])
def get_price_data(request):
    request_data = json.loads(request.body)
    price_code = request_data.get("priceCode")
    price_id = request_data.get("priceId")

    token = request.headers.get("Authorization").split(" ")[1]
    token_obj = Application.objects.filter(key=token).first()
    result = []
    if not token_obj.unlimited_access:
        if not price_code and not price_id:
            return {"OK": False, "message": "priceCode или priceId должны быть переданы"}
        check_permissions_price = check_correct_hospital_company_for_price(request, price_code, price_id)
        if not check_permissions_price["OK"]:
            return Response({"ok": False, "message": check_permissions_price["message"]})
        price = check_permissions_price["price"]
    else:
        price = PriceName.get_price_by_id_symbol_code(price_code, price_id)
    if price:
        data_price = PriceCoast.objects.filter(price_name=price)
        result = [
            {"title": i.research.title, "shortTitle": i.research.short_title, "coast": i.coast, "internalCode": i.research.internal_code, "researchCodeNMU": i.research.code}
            for i in data_price
        ]
    return Response({"data": result})


@api_view(["POST"])
def get_prices_by_date(request):
    request_data = json.loads(request.body)
    token = request.headers.get("Authorization").split(" ")[1]
    token_obj = Application.objects.filter(key=token).first()
    ogrn = request_data.get("ogrn" or "")
    date = request_data.get("date" or "")
    if not token_obj.unlimited_access:
        check_permissions = check_correct_hospital_company(request, ogrn)
        if not check_permissions["OK"]:
            return Response({"ok": False, "message": check_permissions["message"]})
        hospital = check_permissions["hospital"]
        company = check_permissions["company"]
        is_company = check_permissions["is_company"]
        if is_company:
            prices = PriceName.objects.filter(company=company, date_start__lte=date, date_end__gte=date)
        else:
            prices = PriceName.objects.filter(hospital=hospital, date_start__lte=date, date_end__gte=date)
    else:
        prices = PriceName.objects.filter(date_start__lte=date, date_end__gte=date)

    result = [
        {
            "id": i.pk,
            "priceCode": i.symbol_code,
            "title": i.title,
            "dateStart": i.date_start,
            "dateEnd": i.date_end,
        }
        for i in prices
    ]

    return Response({"data": result})


@api_view(["POST"])
def get_reference_books(request):
    request_data = json.loads(request.body)
    token = request.headers.get("Authorization").split(" ")[1]
    token_obj = Application.objects.filter(key=token).first()
    mode = request_data.get("mode")
    is_lab = request_data.get("isLab", mode == "laboratory")
    if not token_obj.unlimited_access:
        return Response({"ok": False, "message": "Некорректный auth токен"})
    result = []
    if is_lab:
        lab_data = get_lab_research_reference_books()
        service_result = {"serviceId": "", "serviceTitle": "", "serviceInternalCode": "", "serviceNMUCode": "", "fractions": []}

        last_research_id = -1
        step = 0
        tmp_result = service_result.copy()
        fractions = []
        for i in lab_data:
            if i.research_id != last_research_id:
                if step != 0:
                    result.append(tmp_result.copy())
                    fractions = []
                tmp_result = service_result.copy()
                tmp_result["serviceId"] = i.research_id
                tmp_result["serviceTitle"] = i.research_title
                tmp_result["serviceInternalCode"] = i.research_internal_code
                tmp_result["serviceNMUCode"] = i.research_nmu_code
                tmp_result["fractions"] = fractions

            fractions.append(
                {
                    "id": i.fraction_id,
                    "title": i.fraction_title,
                    "fsli": i.fraction_fsli,
                    "ref_m": json.loads(i.fraction_ref_m),
                    "ref_f": json.loads(i.fraction_ref_f),
                    "unitTitle": i.unit_title,
                    "unitCode": i.unit_code,
                    "unitUcum": i.unit_ucum,
                }
            )

            last_research_id = i.research_id
            step += 1
        tmp_result["fractions"] = fractions
        result.append(tmp_result.copy())
    return JsonResponse({"result": result})


@api_view(["POST"])
def get_research_fields(request):
    request_data = json.loads(request.body)
    ogrn = request_data.get("ogrn")
    research_id = request_data.get("researchId")
    if not request.user.unlimited_access:
        check_permissions = check_correct_hospital_company(request, ogrn)
        if not check_permissions["OK"]:
            return Response({"ok": False, "message": check_permissions["message"]})
    paraclinic_input_groups = ParaclinicInputGroups.objects.values_list("pk", flat=True).filter(research_id=research_id, hide=False).order_by("order")
    paraclinic_input_fields = ParaclinicInputField.objects.filter(group_id__in=paraclinic_input_groups, hide=False).order_by("order")
    data_fields = [
        {"title": i.title, "id": i.pk, "typeId": i.field_type, "typeTitle": i.get_field_type_display(), "inputTemplates": json.loads(i.input_templates)} for i in paraclinic_input_fields
    ]
    research = Researches.objects.get(pk=research_id)

    return Response({"fields": data_fields, "service": {"title": research.title, "id": research.pk}})


@api_view(["POST"])
def send_laboratory_order(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)

    org = body.get("org", {})
    code_tfoms = org.get("codeTFOMS")
    oid_org = org.get("oid")

    if not code_tfoms and not oid_org:
        return Response({"ok": False, "message": "Должно быть указано хотя бы одно значение из org.codeTFOMS или org.oid"})

    if code_tfoms:
        hospital = Hospitals.objects.filter(code_tfoms=code_tfoms).first()
    else:
        hospital = Hospitals.objects.filter(oid=oid_org).first()

    if not hospital:
        return Response({"ok": False, "message": "Организация не найдена"})

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return Response({"ok": False, "message": "Нет доступа в переданную организацию"})

    patient = body.get("patient", {})

    enp = (patient.get("enp") or "").replace(" ", "")
    snils = (patient.get("snils") or "").replace(" ", "").replace("-", "")

    if enp and (len(enp) != 16 or not enp.isdigit()):
        return Response({"ok": False, "message": "Неверные данные полиса, должно быть 16 чисел"})
    if snils and not petrovna.validate_snils(snils):
        return Response({"ok": False, "message": "patient.snils: не прошёл валидацию"})

    lastname = str(patient.get("lastname") or "")
    firstname = str(patient.get("firstname") or "")
    patronymic = str(patient.get("patronymic") or "")
    birthdate = str(patient.get("birthdate") or "")
    sex = str(patient.get("sex") or "").lower()

    if not enp and not (lastname and firstname and birthdate and sex):
        return Response({"ok": False, "message": "При пустом patient.enp должно быть передано поле patient.lastname patient.firstname patient.birthdate patient.sex"})

    individual = None

    if lastname and not firstname:
        return Response({"ok": False, "message": "При передаче lastname должен быть передан и firstname"})

    if firstname and not lastname:
        return Response({"ok": False, "message": "При передаче firstname должен быть передан и lastname"})

    if firstname and lastname and not birthdate:
        return Response({"ok": False, "message": "При передаче firstname и lastname должно быть передано поле birthdate"})

    if birthdate and (not re.fullmatch(r"\d{4}-\d\d-\d\d", birthdate) or birthdate[0] not in ["1", "2"]):
        return Response({"ok": False, "message": "birthdate должно соответствовать формату YYYY-MM-DD"})

    if birthdate and sex not in ["м", "ж"]:
        return Response({"ok": False, "message": 'patient.sex должно быть "м" или "ж"'})

    if enp:
        individuals = Individual.objects.filter(tfoms_enp=enp)
        if not individuals.exists():
            individuals = Individual.objects.filter(document__number=enp).filter(Q(document__document_type__title="Полис ОМС") | Q(document__document_type__title="ЕНП"))
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
        individuals = Individual.objects.filter(document__number=snils, document__document_type__title="СНИЛС")
        individual = individuals.first()

    card = None
    if not individual and lastname:
        card = Individual.import_from_simple_data(
            {
                "family": patient["lastname"],
                "name": patient["firstname"],
                "patronymic": patient["patronymic"],
                "sex": patient["sex"],
                "birthday": patient["birthdate"],
                "snils": patient["snils"],
            },
            hospital,
            patient["internalId"],
            patient["email"],
            patient["phone"],
        )
        card.main_address = patient["mainAddress"]
        card.fact_address = patient["factAddress"]
        card.save(update_fields=["main_address", "fact_address"])
    if not card:
        return Response({"ok": False, "message": "Карта не найдена"})
    pay_data = body.get("payData", {})

    financing_source_title = pay_data.get("financingSourcetitle", "")
    price_id = pay_data.get("priceId", "")

    financing_source = directions.IstochnikiFinansirovaniya.objects.filter(title__iexact=financing_source_title, base__internal_type=True).first()

    if not financing_source:
        return Response({"ok": False, "message": "Некорректный источник финансирования"})

    order_data = body.get("orderData")
    order_internal_id = order_data.get("internalId", "")

    if order_internal_id is None:
        return Response({"ok": False, "message": "Некорректный номер заказа orderData.internalId"})
    else:
        id_in_hospital = limit_str(order_internal_id, 15)
        if Napravleniya.objects.filter(id_in_hospital=id_in_hospital, hospital=hospital).first():
            return Response({"ok": False, "message": f"Уже существует номер заказа {id_in_hospital} в orderData.internalId для текуще организации"})

    tubes = order_data.get("tubes")
    internal_research_code_by_tube_number = {}
    additional_order_number_by_service = {}
    for tube in tubes:
        tube_number = tube.get("tubeNumber")
        if not tube_number:
            return Response({"ok": False, "message": "не указан tubeNumber "})

        if not directions.NumberGenerator.check_value_for_organization(hospital, int(tube_number)):
            return Response({"ok": False, "message": f"Номер {tube_number} not valid. May be NumberGenerator is over or order number exists"})

        if directions.TubesRegistration.objects.filter(number=int(tube_number)).first():
            return Response({"ok": False, "message": f"Номер {tube_number} уже существует"})

        internal_research_code_by_tube_number[tube_number] = []
        for data_research in tube.get("researches"):
            if not Researches.objects.filter(hide=False, internal_code=data_research.get("internalCode")).first():
                return Response({"ok": False, "message": "Некорректный номер услуги internalCode"})
            internal_research_code_by_tube_number[tube_number].append(data_research.get("internalCode"))
            additional_order_number_by_service[data_research.get("internalCode")] = data_research.get("additionalNumber")
    order_numbers = []

    with transaction.atomic():
        doc = DoctorProfile.get_system_profile()
        services_by_order_number = {}
        services_by_additional_order_num = {}
        for order_number, services_codes in internal_research_code_by_tube_number.items():
            for service_code in services_codes:
                service = Researches.objects.filter(hide=False, internal_code=service_code).first()
                if not service:
                    raise ServiceNotFoundException(f"Service {service_code} not found")
                if order_number not in services_by_order_number:
                    services_by_order_number[order_number] = []
                services_by_order_number[order_number].append(service.pk)
                services_by_additional_order_num[service.pk] = additional_order_number_by_service.get(service_code, "")

        for order_number_str, services in services_by_order_number.items():
            order_numbers.append(order_number_str)

            if not order_number_str.isdigit():
                raise InvalidOrderNumberException(f"Number {order_number} is not digit")
            order_number = int(order_number_str)
            if order_number <= 0:
                raise InvalidOrderNumberException(f"Number {order_number} need to be greater than 0")
            if not directions.NumberGenerator.check_value_for_organization(hospital, order_number):
                raise InvalidOrderNumberException(f"Number {order_number} not valid. May be NumberGenerator is over or order number exists")

            external_order = directions.RegisteredOrders.objects.create(
                order_number=order_number,
                organization=hospital,
                services=internal_research_code_by_tube_number[order_number_str],
                patient_card=card,
                file_name="",
                hl7=order_data.get("hl7", ""),
            )
            result = Napravleniya.gen_napravleniya_by_issledovaniya(
                card.pk,
                "",
                financing_source.pk,
                "",
                None,
                doc,
                {-1: services},
                {},
                False,
                {},
                vich_code="",
                count=1,
                discount=0,
                rmis_slot=None,
                external_order=external_order,
                hospital_override=hospital.pk,
                services_by_additional_order_num=services_by_additional_order_num,
                price_name=price_id,
                id_in_hospital=id_in_hospital,
            )

            if not result["r"]:
                raise FailedCreatingDirectionsException(result.get("message") or "Failed creating directions")

            Log.log(
                json.dumps(order_numbers),
                190004,
                None,
                {
                    "org": hospital.safe_short_title,
                    "content": body,
                    "service": services,
                    "directions": result["list_id"],
                    "card": card.number_with_type(),
                },
            )

    return Response({"ok": True, "message": "", "directions": result["list_id"]})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def client_register(request):
    body = json.loads(request.body)
    phone = str(body.get("phone"))
    os = str(body.get("os"))

    ip = Log.get_client_ip(request)

    if IPLimitter.check_limit(ip):
        return Response({"ok": False, "message": "Too many requests"})

    if len(phone) != 10 or not phone.isdigit() or phone[0] != "9":
        return Response({"ok": False, "message": "Неверный формат телефона"})

    code = body.get("code")

    if code is not None and (not isinstance(code, str) or (code and len(code) != 4 or not code.isdigit())):
        return Response({"ok": False, "message": "Неверный формат кода"})

    token = body.get("token")

    if token is not None and not isinstance(token, str):
        return Response({"ok": False, "message": "Неверный формат токена"})

    ok = False
    need_code = False
    api_token = None
    error = None
    message = None

    if token is None or code is None:
        code_n = random.randint(0, 9)
        code_x = random.randint(0, 9)
        code_y = random.randint(0, 9)
        code = f"{code_n}{code_x}{code_n}{code_y}"
        auth = IndividualAuth.objects.create(
            device_os=os,
            confirmation_code=code,
            used_phone=Phones.format_as_plus_7(phone),
        )
        api_token = auth.token
        send_code_cascade.apply_async(
            kwargs={
                "phone": phone,
                "auth_id": auth.pk,
            },
            countdown=1,
        )

        need_code = True
    else:
        auth: IndividualAuth = IndividualAuth.objects.filter(
            token=token,
            is_confirmed=False,
            device_os=os,
            used_phone=Phones.format_as_plus_7(phone),
        ).first()

        if auth:
            time.sleep(auth.code_check_count * 2)
            auth.code_check_count += 1
            auth.save(update_fields=["code_check_count"])

        if not auth or auth.confirmation_code != code:
            need_code = True
            api_token = token
            error = True
            message = "Неверный код"
        else:
            auth.is_confirmed = True
            auth.save(update_fields=["is_confirmed"])
            ok = True
            api_token = token
            stop_code_cascade.apply_async(
                kwargs={
                    'auth_id': auth.pk,
                },
                countdown=1,
            )

    return Response(
        {
            "ok": ok,
            "needCode": need_code,
            "apiToken": api_token,
            "error": error,
            "message": message,
        }
    )


@api_view(["POST"])
@authentication_classes([IndividualAuthentication])
@permission_classes([])
def client_logout(request):
    individual: IndividualAuth = request.user

    individual.is_confirmed = False
    individual.save(update_fields=["is_confirmed"])

    return Response(
        {
            "ok": True,
        }
    )


@api_view(["POST"])
@authentication_classes([IndividualAuthentication])
@permission_classes([])
def client_info(request):
    individual_auth: IndividualAuth = request.user

    individuals = list(individual_auth.individuals)

    return Response(
        {
            "rows": [
                {
                    "id": individual.pk,
                    "fullName": f"{individual.fio(dots=True, short=True)} {individual.age_s()}",
                    "phone": individual_auth.used_phone or "--",
                }
                for individual in individuals
            ]
            if individuals
            else [
                {
                    "id": -1,
                    "fullName": "Нет данных",
                    "phone": individual_auth.used_phone or "--",
                }
            ]
        }
    )


@api_view(["POST"])
@authentication_classes([IndividualAuthentication])
@permission_classes([])
def client_categories(request):
    return Response(
        {
            "categories": [
                {
                    "id": "all",
                    "title": "Все результаты",
                },
                {
                    "id": "consultations",
                    "title": "Консультации",
                },
                {
                    "id": "laboratory",
                    "title": "Лаборатория",
                },
                {
                    "id": "diagnostics",
                    "title": "Диагностика",
                },
            ],
        }
    )


@api_view(["POST"])
@authentication_classes([IndividualAuthentication])
@permission_classes([])
def client_results_list(request):
    individual_auth: IndividualAuth = request.user
    body = json.loads(request.body)
    category = body.get("category")
    user_id = body.get("userId")
    page = max(min(body.get("page", 1), 1000), 1)
    page_size = max(min(body.get("pageSize", 20), 20), 10)

    if category not in ["all", *[x[0] for x in ResultFeed.CATEGORIES]]:
        return Response({"rows": [], "total": 0, "pages": 0, "page": page, "pageSize": page_size})

    individual = individual_auth.individuals.get(pk=user_id)
    rows = ResultFeed.objects.filter(individual=individual)
    if category != "all":
        rows = rows.filter(category=category)
    rows = rows.order_by("-result_confirmed_at")

    paginator = Paginator(rows, page_size)
    page = paginator.get_page(page)

    return Response(
        {
            "rows": [x.json for x in page.object_list],
            "total": paginator.count,
            "pages": paginator.num_pages,
            "page": page.number,
            "pageSize": page_size,
        }
    )


@api_view(["POST"])
@authentication_classes([IndividualAuthentication])
@permission_classes([])
def client_results_pdf(request):
    individual_auth: IndividualAuth = request.user
    body = json.loads(request.body)
    unique_id = body.get("id")
    user_id = body.get("userId")

    individual = individual_auth.individuals.get(pk=user_id)
    result: ResultFeed = ResultFeed.objects.filter(individual=individual, unique_id=unique_id).first()

    if not result:
        return Response({"data": ""})

    from results.views import result_print

    request_tuple = collections.namedtuple("HttpRequest", ("GET", "user", "plain_response"))
    req = {
        "GET": {
            "pk": f"[{result.direction_id}]",
            "split": "1",
            "leftnone": "0",
            "inline": "1",
            "protocol_plain_text": "1",
        },
        "user": request.user,
        "plain_response": True,
    }
    pdf_content = base64.b64encode(result_print(request_tuple(**req))).decode("utf-8")

    return Response({"data": pdf_content, "name": f"{result.direction_id}.pdf"})


@api_view(["POST"])
@authentication_classes([IndividualAuthentication])
@permission_classes([])
def client_fcm(request):
    individual: IndividualAuth = request.user
    body = json.loads(request.body)
    token = body.get("token")

    if not token:
        return Response({"ok": False, "message": "Неверный формат токена"})

    individual.fcm_token = token
    individual.save(update_fields=["fcm_token"])

    return Response({"ok": True})
