import base64
import math
import os
import uuid
from typing import Optional

from django.core.paginator import Paginator

from barcodes.views import tubes
from cda.integration import cdator_gen_xml, render_cda
from contracts.models import PriceCategory, PriceCoast, PriceName, Company
from ecp_integration.integration import get_ecp_time_table_list_patient, get_ecp_evn_direction, fill_slot_ecp_free_nearest
from external_system.models import ProfessionsWorkersPositionsRefbook
from integration_framework.common_func import directions_pdf_result
from l2vi.integration import gen_cda_xml, send_cda_xml, send_lab_direction_to_ecp
import collections

from integration_framework.views import get_cda_data
from results.prepare_data import fields_result_only_title_fields
from utils.response import status_response
from hospitals.models import Hospitals, HospitalParams
import operator
import re
import time
from datetime import datetime, time as dtime, timedelta
from operator import itemgetter

import pytz_deprecation_shim as pytz
import simplejson as json
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import HttpRequest
from django.http import JsonResponse
from django.utils import dateformat
from django.utils import timezone
from api import sql_func
from api.dicom import search_dicom_study, check_server_port, check_dicom_study_instance_uid
from api.patients.views import save_dreg
from api.sql_func import get_fraction_result, get_field_result
from api.stationar.stationar_func import forbidden_edit_dir, desc_to_data
from api.views import get_reset_time_vars
from appconf.manager import SettingManager
from clients.models import Card, Individual, DispensaryReg, BenefitReg
from directions.models import (
    DirectionDocument,
    DocumentSign,
    Napravleniya,
    Issledovaniya,
    NumberGenerator,
    Result,
    ParaclinicResult,
    Recipe,
    MethodsOfTaking,
    ExternalOrganization,
    MicrobiologyResultCulture,
    MicrobiologyResultCultureAntibiotic,
    MicrobiologyResultPhenotype,
    DirectionToUserWatch,
    IstochnikiFinansirovaniya,
    DirectionsHistory,
    MonitoringResult,
    TubesRegistration,
    DirectionParamsResult,
    IssledovaniyaFiles,
    IssledovaniyaResultLaborant,
    SignatureCertificateDetails,
    GeneratorValuesAreOver,
    NoGenerator,
    ComplexResearchAccountPerson,
)
from directory.models import Fractions, ParaclinicInputGroups, ParaclinicTemplateName, ParaclinicInputField, HospitalService, Researches, AuxService
from laboratory import settings
from laboratory import utils
from laboratory.decorators import group_required
from laboratory.settings import (
    DICOM_SERVER,
    TIME_ZONE,
    REMD_ONLY_RESEARCH,
    REMD_EXCLUDE_RESEARCH,
    SHOW_EXAMINATION_DATE_IN_PARACLINIC_RESULT_PAGE,
    DICOM_SERVERS,
    TUBE_MAX_RESEARCH_WITH_SHARE,
)
from laboratory.utils import current_year, strdateru, strdatetime, strdate, strdatetimeru, strtime, tsdatetime, start_end_year, strfdatetime, current_time, replace_tz
from pharmacotherapy.models import ProcedureList, ProcedureListTimes, Drugs, FormRelease, MethodsReception
from results.sql_func import get_not_confirm_direction, get_laboratory_results_by_directions
from results.views import result_normal, result_print
from rmis_integration.client import Client, get_direction_full_data_cache
from slog.models import Log
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, Outcomes, Place
from users.models import DoctorProfile
from utils.common import non_selected_visible_type, none_if_minus_1, values_from_structure_data
from utils.dates import normalize_date, date_iter_range, try_strptime
from utils.dates import try_parse_range
from utils.xh import check_float_is_valid, short_fio_dots
from xml_generate.views import gen_resul_cpp_file, gen_result_cda_files
from .sql_func import (
    get_history_dir,
    get_confirm_direction,
    filter_direction_department,
    get_lab_podr,
    filter_direction_doctor,
    get_confirm_direction_patient_year,
    get_patient_contract,
    get_directions_by_user,
    get_confirm_direction_by_hospital,
    get_directions_meta_info,
    get_patient_open_case_data,
    get_template_research_by_department,
    get_template_field_by_department,
)
from api.stationar.stationar_func import hosp_get_hosp_direction, hosp_get_text_iss
from forms.forms_func import hosp_get_operation_data
from medical_certificates.models import ResearchesCertificate, MedicalCertificates
from utils.data_verification import data_parse
from utils.expertise import get_expertise
from ..patients.common_func import get_card_control_param, get_vital_param_in_hosp


@login_required
@group_required("Лечащий врач", "Врач-лаборант", "Оператор лечащего врача", "Заполнение мониторингов", "Свидетельство о смерти-доступ")
def directions_generate(request):
    result = {"ok": False, "directions": [], "directionsStationar": [], "message": ""}
    if request.method == "POST":
        p = json.loads(request.body)
        card_pk = p.get("card_pk")
        if card_pk == -1:
            hospital: Hospitals = request.user.doctorprofile.get_hospital()
            if hospital.client:
                card = hospital.client
            else:
                card = Individual.import_from_tfoms(
                    {
                        "enp": f"1010{hospital.code_tfoms}",
                        "family": "Больница",
                        "given": hospital.safe_short_title[:120],
                        "patronymic": "",
                        "gender": 'м',
                        "birthdate": '2000-01-01',
                    },
                    need_return_card=True,
                )
                hospital.client = card
                hospital.save()
            if card:
                card_pk = card.pk
        else:
            card = Card.objects.get(pk=card_pk)
        if card.base.forbidden_create_napr:
            result["message"] = "Для данного типа карт нельзя создать направления"
            return JsonResponse(result)
        fin_source = p.get("fin_source", -1)
        fin_source_pk = int(fin_source) if (isinstance(fin_source, int) or str(fin_source).isdigit()) else fin_source
        type_generate = p.get("type")
        researches = p.get("researches")

        args = [
            card_pk,
            p.get("diagnos"),
            fin_source_pk,
            p.get("history_num"),
            p.get("ofname_pk"),
            request.user.doctorprofile,
            researches,
            p.get("comments"),
            p.get("for_rmis"),
            p.get("rmis_data", {}),
        ]
        kwargs = dict(
            vich_code=p.get("vich_code", ""),
            count=p.get("count", 1),
            discount=p.get("discount", 0),
            parent_iss=p.get("parent_iss", None),
            parent_slave_hosp=p.get("parent_slave_hosp", None),
            counts=p.get("counts", {}),
            localizations=p.get("localizations", {}),
            service_locations=p.get("service_locations", {}),
            direction_purpose=p.get("direction_purpose", "NONE"),
            external_organization=p.get("external_organization", "NONE"),
            direction_form_params=p.get("direction_form_params", {}),
            current_global_direction_params=p.get("current_global_direction_params", {}),
            hospital_department_override=p.get("hospital_department_override", -1),
            hospital_override=p.get("hospital_override", -1),
            price_category=p.get("priceCategory", -1),
            case_id=p.get("caseId", -2),
            case_by_direction=p.get("caseByDirection", False),
            plan_start_date=p.get("planStartDate", None),
            slot_fact_id=p.get("slotFactId", None),
        )
        if type_generate == "calculate-cost":
            fin_source_obj = IstochnikiFinansirovaniya.objects.filter(pk=fin_source_pk).first()
            calculate_researches = []
            for values in researches.values():
                calculate_researches.extend(values)
            result_coast = 0
            if fin_source_obj.title.lower() in ["платно", "средства граждан"]:
                data_coast = PriceCoast.objects.filter(price_name=fin_source_obj.contracts.price, research_id__in=calculate_researches)
                for dc in data_coast:
                    result_coast += dc.coast
            result = {"ok": True, "directions": [], "directionsStationar": [], "message": result_coast}
            return JsonResponse(result)

        for _ in range(p.get("directions_count", 1)):
            rc = Napravleniya.gen_napravleniya_by_issledovaniya(*args, **kwargs)
            result["ok"] = rc["r"]
            if "message" in rc:
                result["message"] = rc["message"]
            result["directions"].extend(rc["list_id"])
            if "messageLimit" in rc:
                result["messageLimit"] = rc["messageLimit"]
            result["directionsStationar"].extend(rc["list_stationar_id"])
            if not result["ok"]:
                break

        if result["ok"]:
            for pk in result["directions"]:
                d: Napravleniya = Napravleniya.objects.get(pk=pk)
                d.fill_acsn()
                fill_slot_ecp_free_nearest(d)
                if SettingManager.get("auto_create_tubes_with_direction", default='false', default_type='b'):
                    resp = tubes(request, direction_implict_id=pk)
                    content_type = resp.headers.get("content-type")
                    if content_type == 'application/json':
                        resp_json = json.loads(resp.content)
                        if isinstance(resp_json, dict) and "message" in resp_json:
                            message_tube = resp_json["message"]
                            result["message"] + message_tube
    return JsonResponse(result)


@login_required
@group_required("Вспомогательные документы")
def aux_directions_generate(request):
    result = {"ok": False, "directions": [], "directionsStationar": [], "message": ""}
    if request.method == "POST":
        p = json.loads(request.body)
        direction_id = p.get("directionId", None)
        parent_iss = Issledovaniya.objects.filter(napravleniye_id=direction_id).first()
        direction_obj = Napravleniya.objects.filter(id=direction_id).first()
        aux_research = p.get("researches")
        fin_source = p.get("fin_source", -1)
        fin_source_pk = int(fin_source) if (isinstance(fin_source, int) or str(fin_source).isdigit()) else fin_source
        args = [
            direction_obj.client.pk,
            p.get("diagnos", "-"),
            fin_source_pk,
            p.get("history_num"),
            p.get("ofname_pk"),
            request.user.doctorprofile,
            aux_research,
            p.get("comments", {}),
            p.get("for_rmis"),
            p.get("rmis_data", {}),
        ]
        kwargs = dict(
            vich_code=p.get("vich_code", ""),
            count=p.get("count", 1),
            discount=p.get("discount", 0),
            parent_iss=parent_iss.id,
            parent_slave_hosp=p.get("parent_slave_hosp", None),
            counts=p.get("counts", {}),
            localizations=p.get("localizations", {}),
            service_locations=p.get("service_locations", {}),
            direction_purpose=p.get("direction_purpose", "NONE"),
            external_organization=p.get("external_organization", "NONE"),
            direction_form_params=p.get("direction_form_params", {}),
            current_global_direction_params=p.get("current_global_direction_params", {}),
            hospital_department_override=p.get("hospital_department_override", -1),
            hospital_override=p.get("hospital_override", -1),
            price_category=p.get("priceCategory", -1),
        )
        rc = Napravleniya.gen_napravleniya_by_issledovaniya(*args, **kwargs)
        result["ok"] = rc["r"]
        if "message" in rc:
            result["message"] = rc["message"]
        result["directions"].extend(rc["list_id"])
        if "messageLimit" in rc:
            result["messageLimit"] = rc["messageLimit"]
        result["directionsStationar"].extend(rc["list_stationar_id"])

        if result["ok"]:
            for pk in result["directions"]:
                d: Napravleniya = Napravleniya.objects.get(pk=pk)
                d.fill_acsn()
                fill_slot_ecp_free_nearest(d)
    return JsonResponse(result)


@login_required
@group_required("Лечащий врач", "Врач-лаборант", "Врач консультаций")
def add_additional_issledovaniye(request):
    saved = False
    p = json.loads(request.body)
    direction_pk = p.get("direction_pk", None)
    who_add = request.user.doctorprofile
    researches = p.get("researches", None)
    pks = []
    created_later_research = {x: True for x in Issledovaniya.objects.values_list("research_id", flat=True).filter(napravleniye_id=direction_pk)}
    with transaction.atomic():
        for research_pk in researches:
            if research_pk not in created_later_research:
                iss = Issledovaniya(napravleniye_id=direction_pk, research_id=research_pk, doc_add_additional=who_add)
                iss.save()
                pks.append(iss.pk)
                saved = True
    if saved:
        return status_response(True, data={"pks": pks})
    return status_response(False, "Операция не выполнена")


@login_required
def resend_results(request):
    request_data = json.loads(request.body)
    ids = request_data['ids']
    for pk in ids:
        direction = Napravleniya.objects.get(pk=pk)
        direction.post_confirmation()
    return status_response(True)


@login_required()
def need_order_redirection(request):
    request_data = json.loads(request.body)
    ids = request_data['ids']
    for pk in ids:
        direction = Napravleniya.objects.get(pk=pk)
        direction.need_order_redirection = True
        direction.save()
    return status_response(True)


@login_required
def directions_history(request):
    # SQL-query
    res = {"directions": []}
    request_data = json.loads(request.body)
    pk = request_data.get("patient", -1)
    req_status = request_data.get("type", 4)
    iss_pk = request_data.get("iss_pk", None)
    for_slave_hosp = request_data.get("forHospSlave", False)
    services = request_data.get("services", [])
    services = list(map(int, services or []))

    date_start, date_end = try_parse_range(request_data["date_from"], request_data["date_to"])
    date_start = datetime.combine(date_start, dtime.min)
    date_end = datetime.combine(date_end, dtime.max)
    user_creater = -1
    patient_card = -1
    final_result = []
    parent_obj = {"iss_id": "", "parent_title": "", "parent_is_hosp": "", "parent_is_doc_refferal": ""}

    # status: 4 - выписано пользователем, 0 - только выписанные, 1 - Материал получен лабораторией. 2 - результат подтвержден, 3 - направления пациента,  -1 - отменено,
    if req_status == 4:
        user_creater = request.user.doctorprofile.pk
    if req_status in [0, 1, 2, 3, 5, 7, 8]:
        patient_card = pk

    if req_status == 8:
        patient_complex_data = ComplexResearchAccountPerson.get_patient_complex_research(date_start, date_end, patient_card)

        final_result = [
            {
                "checked": False,
                "pacs": False,
                "has_hosp": False,
                "has_descriptive": False,
                "maybe_onco": False,
                "is_application": False,
                "lab": "",
                "parent": parent_obj,
                "is_expertise": False,
                "expertise_status": False,
                "person_contract_pk": "",
                "person_contract_dirs": "",
                "isComplex": True,
                'pk': i.get('pk'),
                'researches': i.get('researches'),
                'cancel': False,
                'date': i.get('date'),
                'status': f"из {i.get('current_sum_iss')} - {i.get('current_sum_iss_confirm')}",
                'planed_doctor': "",
                'register_number': "",
            }
            for i in patient_complex_data
        ]
        res['directions'] = final_result

        return JsonResponse(res)

    if req_status == 5:
        patient_contract = get_patient_contract(date_start, date_end, patient_card)
        count = 0
        last_contract = None
        temp_data = {
            'pk': "",
            'status': "",
            'researches': "",
            "researches_pks": "",
            'date': "",
            'cancel': False,
            'checked': False,
            'pacs': False,
            'has_hosp': False,
            'has_descriptive': False,
            'maybe_onco': False,
            'is_application': False,
            'isComplex': False,
            'lab': "",
            'parent': parent_obj,
            'is_expertise': False,
            'expertise_status': False,
            'person_contract_pk': "",
            'person_contract_dirs': "",
        }
        for i in patient_contract:
            if i.id != last_contract and count != 0:
                final_result.append(temp_data.copy())
                temp_data = {
                    'pk': "",
                    'status': "",
                    'researches': "",
                    "researches_pks": "",
                    'date': "",
                    'cancel': False,
                    'checked': False,
                    'pacs': False,
                    'has_hosp': False,
                    'has_descriptive': False,
                    'maybe_onco': False,
                    'is_application': False,
                    'isComplex': False,
                    'lab': "",
                    'parent': parent_obj,
                    'is_expertise': False,
                    'expertise_status': False,
                    'person_contract_pk': "",
                    'person_contract_dirs': "",
                }
            temp_data['pk'] = i.id
            if temp_data['researches']:
                temp_data['researches'] = f"{temp_data['researches']} | {i.title}"
            else:
                temp_data['researches'] = f"{i.title}"
            temp_data['cancel'] = i.cancel
            temp_data['date'] = i.date_create
            temp_data['status'] = i.sum_contract
            temp_data['person_contract_dirs'] = i.dir_list
            last_contract = i.id
            count += 1
        final_result.append(temp_data.copy())
        res['directions'] = final_result

        return JsonResponse(res)

    if req_status == 6:
        if not pk or pk == -1:
            return JsonResponse(res)

        card = Card.objects.get(pk=pk)
        ecp_id = card.get_ecp_id()

        if not ecp_id:
            return JsonResponse(res)
        patient_time_table = get_ecp_time_table_list_patient(ecp_id)
        patient_direction_time_table = get_ecp_evn_direction(ecp_id)
        patient_time_table.extend(patient_direction_time_table)

        patient_time_table = sorted(patient_time_table, key=lambda k: k["full_time"])
        res['directions'] = [
            {
                'pk': i["time"],
                'status': "",
                'researches': f"{i['Post_name']};-{i['TimeTable_id']}",
                "researches_pks": "",
                'date': i["date"],
                'cancel': False,
                'checked': False,
                'pacs': False,
                'has_hosp': False,
                'has_descriptive': False,
                'maybe_onco': False,
                'is_application': False,
                'isComplex': False,
                'lab': "",
                'parent': parent_obj,
                'is_expertise': False,
                'expertise_status': False,
                'person_contract_pk': "",
                'person_contract_dirs': "",
                'rmis_location': i["rmis_location"],
                'type_slot': i["type_slot"],
                'timeTable_id': i['TimeTable_id'],
            }
            for i in patient_time_table
        ]

        return JsonResponse(res)

    is_service = False
    if services:
        is_service = True

    if not is_service:
        services = [-1]

    is_parent = False
    if iss_pk:
        is_parent = True

    result_sql = get_history_dir(date_start, date_end, patient_card, user_creater, services, is_service, iss_pk, is_parent, for_slave_hosp)
    # napravleniye_id, cancel, iss_id, tubesregistration_id, res_id, res_title, date_create,
    # doc_confirmation_id, time_recive, ch_time_save, podr_title, is_hospital, maybe_onco, can_has_pacs,
    # is_slave_hospital, is_treatment, is_stom, is_doc_refferal, is_paraclinic, is_microbiology, parent_id, study_instance_uid, parent_slave_hosp_id, tube_number
    researches_pks = []
    researches_titles = ''
    child_researches_titles = ''

    last_dir, dir, status, date, cancel, pacs, has_hosp, has_descriptive = None, None, None, None, None, None, None, None
    maybe_onco, is_application, is_expertise, expertise_status, can_has_pacs, isComplex = False, False, False, False, False, False
    parent_obj = {"iss_id": "", "parent_title": "", "parent_is_hosp": "", "parent_is_doc_refferal": "", 'countConfirms': ""}
    person_contract_pk = -1
    status_set = {-2}
    lab = set()
    lab_title = None
    person_contract_dirs, planed_doctor, register_number, rmis_number = "", "", "", ""
    created_document_only_user_hosp = SettingManager.get("created_document_only_user_hosp", default='false', default_type='b')
    user_groups = [str(x) for x in request.user.groups.all()]
    type_service = request_data.get("type_service", None)
    for i in result_sql:
        if created_document_only_user_hosp and i[28] != request.user.doctorprofile.hospital_id and "Направления-все МО" not in user_groups:
            continue
        if i[14]:
            continue
        elif type_service == 'is_paraclinic' and not i[18]:
            continue
        elif type_service == 'is_doc_refferal' and not i[17]:
            continue
        elif type_service == 'is_lab' and (i[11] or i[14] or i[15] or i[16] or i[17] or i[18] or i[19]):
            continue
        elif req_status == 7 and not i[36]:
            continue
        elif i[36] and req_status != 7:
            continue
        if i[0] != last_dir:
            status = min(status_set)
            if len(lab) > 0:
                lab_title = ', '.join(lab)
            aux_researches = []
            has_aux = False
            if status == 2:
                aux_researches_obj = AuxService.objects.filter(main_research__in=researches_pks)
                if aux_researches_obj.exists():
                    aux_researches = [{"pk": i.aux_research.pk, "title": i.aux_research.title} for i in aux_researches_obj]
                    has_aux = True
            if (req_status == 2 and status == 2) or (req_status in [3, 4, 7] and status != -2) or (req_status == 1 and status == 1) or (req_status == 0 and status == 0):
                final_result.append(
                    {
                        'pk': dir,
                        'status': status,
                        'researches': f"{researches_titles} {child_researches_titles}",
                        "researches_pks": researches_pks,
                        "aux_researches": aux_researches,
                        "has_aux": has_aux,
                        'date': date,
                        'cancel': cancel,
                        'checked': False,
                        'pacs': pacs,
                        'can_has_pacs': can_has_pacs,
                        'has_hosp': has_hosp,
                        'has_descriptive': has_descriptive,
                        'maybe_onco': maybe_onco,
                        'is_application': is_application,
                        'isComplex,': False,
                        'lab': lab_title,
                        'parent': parent_obj,
                        'is_expertise': is_expertise,
                        'expertise_status': expertise_status,
                        'person_contract_pk': person_contract_pk,
                        'person_contract_dirs': person_contract_dirs,
                        'planed_doctor': planed_doctor,
                        'register_number': register_number,
                        'rmis_number': rmis_number,
                        'countConfirms': "",
                    }
                )
                child_researches_titles = ""
                person_contract_pk = -1
                person_contract_dirs = ""
                planed_doctor = ""
                register_number = ""
                rmis_number = ""

            dir = i[0]
            expertise_data = get_expertise(dir)
            is_expertise = False
            expertise_status = False
            if expertise_data.get('status') != 'empty':
                is_expertise = True
                expertise_status = 2 if expertise_data.get('status') == 'ok' else 0

            researches_titles = ''
            date = i[6]
            status_set = set()
            researches_pks = []
            pacs = None
            maybe_onco = False
            is_application = False
            isComplex = False
            can_has_pacs = False
            parent_obj = {"iss_id": "", "parent_title": "", "parent_is_hosp": "", "parent_is_doc_refferal": ""}
            if i[13]:
                can_has_pacs = True
                if i[21]:
                    if len(DICOM_SERVERS) > 1:
                        pacs = check_dicom_study_instance_uid(DICOM_SERVERS, i[21])
                    else:
                        pacs = f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={i[21]}'
                else:
                    pacs = None
            has_hosp = False
            if i[11]:
                has_hosp = True
            lab = set()

        if i[36] and req_status == 7:
            case_child_direction = Napravleniya.objects.values_list("pk", flat=True).filter(parent_case__id=i[2])
            case_childs = Issledovaniya.objects.filter(napravleniye_id__in=case_child_direction)
            step = 0
            for csh in case_childs:
                ch_title = csh.research.short_title if csh.research.short_title else csh.research.title
                if step != 0:
                    child_researches_titles = f"{child_researches_titles}; {ch_title}"
                else:
                    child_researches_titles = f"{ch_title}"
                step += 1

        if researches_titles:
            researches_titles = f'{researches_titles} | {i[5]}'
        elif child_researches_titles:
            researches_titles = f'{child_researches_titles} - {i[5]}'
        else:
            researches_titles = i[5]

        child_researches_titles = ""

        status_val = 0
        has_descriptive = False
        if i[8] or i[9] or i[33] or i[34] or i[35]:
            status_val = 1
        if i[7] or i[24]:
            status_val = 2
        if i[1]:
            status_val = -1
        status_set.add(status_val)
        researches_pks.append(i[4])
        if i[12]:
            maybe_onco = True
        if i[20]:
            parent_obj = get_data_parent(i[20])
        last_dir = dir
        cancel = i[1]
        title_podr = i[10]
        if title_podr is None:
            title_podr = ''
        if title_podr not in lab:
            lab.add(title_podr)
        if i[14] or i[15] or i[16] or i[17] or i[18] or i[19] or i[23]:
            has_descriptive = True
        if i[24]:
            is_application = True
        if i[26]:
            person_contract_pk = i[26]
            person_contract_dirs = i[27]
        if i[29]:
            register_number = i[29]
        if i[30]:
            planed_doctor = f"{i[30]} {i[31]} {i[32]}"
        if i[37]:
            rmis_number = i[37]

    status = min(status_set)
    if len(lab) > 0:
        lab_title = ', '.join(lab)
    aux_researches = []
    has_aux = False
    if status == 2:
        aux_researches_obj = AuxService.objects.filter(main_research__in=researches_pks)
        if aux_researches_obj.exists():
            aux_researches = [{"pk": i.aux_research.pk, "title": i.aux_research.title} for i in aux_researches_obj]
            has_aux = True
    if (req_status == 2 and status == 2) or (req_status in [3, 4, 7] and status != -2) or (req_status == 1 and status == 1) or (req_status == 0 and status == 0):
        final_result.append(
            {
                'pk': dir,
                'status': status,
                'researches': f"{researches_titles} {child_researches_titles}",
                "researches_pks": researches_pks,
                "aux_researches": aux_researches,
                "has_aux": has_aux,
                'date': date,
                'cancel': cancel,
                'checked': False,
                'pacs': pacs,
                'can_has_pacs': can_has_pacs,
                'has_hosp': has_hosp,
                'has_descriptive': has_descriptive,
                'maybe_onco': maybe_onco,
                'is_application': is_application,
                'isComplex': isComplex,
                'lab': lab_title,
                'parent': parent_obj,
                'is_expertise': is_expertise,
                'expertise_status': expertise_status,
                'person_contract_pk': person_contract_pk,
                'person_contract_dirs': person_contract_dirs,
                'planed_doctor': planed_doctor,
                'register_number': register_number,
                'rmis_number': rmis_number,
                'countConfirms': "",
            }
        )
    res['directions'] = final_result
    return JsonResponse(res)


def get_data_parent(parent_id):
    iss_obj = Issledovaniya.objects.get(pk=parent_id)
    research_title = iss_obj.research.title
    research_is_hosp = iss_obj.research.is_hospital
    research_is_doc_refferal = iss_obj.research.is_doc_refferal
    direction = iss_obj.napravleniye_id
    is_confirm = False
    if iss_obj.time_confirmation:
        is_confirm = True

    return {
        "iss_id": parent_id,
        "pk": direction,
        "parent_title": research_title,
        "parent_is_hosp": research_is_hosp,
        "parent_is_doc_refferal": research_is_doc_refferal,
        "is_confirm": is_confirm,
    }


@login_required
@group_required("Врач стационара")
def hosp_set_parent(request):
    # SQL-query
    date_end = utils.current_time()
    days_ago = SettingManager.get("days_before_hosp", default='30', default_type='i')
    date_start = date_end + relativedelta(days=-days_ago)
    date_start = datetime.combine(date_start, dtime.min)
    date_end = datetime.combine(date_end, dtime.max)
    request_data = json.loads(request.body)
    patient_card = request_data.get("patient", -1)
    user_creater = -1
    iss_pk = None
    for_slave_hosp = False

    is_service = False
    services = [-1]
    is_parent = False

    result_sql = get_history_dir(date_start, date_end, patient_card, user_creater, services, is_service, iss_pk, is_parent, for_slave_hosp)
    # napravleniye_id, cancel, iss_id, tubesregistration_id, res_id, res_title, date_create,
    # doc_confirmation_id, time_recive, ch_time_save, podr_title, is_hospital, maybe_onco, can_has_pacs,
    # is_slave_hospital, is_treatment, is_stom, is_doc_refferal, is_paraclinic, is_microbiology, parent_id, study_instance_uid, tube_number
    res = {"directions": []}

    for i in result_sql:
        if i[11]:
            if forbidden_edit_dir(i[0]):
                continue
            researche_title = i[5]
            dir = i[0]
            iss_id = i[2]
            date_create = i[6]
            res['directions'].append({'dir_num': dir, 'iss_id': iss_id, 'researche_titles': researche_title, 'date': date_create})

    return JsonResponse(res)


@login_required
@group_required("Врач стационара")
def update_parent(request):
    request_data = json.loads(request.body)
    parent = request_data.get("parent")
    slave_dirs = request_data.get("slave_dirs", [])
    g = [str(x) for x in request.user.groups.all()]
    forbidden = "Управление иерархией истории" not in g

    iss = Issledovaniya.objects.filter(napravleniye__in=slave_dirs)
    for r in iss:
        if r.research.is_hospital and forbidden:
            return JsonResponse({"ok": False, "message": "Нет прав для стационарного изменения"})

    parent_iss = None
    if parent is not None and parent > -1:
        parent_iss = Issledovaniya.objects.get(pk=parent)
        Napravleniya.objects.filter(pk__in=slave_dirs).update(parent=parent_iss)
    if parent == -1:
        Napravleniya.objects.filter(pk__in=slave_dirs).update(parent=None)

    dir_parent = ""
    if parent_iss:
        dir_parent = parent_iss.napravleniye.pk

    for i in slave_dirs:
        Log(key=i, type=5003, body=json.dumps({"dir": i, "parent_dir": dir_parent, "parent_iss_id": parent}), user=request.user.doctorprofile).save()

    return JsonResponse({"ok": True, "message": ""})


@login_required
def directions_rmis_directions(request):
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    rows = []
    if pk and Card.objects.filter(pk=pk, base__is_rmis=True).exists():
        c = Client(modules=["directions", "services"])
        sd = c.directions.get_individual_active_directions(Card.objects.get(pk=pk).number)
        dirs_data = [c.directions.get_direction_full_data(x) for x in sd if not Napravleniya.objects.filter(rmis_number=x).exists()]
        rows = [x for x in dirs_data if x]
    return JsonResponse({"rows": rows})


@login_required
def directions_rmis_direction(request):
    request_data = json.loads(request.body)
    data = {}
    pk = request_data.get("pk")
    if pk and not Napravleniya.objects.filter(rmis_number=pk).exists():
        data = get_direction_full_data_cache(pk)
        if not data:
            c = Client(modules=["directions", "services"])
            data = c.directions.get_direction_full_data(pk)
    return JsonResponse(data)


@login_required
def directions_cancel(request):
    response = {"cancel": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    response["forbidden"] = False
    default_cancel_direction = SettingManager.get("default_cancel_direction", default='true', default_type='b')
    user_groups = [str(x) for x in request.user.groups.all()]
    if not default_cancel_direction and "Отмена направлений" not in user_groups:
        response["forbidden"] = True
    elif Napravleniya.objects.filter(pk=pk).exists():
        direction = Napravleniya.objects.get(pk=pk)
        direction.cancel = not direction.cancel
        direction.save()
        response["cancel"] = direction.cancel
        Log(key=pk, type=5002, body="да" if direction.cancel else "нет", user=request.user.doctorprofile).save()
    return JsonResponse(response)


@login_required
def directions_results(request):
    result = {"ok": False, "desc": False, "direction": {"pk": -1, "doc": "", "date": ""}, "client": {}, "full": False}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if Napravleniya.objects.filter(pk=pk).exists():
        napr = Napravleniya.objects.get(pk=pk)
        dates = {}
        for iss in Issledovaniya.objects.filter(napravleniye=napr):
            if iss.research.desc:
                result["desc"] = True
                if not request_data.get("force", False):
                    return JsonResponse(result)
        for iss in Issledovaniya.objects.filter(napravleniye=napr, time_save__isnull=False):
            if iss.time_save:
                dt = str(dateformat.format(iss.time_save, settings.DATE_FORMAT))
                if dt not in dates.keys():
                    dates[dt] = 0
                dates[dt] += 1

        maxdate = ""
        if dates != {}:
            maxdate = max(dates.items(), key=operator.itemgetter(1))[0]
        else:
            iss = Issledovaniya.objects.filter(napravleniye=napr)[0]
            if iss.time_confirmation:
                maxdate = str(dateformat.format(iss.time_confirmation, settings.DATE_FORMAT))

        iss_list = Issledovaniya.objects.filter(napravleniye=napr)
        t = 0
        if not iss_list.filter(time_confirmation__isnull=True).exists() or iss_list.filter(deferred=False).exists():
            result["direction"]["pk"] = napr.pk
            result["full"] = False
            result["ok"] = True
            result["pacs"] = None if not iss_list[0].research.podrazdeleniye or not iss_list[0].research.podrazdeleniye.can_has_pacs else search_dicom_study(pk)
            if iss_list.filter(time_confirmation__isnull=False).exists():
                result["direction"]["doc"] = iss_list.filter(time_confirmation__isnull=False)[0].doc_confirmation_fio
                if iss_list.filter(time_confirmation__isnull=True, deferred=False).exists():
                    result["direction"]["doc"] = result["direction"]["doc"] + " (выполнено не полностью)"
                else:
                    result["full"] = True
            else:
                result["direction"]["doc"] = "Не подтверждено"
            result["direction"]["date"] = maxdate

            result["client"]["sex"] = napr.client.individual.sex
            result["client"]["fio"] = napr.client.individual.fio()
            result["client"]["age"] = napr.client.individual.age_s(direction=napr)
            result["client"]["cardnum"] = napr.client.number_with_type()
            result["client"]["dr"] = napr.client.individual.bd()

            result["results"] = collections.OrderedDict()
            isses = []
            for issledovaniye in iss_list.order_by("tubes__number", "research__sort_weight"):
                if issledovaniye.pk in isses:
                    continue
                isses.append(issledovaniye.pk)
                t += 1
                kint = "%s_%s_%s_%s" % (
                    t,
                    "-1" if not issledovaniye.research.direction else issledovaniye.research.direction_id,
                    issledovaniye.research.sort_weight,
                    issledovaniye.research_id,
                )
                result["results"][kint] = {"title": issledovaniye.research.title, "fractions": collections.OrderedDict(), "sort": issledovaniye.research.sort_weight, "tube_time_get": ""}
                if not issledovaniye.deferred or issledovaniye.time_confirmation:
                    for isstube in issledovaniye.tubes.all():
                        if isstube.time_get:
                            result["results"][kint]["tube_time_get"] = str(dateformat.format(isstube.time_get_local, settings.DATE_FORMAT))
                            break

                    results = Result.objects.filter(issledovaniye=issledovaniye).order_by("fraction__sort_weight")  # Выборка результатов из базы

                    n = 0
                    for res in results:  # Перебор результатов
                        pk = res.fraction.sort_weight
                        if not pk or pk <= 0:
                            pk = res.fraction_id
                        if res.fraction.render_type == 0:
                            if pk not in result["results"][kint]["fractions"].keys():
                                result["results"][kint]["fractions"][pk] = {}

                            result["results"][kint]["fractions"][pk]["result"] = result_normal(res.value)
                            result["results"][kint]["fractions"][pk]["title"] = res.fraction.title
                            result["results"][kint]["fractions"][pk]["units"] = res.get_units()
                            refs = res.get_ref(full=True)
                            ref_m = refs["m"]
                            ref_f = refs["f"]
                            if isinstance(ref_m, str):
                                ref_m = json.loads(ref_m)
                            if isinstance(ref_f, str):
                                ref_f = json.loads(ref_f)
                            result["results"][kint]["fractions"][pk]["ref_m"] = ref_m
                            result["results"][kint]["fractions"][pk]["ref_f"] = ref_f
                        else:
                            try:
                                tmp_results = json.loads("{}" if not res.value else res.value).get("rows", {})
                            except Exception:
                                tmp_results = {}

                            n = 0
                            for row in tmp_results.values():
                                n += 1
                                tmp_pk = "%d_%d" % (pk, n)
                                if tmp_pk not in result["results"][kint]["fractions"].keys():
                                    result["results"][kint]["fractions"][tmp_pk] = {}
                                result["results"][kint]["fractions"][tmp_pk]["title"] = "Выделенная культура"
                                result["results"][kint]["fractions"][tmp_pk]["result"] = row["title"]
                                result["results"][kint]["fractions"][tmp_pk]["ref_m"] = {}
                                result["results"][kint]["fractions"][tmp_pk]["ref_f"] = {}
                                result["results"][kint]["fractions"][tmp_pk]["units"] = ""
                                for subrow in row["rows"].values():
                                    if "null" in subrow["value"]:
                                        continue
                                    n += 1
                                    tmp_pk = "%d_%d" % (pk, n)
                                    if tmp_pk not in result["results"][kint]["fractions"].keys():
                                        result["results"][kint]["fractions"][tmp_pk] = {}
                                    result["results"][kint]["fractions"][tmp_pk]["title"] = subrow["title"]
                                    result["results"][kint]["fractions"][tmp_pk]["result"] = subrow["value"]
                                    result["results"][kint]["fractions"][tmp_pk]["ref_m"] = {}
                                    result["results"][kint]["fractions"][tmp_pk]["ref_f"] = {}
                                    result["results"][kint]["fractions"][tmp_pk]["units"] = ""

                            n += 1
                            tmp_pk = "%d_%d" % (pk, n)
                            if tmp_pk not in result["results"][kint]["fractions"].keys():
                                result["results"][kint]["fractions"][tmp_pk] = {}
                            result["results"][kint]["fractions"][tmp_pk]["title"] = "S - чувствителен; R - резистентен; I - промежуточная чувствительность;"
                            result["results"][kint]["fractions"][tmp_pk]["result"] = ""
                            result["results"][kint]["fractions"][tmp_pk]["ref_m"] = {}
                            result["results"][kint]["fractions"][tmp_pk]["ref_f"] = {}
                            result["results"][kint]["fractions"][tmp_pk]["units"] = ""
                    if issledovaniye.lab_comment and issledovaniye.lab_comment != "":
                        n += 1
                        tmp_pk = "%d_%d" % (pk, n)
                        if tmp_pk not in result["results"][kint]["fractions"].keys():
                            result["results"][kint]["fractions"][tmp_pk] = {}
                        result["results"][kint]["fractions"][tmp_pk]["title"] = "Комментарий"
                        result["results"][kint]["fractions"][tmp_pk]["result"] = issledovaniye.lab_comment.replace("\n", "<br/>")
                        result["results"][kint]["fractions"][tmp_pk]["ref_m"] = {}
                        result["results"][kint]["fractions"][tmp_pk]["ref_f"] = {}
                        result["results"][kint]["fractions"][tmp_pk]["units"] = ""
                else:
                    fr_list = Fractions.objects.filter(research=issledovaniye.research)
                    for fr in fr_list:
                        pk = fr.sort_weight
                        if not pk or pk <= 0:
                            pk = fr.pk
                        if pk not in result["results"][kint]["fractions"].keys():
                            result["results"][kint]["fractions"][pk] = {}

                        result["results"][kint]["fractions"][pk]["result"] = "отложен"  # Значение
                        result["results"][kint]["fractions"][pk]["title"] = fr.title  # Название фракции
                        result["results"][kint]["fractions"][pk]["units"] = fr.get_unit_str()  # Еденицы измерения
                        ref_m = {"": ""}  # fr.ref_m
                        ref_f = {"": ""}  # fr.ref_f
                        if not isinstance(ref_m, str):
                            ref_m = json.loads(ref_m)
                        if not isinstance(ref_f, str):
                            ref_f = json.loads(ref_f)
                        result["results"][kint]["fractions"][pk]["ref_m"] = ref_m  # Референсы М
                        result["results"][kint]["fractions"][pk]["ref_f"] = ref_f  # Референсы Ж

    return JsonResponse(result)


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_services(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    f = False
    dn = Napravleniya.objects.filter(pk=pk)
    if dn.exists():
        n = dn[0]
        if Issledovaniya.objects.filter(
            Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True) | Q(research__is_microbiology=True) | Q(research__is_citology=True) | Q(research__is_gistology=True)
        ).exists():
            cdid, ctime, ctp, rt = get_reset_time_vars(n)

            response["ok"] = True
            researches = []
            has_microbiology = False
            has_gistology = False
            receive_datetime = None
            for i in (
                Issledovaniya.objects.filter(napravleniye=n)
                .filter(
                    Q(research__is_paraclinic=True) | Q(research__is_doc_refferal=True) | Q(research__is_microbiology=True) | Q(research__is_citology=True) | Q(research__is_gistology=True)
                )
                .distinct()
            ):
                researches.append(
                    {
                        "pk": i.pk,
                        "title": i.research.title,
                        "department": "" if not i.research.podrazdeleniye else i.research.podrazdeleniye.get_title(),
                        "is_microbiology": i.research.is_microbiology,
                        "comment": i.localization.title if i.localization else i.comment,
                        "tube": {"title": i.research.microbiology_tube.title, "color": i.research.microbiology_tube.color, "pk": i.pk} if i.research.is_microbiology else None,
                    }
                )
                if i.research.is_microbiology:
                    has_microbiology = True
                if i.research.is_gistology:
                    has_gistology = True

            if has_microbiology:
                receive_datetime = None if not n.time_microbiology_receive else strdatetime(n.time_microbiology_receive)

            gistology_receive_time = None
            if has_gistology and n.time_gistology_receive:
                gistology_receive_time = strfdatetime(n.time_gistology_receive, '%Y-%m-%dT%X')

            response["direction_data"] = {
                "date": strdate(n.data_sozdaniya),
                "client": n.client.individual.fio(full=True),
                "card": n.client.number_with_type(),
                "diagnos": n.diagnos,
                "has_microbiology": has_microbiology,
                "has_gistology": has_gistology,
                "receive_datetime": receive_datetime,
                "gistology_receive_time": gistology_receive_time,
                "doc": "" if not n.doc else "{}, {}".format(n.doc.get_fio(), n.doc.podrazdeleniye.title),
                "imported_from_rmis": n.imported_from_rmis,
                "imported_org": "" if not n.imported_org else n.imported_org.title,
                "visit_who_mark": "" if not n.visit_who_mark else "{}, {}".format(n.visit_who_mark.get_fio(), n.visit_who_mark.podrazdeleniye.title),
                "fin_source": "" if not n.istochnik_f else "{} - {}".format(n.istochnik_f.base.title, n.istochnik_f.title),
                "priceCategory": "" if not n.price_category else n.price_category.title,
                "coExecutor": n.co_executor_id,
                "additionalNumber": n.register_number,
                "additionalNumberYear": n.register_number_year,
                "planedDoctorExecutor": n.planed_doctor_executor_id,
            }
            response["researches"] = researches
            response["loaded_pk"] = pk
            response["visit_status"] = n.visit_date is not None
            response["visit_date"] = "" if not n.visit_date else strdatetime(n.visit_date)
            response["allow_reset_confirm"] = bool(
                (
                    (ctime - ctp < rt and cdid == request.user.doctorprofile.pk)
                    or request.user.is_superuser
                    or "Сброс подтверждений результатов" in [str(x) for x in request.user.groups.all()]
                    or "Отмена регистрации" in [str(x) for x in request.user.groups.all()]
                )
                and n.visit_date
            )
            f = True
    if not f:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_mark_visit(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    cancel = request_data.get("cancel", False)
    co_executor = request_data.get("coExecutor", None)
    planed_doctor_executor = request_data.get("planedDoctorExecutor", None)
    register_number = request_data.get("additionalNumber", '')
    register_number_year = request_data.get("additionalNumberYear") or None
    gistology_receive_time = request_data.get("gistologyReceiveTime") or None
    visit_date = request_data.get("visitDate") or None
    if visit_date:
        visit_date = f"{visit_date}.000113"

    dn = Napravleniya.objects.filter(pk=pk)
    f = False
    if dn.exists():
        n = dn[0]
        if register_number and n.register_number != register_number:
            if Napravleniya.objects.filter(register_number=register_number, register_number_year=register_number_year).exclude(pk=pk).exists():
                response["message"] = f'Номер "{register_number}" уже занят'
                return JsonResponse(response)
            n.register_number = register_number
            n.register_number_year = register_number_year
            n.save(update_fields=['register_number', 'register_number_year'])
        if co_executor and n.co_executor_id != co_executor:
            n.co_executor_id = co_executor
            n.save(update_fields=['co_executor_id'])
        if planed_doctor_executor and n.planed_doctor_executor_id != planed_doctor_executor:
            n.planed_doctor_executor_id = planed_doctor_executor
            n.save(update_fields=['planed_doctor_executor_id'])
        has_gistology = Issledovaniya.objects.filter(napravleniye_id=pk, research__is_gistology=True).exists()

        if not cancel:
            if has_gistology:
                current_gistology_time = None if not n.time_gistology_receive else strfdatetime(n.time_gistology_receive, '%Y-%m-%dT%X')
                if current_gistology_time != gistology_receive_time:
                    n.doc_gistology_receive = request.user.doctorprofile
                    n.time_gistology_receive = try_strptime(gistology_receive_time, ('%Y-%m-%dT%X',))
                    Log.log(
                        n.pk,
                        122000,
                        request.user.doctorprofile,
                        {
                            'gistology_receive_time': gistology_receive_time,
                        },
                    )
            if visit_date and has_gistology:
                n.visit_date = replace_tz(try_strptime(visit_date, ('%Y-%m-%dT%H:%M:%S.%f',)))
            else:
                n.visit_date = timezone.now()
            n.visit_who_mark = request.user.doctorprofile
            n.save()
            cdid, ctime, ctp, rt = get_reset_time_vars(n)
            allow_reset_confirm = bool(
                (
                    (ctime - ctp < rt and cdid == request.user.doctorprofile.pk)
                    or request.user.is_superuser
                    or "Сброс подтверждений результатов" in [str(x) for x in request.user.groups.all()]
                )
                and n.visit_date
            )
            response["visit_status"] = n.visit_date is not None
            response["visit_date"] = strdatetime(n.visit_date)
            response["allow_reset_confirm"] = allow_reset_confirm
            response["ok"] = True
        else:
            ctp = int(0 if not n.visit_date else int(time.mktime(timezone.localtime(n.visit_date).timetuple())))
            ctime = int(time.time())
            cdid = -1 if not n.visit_who_mark else n.visit_who_mark_id
            rtm = SettingManager.get("visit_reset_time_min", default="20.0", default_type='f')
            rt = rtm * 60
            allow_reset_confirm = bool(
                (
                    (ctime - ctp < rt and cdid == request.user.doctorprofile.pk)
                    or request.user.is_superuser
                    or "Сброс подтверждений результатов" in [str(x) for x in request.user.groups.all()]
                    or "Отмена регистрации" in [str(x) for x in request.user.groups.all()]
                )
                and n.visit_date
                and not n.has_confirm()
            )
            if allow_reset_confirm:
                response["ok"] = True
                response["visit_status"] = None
                response["visit_date"] = ''
                response["allow_reset_confirm"] = False
                n.visit_date = None
                n.visit_who_mark = None
                n.save()
            elif n.has_confirm():
                response["message"] = 'Отмена посещения возможна только после "Сброса подтверждения"'
            else:
                response["message"] = "Отмена посещения возможна только в течении {} мин.".format(rtm)
            f = True
        if allow_reset_confirm or not cancel:
            log_data = {
                "Посещение": "отмена" if cancel else "да",
                "Дата и время": response["visit_date"],
                "Дополнительный номер": register_number,
                "Год": register_number_year,
                "Со-исполнитель": co_executor,
            }
            Log(key=pk, type=5001, body=json.dumps(log_data), user=request.user.doctorprofile).save()
            f = True
    if not f:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def clear_register_number(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    register_number = request_data.get("additionalNumber", '')
    register_number_year = request_data.get("additionalNumberYear", None)
    dn = Napravleniya.objects.filter(pk=pk)
    if dn.exists():
        n = dn[0]
        if n.register_number == register_number and n.register_number_year == register_number_year:
            n.register_number = ""
            n.save()
            response["message"] = f'Номер "{register_number}" освобожден'
            response["ok"] = True
        else:
            response["message"] = f'Номер "{register_number}" принадлежит другому направлению'

    return JsonResponse(response)


@group_required("Получатель биоматериала микробиологии")
def directions_receive_material(request):
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1)
    cancel = request_data.get("cancel", False)
    dn = Napravleniya.objects.filter(pk=pk)
    f = False
    if dn.exists():
        n = dn[0]
        if not cancel:
            if not n.time_microbiology_receive:
                n.time_microbiology_receive = timezone.now()
                n.doc_microbiology_receive = request.user.doctorprofile
                n.save()
                response["ok"] = True
                response["receive_datetime"] = strdatetime(n.time_microbiology_receive)
            else:
                response["message"] = "Материал уже принят"
        else:
            n.time_microbiology_receive = None
            n.doc_microbiology_receive = None
            n.save()
            response["ok"] = True
            response["receive_datetime"] = None
        f = True
    if not f:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_visit_journal(request):
    response = {"data": []}
    request_data = json.loads(request.body)
    date_start, date_end = try_parse_range(request_data["date"])
    for v in Napravleniya.objects.filter(
        visit_date__range=(
            date_start,
            date_end,
        ),
        visit_who_mark=request.user.doctorprofile,
    ).order_by("-visit_date"):
        response["data"].append(
            {"pk": v.pk, "additionalNumber": v.register_number, "client": v.client.individual.fio(full=True), "card": v.client.number_with_type(), "datetime": strdatetime(v.visit_date)}
        )
    return JsonResponse(response)


@group_required("Врач параклиники", "Посещения по направлениям", "Врач консультаций")
def directions_recv_journal(request):
    response = {"data": []}
    request_data = json.loads(request.body)
    date_start, date_end = try_parse_range(request_data["date"])
    for v in Napravleniya.objects.filter(
        time_microbiology_receive__range=(
            date_start,
            date_end,
        ),
        doc_microbiology_receive=request.user.doctorprofile,
    ).order_by("-time_microbiology_receive"):
        tubes = []
        for i in Issledovaniya.objects.filter(napravleniye=v, research__microbiology_tube__isnull=False):
            tube = i.research.microbiology_tube
            tubes.append(
                {
                    "color": tube.color,
                    "title": tube.title,
                }
            )
        response["data"].append(
            {
                "pk": v.pk,
                "client": v.client.individual.fio(full=True),
                "datetime": strdatetime(v.time_microbiology_receive),
                "tubes": tubes,
            }
        )
    return JsonResponse(response)


@login_required
def directions_last_result(request):
    response = {"ok": False, "data": {}, "type": "result", "has_last_result": False}
    request_data = json.loads(request.body)
    individual = request_data.get("individual", -1)
    research = request_data.get("research", -1)
    parent_iss = request_data.get("parentIss", None)
    filter = {
        "napravleniye__client__individual__pk": individual,
        "research__pk": research,
    }
    if parent_iss:
        filter["napravleniye__parent__pk"] = parent_iss
    i = Issledovaniya.objects.filter(**filter, time_confirmation__isnull=False).order_by("-time_confirmation").first()
    u = Issledovaniya.objects.filter(**filter, time_confirmation__isnull=True).order_by("-napravleniye__data_sozdaniya").first()
    v = (
        Issledovaniya.objects.filter(**filter, research__is_paraclinic=True, time_confirmation__isnull=True, napravleniye__visit_date__isnull=False)
        .order_by("-napravleniye__visit_date")
        .first()
    )
    if i:
        if not u or i.time_confirmation >= u.napravleniye.data_sozdaniya:
            response["ok"] = True
            if v and v.napravleniye.visit_date > i.time_confirmation:
                response["type"] = "visit"
                response["data"] = {"direction": u.napravleniye_id, "datetime": strdate(v.napravleniye.visit_date), "is_desc": i.research.desc, "ts": tsdatetime(v.napravleniye.visit_date)}
                response["has_last_result"] = True
                response["last_result"] = {
                    "direction": i.napravleniye_id,
                    "datetime": strdate(i.time_confirmation),
                    "ts": tsdatetime(i.time_confirmation),
                    "is_desc": i.research.desc,
                    "is_doc_referral": i.research.is_doc_referral,
                    "is_paraclinic": i.research.is_paraclinic,
                }
            else:
                response["data"] = {
                    "direction": i.napravleniye_id,
                    "datetime": strdate(i.time_confirmation),
                    "is_desc": i.research.desc,
                    "is_doc_referral": i.research.is_doc_referral,
                    "ts": tsdatetime(i.time_confirmation),
                    "is_paraclinic": i.research.is_paraclinic,
                }
        elif u:
            response["ok"] = True
            if v and v.napravleniye.visit_date > u.napravleniye.data_sozdaniya:
                response["type"] = "visit"
                response["data"] = {"direction": u.napravleniye_id, "datetime": strdate(v.napravleniye.visit_date), "is_desc": i.research.desc, "ts": tsdatetime(v.napravleniye.visit_date)}
            else:
                response["type"] = "direction"
                response["data"] = {
                    "direction": u.napravleniye_id,
                    "datetime": strdate(u.napravleniye.data_sozdaniya),
                    "is_desc": i.research.desc,
                    "ts": tsdatetime(u.napravleniye.data_sozdaniya),
                }
            response["has_last_result"] = True
            response["last_result"] = {
                "direction": i.napravleniye_id,
                "datetime": strdate(i.time_confirmation),
                "is_doc_referral": i.research.is_doc_referral,
                "ts": tsdatetime(i.time_confirmation),
                "is_paraclinic": i.research.is_paraclinic,
            }
    elif u:
        response["ok"] = True
        if v and v.napravleniye.visit_date > u.napravleniye.data_sozdaniya:
            response["type"] = "visit"
            response["data"] = {"direction": u.napravleniye_id, "datetime": strdate(v.napravleniye.visit_date), "ts": tsdatetime(v.napravleniye.visit_date)}
        else:
            response["type"] = "direction"
            response["data"] = {"direction": u.napravleniye_id, "datetime": strdate(u.napravleniye.data_sozdaniya), "ts": tsdatetime(u.napravleniye.data_sozdaniya)}
    return JsonResponse(response)


@login_required
def directions_results_report(request):
    import re

    data = []
    request_data = json.loads(request.body)
    individual_pk = request_data.get("individual", -1)
    Log(key=str(individual_pk), type=20000, body=json.dumps(request_data), user=request.user.doctorprofile).save()
    params = request_data.get("params", [])

    date_start, date_end = try_parse_range(request_data.get("date_start"), request_data.get("date_end"))

    if Individual.objects.filter(pk=individual_pk).exists():
        i = Individual.objects.get(pk=individual_pk)
        for param in params:
            ppk = param["pk"]
            if param["is_paraclinic"]:
                if ParaclinicInputGroups.objects.filter(pk=ppk).exists():
                    g = ParaclinicInputGroups.objects.get(pk=ppk)
                    for i in Issledovaniya.objects.filter(research__paraclinicinputgroups=g, time_confirmation__isnull=False):
                        res = []
                        for r in ParaclinicResult.objects.filter(field__group=g, issledovaniye=i).order_by("field__order"):
                            if r.value == "":
                                continue
                            res.append((r.field.get_title(force_type=r.get_field_type()) + ": " if r.field.get_title(force_type=r.get_field_type()) != "" else "") + r.value)

                        if len(res) == 0:
                            continue

                        paramdata = {
                            "research": i.research_id,
                            "pk": ppk,
                            "order": g.order,
                            "date": strdate(i.time_confirmation),
                            "timestamp": tsdatetime(i.time_confirmation),
                            "value": "; ".join(res),
                            "units": "",
                            "is_norm": "normal",
                            "not_norm_dir": "",
                            # "delta": 0,
                            "active_ref": None,
                            "direction": i.napravleniye_id,
                        }
                        data.append(paramdata)
            else:
                if Fractions.objects.filter(pk=ppk).exists():
                    f = Fractions.objects.get(pk=ppk)
                    for r in Result.objects.filter(issledovaniye__napravleniye__client__individual=i, fraction=f, issledovaniye__time_confirmation__range=(date_start, date_end)):
                        if r.value == "":
                            continue
                        is_norm, ref_sign = r.get_is_norm()
                        not_norm_dir = ""
                        # delta = ""
                        active_ref = r.calc_normal(fromsave=False, only_ref=True)
                        if isinstance(active_ref, str) and re.match(r"^\d+(\.\d+)?$", r.value.replace(",", ".").strip()):
                            # x = float(r.value.replace(",", ".").strip())
                            r1, r2 = r.calc_normal(fromsave=False, only_ref=False)

                            if r1 and r2:
                                if r1 == 'not_normal':
                                    not_norm_dir = {'<': "n_down", ">": "n_up"}.get(r2, "")
                                # if spl[0] >= x:
                                #     not_norm_dir = "down"
                                #     nx = spl[0] - x
                                #     n10 = spl[0] * 0.2
                                #     if nx <= n10:
                                #         not_norm_dir = "n_down"
                                #     delta = nx
                                # elif spl[1] <= x:
                                #     not_norm_dir = "up"
                                #     nx = x - spl[1]
                                #     n10 = spl[1] * 0.2
                                #     if nx <= n10:
                                #         not_norm_dir = "n_up"
                                #     delta = nx

                        paramdata = {
                            "research": f.research_id,
                            "pk": ppk,
                            "order": f.sort_weight,
                            "date": strdate(r.issledovaniye.time_confirmation),
                            "timestamp": tsdatetime(r.issledovaniye.time_confirmation),
                            "value": r.value,
                            "units": r.get_units(),
                            "is_norm": is_norm,
                            "not_norm_dir": not_norm_dir,
                            # "delta": delta,
                            "active_ref": active_ref,
                            "direction": r.issledovaniye.napravleniye_id,
                        }
                        data.append(paramdata)
    data.sort(key=itemgetter("timestamp"), reverse=True)
    data.sort(key=itemgetter("pk"))
    data.sort(key=itemgetter("order"))
    data.sort(key=itemgetter("research"))
    return JsonResponse({"data": data})


@group_required("Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p", "Заполнение мониторингов", "Свидетельство о смерти-доступ")
def directions_paraclinic_form(request):
    TADP = SettingManager.get("tadp", default='Температура', default_type='s')
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("pk", -1) or -1
    search_mode = request_data.get("searchMode", 'direction')
    force_form = request_data.get("force", False)
    without_issledovaniye = request_data.get("withoutIssledovaniye", None)
    if isinstance(pk, int) and pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    add_fr = {}
    f = False
    doc_department_id = request.user.doctorprofile.podrazdeleniye_id
    user_groups = [str(x) for x in request.user.groups.all()]
    is_without_limit_paraclinic = "Параклиника без ограничений" in user_groups
    if not request.user.is_superuser and not is_without_limit_paraclinic:
        add_fr = dict(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)

    if search_mode == 'mk':
        if Issledovaniya.objects.filter(pk=pk, research__is_microbiology=True).exists():
            pk = Issledovaniya.objects.get(pk=pk).napravleniye_id
        else:
            pk = -1
    elif search_mode == 'additional':
        register_year = request_data.get("year")
        if Napravleniya.objects.filter(register_number=pk, register_number_year=register_year).exists():
            pk = Napravleniya.objects.filter(register_number=pk, register_number_year=register_year)[0].pk
        else:
            pk = -1
    dn = (
        Napravleniya.objects.filter(pk=pk)
        .select_related('client', 'client__base', 'client__individual', 'doc', 'doc__podrazdeleniye', 'doc__hospital', 'hospital')
        .prefetch_related(
            Prefetch(
                'issledovaniya_set',
                queryset=(
                    Issledovaniya.objects.all()
                    if force_form
                    else Issledovaniya.objects.filter(
                        Q(research__is_paraclinic=True, **add_fr)
                        | Q(research__is_doc_refferal=True)
                        | Q(research__is_treatment=True)
                        | Q(research__is_stom=True)
                        | Q(research__is_microbiology=True)
                        | Q(research__is_citology=True)
                        | Q(research__is_gistology=True)
                        | Q(research__is_form=True)
                        | Q(research__is_monitoring=True)
                        | Q(research__is_expertise=True)
                        | Q(research__is_aux=True)
                        | Q(research__is_case=True)
                    )
                )
                .select_related('research', 'research__microbiology_tube', 'research__podrazdeleniye')
                .prefetch_related(
                    Prefetch(
                        'research__paraclinicinputgroups_set',
                        queryset=ParaclinicInputGroups.objects.filter(hide=False)
                        .order_by("order")
                        .prefetch_related(Prefetch('paraclinicinputfield_set', queryset=ParaclinicInputField.objects.filter(hide=False).order_by("order"))),
                    ),
                    Prefetch('recipe_set', queryset=Recipe.objects.all().order_by('pk')),
                )
                .distinct(),
            )
        )
    )
    d = None
    if dn.exists():
        d: Napravleniya = dn[0]
        if SettingManager.get("control_planed_fact_doctor", default='false', default_type='b') and d.planed_doctor_executor != request.user.doctorprofile:
            if not request.user.is_superuser and not is_without_limit_paraclinic:
                response["message"] = "Направление для другого Врача"
                return JsonResponse(response)
        all_confirmed = d.is_all_confirm()
        if (
            SettingManager.get("control_visit_gistology", default='false', default_type='b')
            and not all_confirmed
            and d.research().is_gistology
            and (d.visit_date is None or d.register_number is None)
        ):
            response["message"] = "Отсутствует дата регистрации"
            return JsonResponse(response)
        if SettingManager.get("control_time_gistology_receive", default='false', default_type='b') and not all_confirmed and d.research().is_gistology and d.time_gistology_receive is None:
            response["message"] = "Отсутствует дата приема"
            return JsonResponse(response)

        df = d.issledovaniya_set.all()
        if df.exists():
            response["ok"] = True
            response["has_doc_referral"] = False
            response["has_expertise"] = False
            response["has_paraclinic"] = False
            response["has_microbiology"] = False
            response["has_citology"] = False
            response["has_gistology"] = False
            response["has_monitoring"] = False
            response["card_internal"] = d.client.base.internal_type
            response["hospital_title"] = d.hospital_title
            card_documents = d.client.get_card_documents(check_has_type=['СНИЛС'])

            has_snils = bool(card_documents)
            response["patient"] = {
                "fio_age": d.client.individual.fio(full=True),
                "fio": d.client.individual.fio(),
                "age": d.client.individual.age(),
                "sex": d.client.individual.sex.lower(),
                "card": d.client.number_with_type(),
                "card_pk": d.client_id,
                "pk": d.client_id,
                "individual_pk": d.client.individual_id,
                "has_dreg": DispensaryReg.objects.filter(date_end__isnull=True, card=d.client).exists(),
                "has_benefit": BenefitReg.objects.filter(date_end__isnull=True, card=d.client).exists(),
                "doc": "" if not d.doc else (d.doc.get_fio(dots=True) + ", " + d.doc.podrazdeleniye.title),
                "imported_from_rmis": d.imported_from_rmis,
                "imported_org": "" if not d.imported_org else d.imported_org.title,
                "base": d.client.base_id,
                "main_diagnosis": d.client.main_diagnosis,
                "has_snils": has_snils,
            }
            response["showExaminationDate"] = SHOW_EXAMINATION_DATE_IN_PARACLINIC_RESULT_PAGE

            hospital_tfoms_code = d.get_hospital_tfoms_id()
            date = strdateru(d.data_sozdaniya)
            response["direction"] = {
                "pk": d.pk,
                "date": date,
                "all_confirmed": all_confirmed,
                "diagnos": d.diagnos,
                "fin_source": d.fin_title,
                "fin_source_id": d.istochnik_f_id,
                "priceCategory": "" if not d.price_category else d.price_category.title,
                "priceCategoryId": "" if not d.price_category else d.price_category.pk,
                "additionalNumber": d.register_number,
                "additionalNumberYear": d.register_number_year,
                "timeGistologyReceive": strdatetimeru(d.time_gistology_receive),
                "coExecutor": d.co_executor_id,
                "tube": None,
                "amd": d.amd_status,
                "amd_number": d.amd_number,
                "hospitalTFOMSCode": hospital_tfoms_code,
            }

            response["researches"] = []
            tube = None
            medical_certificates = []
            tmp_certificates = []
            i: Issledovaniya
            for i in df:
                if i.research.is_doc_refferal:
                    response["has_doc_referral"] = True
                if i.research.is_expertise:
                    response["has_expertise"] = True
                if i.research.is_paraclinic or i.research.is_citology or i.research.is_gistology:
                    response["has_paraclinic"] = True
                if i.research.is_microbiology:
                    response["has_microbiology"] = True
                if i.research.is_citology:
                    response["has_citology"] = True
                if i.research.is_gistology:
                    response["has_gistology"] = True
                if i.research.is_monitoring:
                    response["has_monitoring"] = True
                if i.research.microbiology_tube:
                    tube = {
                        "type": i.research.microbiology_tube.title,
                        "color": i.research.microbiology_tube.color,
                        "get": i.get_visit_date(force=True),
                        "n": d.microbiology_n,
                        "pk": i.pk,
                    }
                transfer_d = Napravleniya.objects.filter(parent_auto_gen=i, cancel=False).first()
                forbidden_edit = forbidden_edit_dir(d.pk)
                more_forbidden = "Врач параклиники" not in user_groups and "Врач консультаций" not in user_groups and "Врач стационара" not in user_groups and "t, ad, p" in user_groups
                cert_researches = ResearchesCertificate.objects.filter(research=i.research)
                general_certificate = MedicalCertificates.objects.filter(general=True)
                for cert in cert_researches:
                    if cert.medical_certificate.certificate_form not in tmp_certificates:
                        tmp_certificates.append(cert.medical_certificate.certificate_form)
                        medical_certificates.append({"form": cert.medical_certificate.certificate_form, "title": cert.medical_certificate.title})
                for cert in general_certificate:
                    medical_certificates.append({"form": cert.certificate_form, "title": cert.title})

                iss = {
                    "pk": i.pk,
                    "amd": d.amd_status,
                    "amd_number": d.amd_number,
                    "direction_pk": d.pk,
                    "research": {
                        "pk": i.research_id,
                        "title": i.research.title,
                        "version": i.pk * 10000,
                        "is_paraclinic": i.research.is_paraclinic or i.research.is_citology or i.research.is_gistology,
                        "is_doc_refferal": i.research.is_doc_refferal,
                        "is_gistology": i.research.is_gistology,
                        "is_microbiology": i.research.is_microbiology,
                        "is_treatment": i.research.is_treatment,
                        "is_stom": i.research.is_stom,
                        "isAux": i.research.is_aux,
                        "is_monitoring": i.research.is_monitoring,
                        "wide_headers": i.research.wide_headers,
                        "comment": i.localization.title if i.localization else i.comment,
                        "groups": [],
                        "can_transfer": i.research.can_transfer,
                        "is_extract": i.research.is_extract,
                        "transfer_direction": None if not transfer_d else transfer_d.pk,
                        "transfer_direction_iss": [] if not transfer_d else [r.research.title for r in Issledovaniya.objects.filter(napravleniye=transfer_d.pk)],
                        "r_type": i.research.r_type,
                        "show_more_services": i.research.show_more_services and not i.research.is_form and not i.research.is_microbiology,
                        "enabled_add_files": i.research.enabled_add_files,
                        "is_need_send_egisz": i.research.is_need_send_egisz,
                    },
                    "pacs": None if not i.research.podrazdeleniye or not i.research.podrazdeleniye.can_has_pacs else search_dicom_study(d.pk),
                    "examination_date": i.get_medical_examination(),
                    "templates": [],
                    "saved": i.time_save is not None,
                    "confirmed": i.time_confirmation is not None,
                    "confirmed_at": None if not i.time_confirmation else time.mktime(timezone.localtime(i.time_confirmation).timetuple()),
                    "allow_reset_confirm": i.allow_reset_confirm(request.user) and (not more_forbidden or TADP in i.research.title),
                    "more": [x.research_id for x in Issledovaniya.objects.filter(parent=i)],
                    "sub_directions": [],
                    "recipe": [],
                    "lab_comment": i.lab_comment,
                    "forbidden_edit": forbidden_edit,
                    "maybe_onco": i.maybe_onco,
                    "work_by": None,
                    "tube": tube,
                    "procedure_list": [],
                    "is_form": i.research.is_form,
                    "children_directions": [
                        {"pk": x.pk, "services": [y.research.get_title() for y in Issledovaniya.objects.filter(napravleniye=x)]} for x in Napravleniya.objects.filter(parent=i)
                    ],
                    "parentDirection": None
                    if not i.napravleniye.parent
                    else {
                        "pk": i.napravleniye.parent.napravleniye_id,
                        "service": i.napravleniye.parent.research.get_title(),
                        "is_hospital": i.napravleniye.parent.research.is_hospital,
                    },
                    "whoSaved": None if not i.doc_save or not i.time_save else f"{i.doc_save}, {strdatetimeru(i.time_save)}",
                    "whoConfirmed": (None if not i.doc_confirmation or not i.time_confirmation else f"{i.doc_confirmation}, {strdatetimeru(i.time_confirmation)}"),
                    "whoExecuted": None if not i.time_confirmation or not i.executor_confirmation else str(i.executor_confirmation),
                    "countFiles": IssledovaniyaFiles.objects.filter(issledovaniye_id=i.pk).count(),
                }

                if i.research.is_microbiology:
                    conclusion_default = []
                    culture_default = []
                    iss["microbiology"] = {
                        "bacteries": [],
                        "conclusion": i.microbiology_conclusion or "",
                        "conclusionTemplates": [x for x in [*i.research.bac_conclusion_templates.split('|'), *conclusion_default] if x],
                        "cultureCommentsTemplates": [x for x in [*i.research.bac_culture_comments_templates.split('|'), *culture_default] if x],
                    }

                    for br in MicrobiologyResultCulture.objects.filter(issledovaniye=i):
                        bactery = {
                            "resultPk": br.pk,
                            "bacteryPk": br.culture.pk,
                            "bacteryTitle": br.culture.title,
                            "bacteryGroupTitle": br.culture.group_culture.title if br.culture.group_culture else '',
                            "koe": br.koe,
                            "comments": br.comments,
                            "antibiotics": [],
                            "selectedGroup": {},
                            "selectedAntibiotic": {},
                            "selectedSet": {},
                            "phenotype": [],
                        }

                        pt: MicrobiologyResultPhenotype
                        for pt in MicrobiologyResultPhenotype.objects.filter(result_culture=br):
                            bactery["phenotype"].append(
                                {
                                    "pk": pt.pk,
                                    "title": pt.phenotype.get_full_title(),
                                    "phenotypePk": pt.phenotype_id,
                                }
                            )

                        for ar in MicrobiologyResultCultureAntibiotic.objects.filter(result_culture=br):
                            bactery["antibiotics"].append(
                                {
                                    "pk": ar.antibiotic.pk,
                                    "amount": ar.antibiotic_amount,
                                    "resultPk": ar.pk,
                                    "sri": ar.sensitivity,
                                    "dia": ar.dia,
                                }
                            )

                        iss["microbiology"]["bacteries"].append(bactery)

                if not force_form:
                    for sd in Napravleniya.objects.filter(parent=i):
                        iss["sub_directions"].append(
                            {
                                "pk": sd.pk,
                                "cancel": sd.cancel,
                                "researches": [x.research.title for x in Issledovaniya.objects.filter(napravleniye=sd)],
                            }
                        )

                for procedure in ProcedureList.objects.filter(diary=d, cancel=False).distinct():
                    drug = procedure.drug
                    procedure_times = ProcedureListTimes.objects.filter(prescription=procedure).order_by("-times_medication")
                    times = []
                    if procedure_times.exists():
                        pt_orig = procedure_times[0]
                        for pt in ProcedureListTimes.objects.filter(prescription=procedure, times_medication__date=pt_orig.times_medication.date()).order_by('times_medication'):
                            t = pt.times_medication.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%H:%M")
                            if t not in times:
                                times.append(t)

                    date_start = procedure.date_start.strftime("%Y-%m-%d")
                    date_end = procedure.date_end.strftime("%d.%m.%Y")
                    count_days = len(list(date_iter_range(procedure.date_start, procedure.date_end)))
                    iss["procedure_list"].append(
                        {
                            "pk": procedure.pk,
                            "drug": str(drug),
                            "drugPk": drug.pk,
                            "form_release": procedure.form_release_id or -1,
                            "method": procedure.method_id or -1,
                            "dosage": procedure.dosage,
                            "units": procedure.units,
                            "comment": procedure.comment,
                            "timesSelected": list(reversed(times)),
                            "dateStart": date_start,
                            "step": procedure.step or 1,
                            "dateEnd": date_end,
                            "countDays": count_days,
                        }
                    )

                if not force_form and (iss["research"]["is_doc_refferal"] or iss["research"]["is_gistology"]):
                    iss = {
                        **iss,
                        "purpose": i.purpose_id or -1,
                        "place": i.place_id or -1,
                        "fin_source": i.fin_source_id or ((i.napravleniye.istochnik_f_id or -1) if i.napravleniye else -1),
                        "price_category": i.price_category_id or ((i.napravleniye.price_category_id or -1) if i.napravleniye else -1),
                        "first_time": i.first_time,
                        "result": i.result_reception_id or -1,
                        "outcome": i.outcome_illness_id or -1,
                        "diagnos": i.diagnos,
                        "purpose_list": non_selected_visible_type(VisitPurpose),
                        "fin_source_list": non_selected_visible_type(IstochnikiFinansirovaniya, {"base": i.napravleniye.client.base}) if i.napravleniye else [],
                        "price_category_list": non_selected_visible_type(PriceCategory),
                        "place_list": non_selected_visible_type(Place),
                        "result_list": non_selected_visible_type(ResultOfTreatment),
                        "outcome_list": non_selected_visible_type(Outcomes),
                    }

                    if not force_form:
                        for rp in i.recipe_set.all():
                            iss["recipe"].append(
                                {
                                    "pk": rp.pk,
                                    "prescription": rp.drug_prescription,
                                    "taking": rp.method_of_taking,
                                    "comment": rp.comment,
                                }
                            )

                default_template = ParaclinicTemplateName.make_default(i.research)

                if i.research.templates_by_department:
                    templates_by_department = get_template_research_by_department(i.research_id, doc_department_id)
                    templates_data = [{"pk": template.id, "title": template.title} for template in templates_by_department]
                    iss["templates"].append(
                        {
                            "pk": default_template.pk,
                            "title": default_template.title,
                        }
                    )
                    iss["templates"].extend(templates_data)

                else:
                    rts = ParaclinicTemplateName.objects.filter(research=i.research, hide=False)

                    for rt in rts.order_by('title'):
                        iss["templates"].append(
                            {
                                "pk": rt.pk,
                                "title": rt.title,
                            }
                        )

                result_fields = {x.field_id: x for x in ParaclinicResult.objects.filter(issledovaniye=i)}

                fields_templates_by_department_data = None
                if i.research.templates_by_department:
                    fields_templates_by_department = get_template_field_by_department(i.research_id, doc_department_id)
                    fields_templates_by_department_data = {field_template.field_id: field_template.value for field_template in fields_templates_by_department}

                for group in i.research.paraclinicinputgroups_set.all():
                    g = {
                        "pk": group.pk,
                        "order": group.order,
                        "title": group.title,
                        "show_title": group.show_title,
                        "hide": group.hide,
                        "display_hidden": False,
                        "fields": [],
                        "visibility": group.visibility,
                        "fieldsInline": group.fields_inline,
                    }
                    for field in group.paraclinicinputfield_set.all():
                        if "Протокол для оператора" in user_groups and not field.operator_enter_param:
                            continue
                        result_field: ParaclinicResult = result_fields.get(field.pk)
                        field_type = field.field_type if not result_field else result_field.get_field_type(default_field_type=field.field_type, is_confirmed_strict=bool(i.time_confirmation))
                        values_to_input = ([] if not field.required or field_type not in [10, 12] or i.research.is_monitoring else ['- Не выбрано']) + (
                            [] if field.input_templates == '[]' or not field.input_templates else json.loads(field.input_templates)
                        )
                        if fields_templates_by_department_data:
                            values_to_input_by_department = fields_templates_by_department_data.get(field.pk)
                            if values_to_input_by_department:
                                values_to_input = json.loads(values_to_input_by_department)

                        value = (
                            ((field.default_value if field_type not in [3, 11, 13, 14, 30] else '') if not result_field else result_field.value)
                            if field_type not in [1, 20]
                            else (get_default_for_field(field_type, field.default_value) if not result_field else result_field.value)
                        )
                        if field_type in [2, 32, 33, 34, 36] and isinstance(value, str) and value.startswith('%'):
                            value = ''
                        elif field_type in [10, 12] and not value and len(values_to_input) > 0 and field.required:
                            value = values_to_input[0]
                        g["fields"].append(
                            {
                                "pk": field.pk,
                                "order": field.order,
                                "lines": field.lines,
                                "title": field.short_title if field.short_title else field.title,
                                "hide": field.hide,
                                "values_to_input": values_to_input,
                                "value": value,
                                "field_type": field_type,
                                "can_edit": field.can_edit_computed,
                                "default_value": field.default_value,
                                "visibility": field.visibility,
                                "required": field.required,
                                "helper": field.helper,
                                "controlParam": field.control_param,
                                "not_edit": field.not_edit,
                                "operator_enter_param": field.operator_enter_param,
                                "deniedGroup": field.denied_group.name if field.denied_group else "",
                            }
                        )
                    iss["research"]["groups"].append(g)
                if not without_issledovaniye or iss['pk'] not in without_issledovaniye:
                    response["researches"].append(iss)
            if not force_form and response["has_doc_referral"]:
                response["anamnesis"] = d.client.anamnesis_of_life

                d1, d2 = start_end_year()
                disp_data = sql_func.dispensarization_research(d.client.individual.sex, d.client.individual.age_for_year(), d.client_id, d1, d2)
                status_disp = 'finished'
                if not disp_data:
                    status_disp = 'notneed'
                else:
                    for disp_row in disp_data:
                        if not disp_row[4]:
                            status_disp = 'need'
                            break
                response["status_disp"] = status_disp
                response["disp_data"] = disp_data
            response["medical_certificates"] = medical_certificates

            f = True

    hospital = d and d.get_hospital()

    hospital_access = not hospital or hospital == request.user.doctorprofile.hospital or request.user.is_superuser

    # TODO: для полного запрета доступа из других организаций убрать response.get("has_monitoring") (так проверяется только для мониторингов)
    if response.get("has_monitoring") and not hospital_access:
        return status_response(False, "Нет доступа")

    if not f:
        response["message"] = "Направление не найдено"
    return JsonResponse(response)


def get_default_for_field(field_type, default_value=None):
    if field_type == 1 and default_value.lower() != "пусто":
        return strfdatetime(current_time(), '%Y-%m-%d')
    if field_type == 20 and default_value.lower() != "пусто":
        return strfdatetime(current_time(), '%H:%M')
    return ''


@group_required("Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p")
def directions_anesthesia_result(request):
    response = {"ok": False, "message": ""}
    rb = json.loads(request.body)
    temp_result = rb.get("temp_result", {})
    research_data = rb.get("research_data", {})
    action = rb.get("action", "add")
    result = ParaclinicResult.anesthesia_value_save(research_data['iss_pk'], research_data['field_pk'], temp_result, action)
    if result:
        response = {"ok": True, "message": ""}
    return JsonResponse(response)


@group_required("Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p")
def directions_anesthesia_load(request):
    rb = json.loads(request.body)
    research_data = rb.get("research_data", '')
    if research_data is None:
        return JsonResponse({'data': 'Ошибка входных данных'})
    anesthesia_data = ParaclinicResult.anesthesia_value_get(research_data['iss_pk'], research_data["field_pk"])
    tb_data = []
    row_category = {}
    if anesthesia_data:
        try:
            result = json.loads(anesthesia_data.replace("'", '"'))

        except:
            result = None
        if isinstance(result, dict):
            cols_template = [''] * (len(result['times']) + 1)
            times_row = ['Параметр']
            times_row.extend(result['times'])
            times_row.append('Сумма')

            def made_structure(type):
                for i in result[type]:
                    sum = 0
                    current_param = ['' for i in cols_template]
                    current_param[0] = i
                    for k, v in result[i].items():
                        if k in times_row:
                            index = times_row.index(k)
                            current_param[index] = v
                            if type in ['potent_drugs', 'narcotic_drugs'] and v:
                                v = v.replace(',', '.')
                                if check_float_is_valid(v):
                                    sum += float(v)
                    current_param.append(round(sum, 4) or '')
                    current_param_temp = set([current_param[i] for i in range(1, len(current_param))])
                    if len(current_param_temp) == 1 and '' in current_param_temp:
                        continue
                    tb_data.append(current_param)
                    row_category[len(tb_data) - 1] = type

            tb_data.append(times_row)
            made_structure('patient_params')
            made_structure('potent_drugs')
            made_structure('narcotic_drugs')

    return JsonResponse({'data': tb_data, 'row_category': row_category})


@group_required("Вспомогательные документы", "Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p", "Заполнение мониторингов", "Свидетельство о смерти-доступ")
def directions_paraclinic_result(request):
    TADP = SettingManager.get("tadp", default='Температура', default_type='s')
    response = {
        "ok": False,
        "message": "",
        "execData": {
            "whoSaved": None,
            "whoConfirmed": None,
            "whoExecuted": None,
        },
    }
    rb = json.loads(request.body)
    request_data = rb.get("data", {})
    pk = request_data.get("pk", -1)
    stationar_research = request_data.get("stationar_research", -1)
    with_confirm = rb.get("with_confirm", False)
    visibility_state = rb.get("visibility_state", {})
    v_g = visibility_state.get("groups", {})
    v_f = visibility_state.get("fields", {})
    recipe = request_data.get("recipe", [])
    procedure_list = request_data.get("procedure_list", [])

    tube = request_data.get("direction", {}).get("tube", {})
    co_executor = request_data.get("coExecutor", None)
    force = rb.get("force", False)
    diss = Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True)
    if (
        force
        or diss.filter(
            Q(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
            | Q(research__is_doc_refferal=True)
            | Q(research__is_paraclinic=True)
            | Q(research__is_treatment=True)
            | Q(research__is_gistology=True)
            | Q(research__is_stom=True)
            | Q(research__is_microbiology=True)
            | Q(research__is_form=True)
            | Q(research__is_monitoring=True)
            | Q(research__is_expertise=True)
            | Q(research__is_aux=True)
        ).exists()
        or request.user.is_staff
    ):
        iss = Issledovaniya.objects.get(pk=pk)
        g = [str(x) for x in request.user.groups.all()]
        tadp = TADP in iss.research.title
        more_forbidden = "Врач параклиники" not in g and "Врач консультаций" not in g and "Врач стационара" not in g and "t, ad, p" in g

        if not iss.research.is_expertise and (forbidden_edit_dir(iss.napravleniye_id) or (more_forbidden and not tadp)):
            response["message"] = "Редактирование запрещено"
            return JsonResponse(response)
        parent_child_data = rb.get('parent_child_data', None)
        slave_reserch = HospitalService.objects.filter(slave_research=iss.research).first()
        if parent_child_data and slave_reserch:
            parent = int(parent_child_data.get('parent_iss', -1))
            child = int(parent_child_data.get('child_iss', -1))
            current = int(parent_child_data.get('current_iss', -1))
            err_message = "Источник и назначение перевода совпадают"
            if (parent == current or current == child) and slave_reserch.site_type == 6:
                response["message"] = err_message
                return JsonResponse(response)
            if parent == child and slave_reserch.site_type == 6 and iss.research.title.lower().find('перевод') != -1 and child != -1:
                response["message"] = err_message
                return JsonResponse(response)

        if procedure_list:
            with transaction.atomic():
                for proc_data in procedure_list:
                    if not iss.napravleniye or not iss.napravleniye.parent or proc_data.get('remove'):
                        continue
                    user_timezone = pytz.timezone(TIME_ZONE)
                    history = iss.napravleniye.parent.napravleniye
                    diary = iss.napravleniye
                    card = iss.napravleniye.client
                    drug = Drugs.objects.get(pk=proc_data["drugPk"])
                    form_release = FormRelease.objects.filter(pk=proc_data["form_release"]).first()
                    if not form_release:
                        response["message"] = f"У назначения {drug} не заполнена форма выпуска"
                        return JsonResponse(response)
                    method = MethodsReception.objects.filter(pk=proc_data["method"]).first()
                    if not form_release:
                        response["message"] = f"У назначения {drug} не заполнен способ приёма"
                        return JsonResponse(response)
                    dosage = proc_data["dosage"]
                    if not form_release:
                        response["message"] = f"У назначения {drug} не заполнена дозировка"
                        return JsonResponse(response)
                    units = proc_data.get("units", "")
                    if not units:
                        response["message"] = f"У назначения {drug} не выбраны единицы измерения"
                        return JsonResponse(response)
                    times = proc_data["timesSelected"]
                    if not times:
                        response["message"] = f"У назначения {drug} не выбрано ни одного времени приёма"
                        return JsonResponse(response)
                    comment = proc_data.get("comment", "")
                    date_start = try_strptime(proc_data['dateStart'], ('%d.%m.%Y', '%Y-%m-%d')).astimezone(user_timezone)
                    step = int(proc_data['step'])
                    if step < 1:
                        step = 1
                    elif step > 5:
                        step = 5
                    date_end = try_strptime(proc_data['dateEnd'], ('%d.%m.%Y', '%Y-%m-%d')).astimezone(user_timezone)
                    parent_child_data = rb.get('parent_child_data', None)
                    if proc_data.get('isNew') and parent_child_data:
                        iss_hosp = Issledovaniya.objects.get(napravleniye_id=parent_child_data['current_direction'])
                        proc_obj = ProcedureList(
                            research=iss_hosp.research,
                            history=history,
                            diary=diary,
                            card=card,
                            drug=drug,
                            form_release=form_release,
                            method=method,
                            dosage=dosage,
                            units=units,
                            comment=comment,
                            date_start=date_start,
                            step=step,
                            date_end=date_end,
                            doc_create=request.user.doctorprofile,
                        )
                        proc_obj.save()
                    else:
                        proc_obj = ProcedureList.objects.get(pk=proc_data["pk"])
                        proc_obj.form_release = form_release
                        proc_obj.method = method
                        proc_obj.dosage = dosage
                        proc_obj.units = units
                        proc_obj.comment = comment
                        proc_obj.date_start = date_start
                        proc_obj.step = step
                        proc_obj.date_end = date_end
                        proc_obj.cancel = False
                        proc_obj.who_cancel = None
                        proc_obj.save()
                    ProcedureListTimes.objects.filter(prescription=proc_obj, executor__isnull=True).delete()
                    for date in date_iter_range(date_start, date_end, step=step):
                        for pc_time in times:
                            times_medication = datetime.strptime(f"{date:%Y-%m-%d} {pc_time}", '%Y-%m-%d %H:%M').astimezone(user_timezone)
                            if not ProcedureListTimes.objects.filter(prescription=proc_obj, times_medication=times_medication).exists():
                                ProcedureListTimes.objects.create(prescription=proc_obj, times_medication=times_medication)

        recipe_no_remove = []

        for r in recipe:
            if r.get("remove", False):
                continue
            if r.get("isNew", False):
                rn = Recipe(issledovaniye=iss, drug_prescription=r["prescription"], method_of_taking=r["taking"], comment=r["comment"])
                rn.save()
            else:
                rn = Recipe.objects.get(pk=r["pk"])
                MethodsOfTaking.dec(rn.drug_prescription, rn.method_of_taking)
                rn.drug_prescription = r["prescription"]
                rn.method_of_taking = r["taking"]
                rn.comment = r["comment"]
                rn.save()
            if rn.method_of_taking:
                MethodsOfTaking.inc(rn.drug_prescription, rn.method_of_taking)
            recipe_no_remove.append(rn.pk)

        Recipe.objects.filter(issledovaniye=iss).exclude(pk__in=recipe_no_remove).delete()

        if tube:
            iss.napravleniye.microbiology_n = tube.get("n", "")
            iss.napravleniye.save()

        count = 0
        date_death = None
        for group in request_data["research"]["groups"]:
            if not v_g.get(str(group["pk"]), True):
                ParaclinicResult.objects.filter(issledovaniye=iss, field__group__pk=group["pk"]).delete()
                continue
            for field in group["fields"]:
                if not v_f.get(str(field["pk"]), True):
                    ParaclinicResult.objects.filter(issledovaniye=iss, field__pk=field["pk"]).delete()
                    continue
                if not ParaclinicInputField.objects.filter(pk=field["pk"]).exists():
                    continue
                f = ParaclinicInputField.objects.get(pk=field["pk"])
                if f.title == "Дата смерти":
                    date_death = datetime.strptime(field["value"], "%Y-%m-%d").date()
                if f.title == "Регистрационный номер" and iss.research.is_gistology:
                    if iss.napravleniye.register_number.strip() != (field["value"]).strip():
                        response["message"] = "Регистрационный номер неверный"
                        return JsonResponse(response)
                if f.field_type == 21:
                    continue
                if not ParaclinicResult.objects.filter(issledovaniye=iss, field=f).exists():
                    f_result = ParaclinicResult(issledovaniye=iss, field=f, value="")
                else:
                    f_result = ParaclinicResult.objects.filter(issledovaniye=iss, field=f)[0]
                f_result.value = field["value"]
                f_result.field_type = f.field_type
                if f.field_type in [27, 28, 29, 32, 33, 34, 35]:
                    try:
                        val = json.loads(field["value"])
                    except:
                        val = {}
                    f_result.value_json = val
                f_result.client = iss.napravleniye.client
                f_result.save()
                if "Протокол для оператора" in g:
                    IssledovaniyaResultLaborant.save_result_operator(iss, f, f.field_type, field["value"], request.user.doctorprofile)
                if iss.research.is_monitoring:
                    if not MonitoringResult.objects.filter(issledovaniye=iss, research=iss.research, napravleniye=iss.napravleniye, field_id=field["pk"]).exists():
                        monitoring_result = MonitoringResult.objects.filter(issledovaniye=iss, research=iss.research, napravleniye=iss.napravleniye)[0]
                        monitoring_result.group_id = group['pk']
                        monitoring_result.group_order = group['order']
                        monitoring_result.field_order = field['order']
                        monitoring_result.field_id = field["pk"]
                        monitoring_result.value_text = ""
                        if count > 0:
                            monitoring_result.pk = None
                    else:
                        monitoring_result: MonitoringResult = MonitoringResult.objects.filter(issledovaniye=iss, research=iss.research, napravleniye=iss.napravleniye, field_id=field["pk"])[
                            0
                        ]
                        monitoring_result.value_text = ""

                    if field['field_type'] == 18 or field['field_type'] == 3 or field['field_type'] == 19:
                        monitoring_result.value_aggregate = field["value"]
                    else:
                        monitoring_result.value_aggregate = None
                        monitoring_result.value_text = field["value"]
                    monitoring_result.field_type = field['field_type']
                    monitoring_result.save()
                if f.field_type in [16, 17] and iss.napravleniye.parent and iss.napravleniye.parent.research.is_hospital:
                    try:
                        val = json.loads(str(field["value"]))
                    except Exception:
                        val = None

                    if f.field_type == 16:
                        if with_confirm:
                            if isinstance(val, list):
                                iss.napravleniye.parent.aggregate_lab = val
                            elif isinstance(val, dict) and val.get("directions"):
                                iss.napravleniye.parent.aggregate_lab = val["directions"]
                            else:
                                iss.napravleniye.parent.aggregate_lab = None
                        else:
                            iss.napravleniye.parent.aggregate_lab = None
                    elif f.field_type == 17:
                        if with_confirm:
                            if isinstance(val, list):
                                iss.napravleniye.parent.aggregate_desc = val
                            elif isinstance(val, dict) and val.get("directions"):
                                iss.napravleniye.parent.aggregate_desc = val["directions"]
                            else:
                                iss.napravleniye.parent.aggregate_desc = None
                        else:
                            iss.napravleniye.parent.aggregate_desc = None
                    iss.napravleniye.parent.save()
                count += 1

        iss.doc_save = request.user.doctorprofile
        iss.time_save = timezone.now()
        if iss.research.is_doc_refferal or iss.research.is_gistology:
            iss.medical_examination = request_data.get("examination_date") or timezone.now().date()
        if with_confirm:
            work_by = request_data.get("work_by")
            if work_by and isinstance(work_by, str) and work_by.isdigit():
                iss.doc_confirmation_id = work_by
                iss.executor_confirmation = request.user.doctorprofile
            else:
                iss.doc_confirmation = request.user.doctorprofile
            iss.time_confirmation = timezone.now()
            if iss.napravleniye:
                iss.napravleniye.qr_check_token = None
                iss.napravleniye.save(update_fields=['qr_check_token'])
            if date_death:
                client_obj = iss.napravleniye.client
                client_obj.death_date = date_death
                client_obj.save()
            if iss.research.uet_refferal_doc and iss.research.uet_refferal_doc > 0:
                iss.def_uet = iss.research.uet_refferal_doc
            if iss.research.uet_refferal_co_executor_1 and iss.research.uet_refferal_co_executor_1 > 0:
                iss.co_executor_uet = iss.research.uet_refferal_co_executor_1

        if not iss.napravleniye.visit_who_mark or not iss.napravleniye.visit_date:
            iss.napravleniye.visit_who_mark = request.user.doctorprofile
            iss.napravleniye.visit_date = timezone.now()
            iss.napravleniye.save()

        if iss.napravleniye.co_executor_id != co_executor:
            iss.napravleniye.co_executor_id = co_executor
            iss.napravleniye.save()

        if iss.research.is_microbiology:
            mb = request_data.get("microbiology", {})
            if mb:
                iss.microbiology_conclusion = mb.get('conclusion')

                has_bacteries = []
                has_anti = []

                for br in mb.get('bacteries', []):
                    if br['resultPk'] == -1:
                        bactery = MicrobiologyResultCulture(issledovaniye=iss, culture_id=br['bacteryPk'], koe=br['koe'], comments=br.get('comments', ''))
                    else:
                        bactery = MicrobiologyResultCulture.objects.get(pk=br['resultPk'])
                        bactery.culture_id = br['bacteryPk']
                        bactery.koe = br['koe']
                        bactery.comments = br.get('comments', '')
                    bactery.save()
                    has_bacteries.append(bactery.pk)

                    for ar in br['antibiotics']:
                        if ar['resultPk'] == -1:
                            anti = MicrobiologyResultCultureAntibiotic(
                                result_culture=bactery,
                                antibiotic_id=ar['pk'],
                                sensitivity=ar['sri'],
                                dia=ar['dia'],
                                antibiotic_amount=ar.get('amount', ''),
                            )
                        else:
                            anti = MicrobiologyResultCultureAntibiotic.objects.get(pk=ar['resultPk'])
                            anti.antibiotic_id = ar['pk']
                            anti.sensitivity = ar['sri']
                            anti.dia = ar['dia']
                            anti.antibiotic_amount = ar.get('amount', '')
                        anti.save()
                        has_anti.append(anti.pk)
                MicrobiologyResultCulture.objects.filter(issledovaniye=iss).exclude(pk__in=has_bacteries).delete()
                MicrobiologyResultCultureAntibiotic.objects.filter(result_culture__issledovaniye=iss).exclude(pk__in=has_anti).delete()

        iss.purpose_id = none_if_minus_1(request_data.get("purpose"))
        iss.place_id = none_if_minus_1(request_data.get("place"))
        iss.first_time = request_data.get("first_time", False)
        iss.result_reception_id = none_if_minus_1(request_data.get("result"))
        iss.outcome_illness_id = none_if_minus_1(request_data.get("outcome"))
        iss.fin_source_id = none_if_minus_1(request_data.get("fin_source"))
        if request_data.get("fin_source", None):
            if IstochnikiFinansirovaniya.objects.get(pk=int(request_data.get("fin_source"))).title == "Платно":
                iss.price_category_id = none_if_minus_1(request_data.get("price_category") or -1)
            else:
                iss.price_category_id = None
        iss.maybe_onco = request_data.get("maybe_onco", False)
        iss.diagnos = request_data.get("diagnos", "")
        iss.lab_comment = request_data.get("lab_comment", "")

        if stationar_research != -1:
            iss.gen_direction_with_research_after_confirm_id = stationar_research
        iss.save()
        if iss.napravleniye:
            iss.napravleniye.sync_confirmed_fields()
        more = request_data.get("more", [])
        h = []
        for m in more:
            if not Issledovaniya.objects.filter(parent=iss, doc_save=request.user.doctorprofile, research_id=m):
                i = Issledovaniya.objects.create(parent=iss, research_id=m)
                i.doc_save = request.user.doctorprofile
                i.time_save = timezone.now()
                i.creator = request.user.doctorprofile
                if with_confirm:
                    work_by = request_data.get("work_by")
                    if work_by and isinstance(work_by, str) and work_by.isdigit():
                        i.doc_confirmation_id = work_by
                        i.executor_confirmation = request.user.doctorprofile
                    else:
                        i.doc_confirmation = request.user.doctorprofile
                    i.time_confirmation = timezone.now()
                    if i.napravleniye:
                        i.napravleniye.qr_check_token = None
                        i.napravleniye.save(update_fields=['qr_check_token'])
                i.fin_source = iss.fin_source
                i.save()
                if i.napravleniye:
                    i.napravleniye.sync_confirmed_fields()
                h.append(i.pk)
            else:
                for i2 in Issledovaniya.objects.filter(parent=iss, doc_save=request.user.doctorprofile, research_id=m):
                    i2.time_save = timezone.now()
                    if with_confirm:
                        work_by = request_data.get("work_by")
                        if work_by and isinstance(work_by, str) and work_by.isdigit():
                            i2.doc_confirmation_id = work_by
                            i2.executor_confirmation = request.user.doctorprofile
                        else:
                            i2.doc_confirmation = request.user.doctorprofile
                        i2.time_confirmation = timezone.now()
                        if i2.napravleniye:
                            i2.napravleniye.qr_check_token = None
                            i2.napravleniye.save(update_fields=['qr_check_token'])
                    i2.fin_source = iss.fin_source
                    i2.save()
                    if i2.napravleniye:
                        i2.napravleniye.sync_confirmed_fields()
                    h.append(i2.pk)

        Issledovaniya.objects.filter(parent=iss).exclude(pk__in=h).delete()

        response["ok"] = True
        response["amd"] = iss.napravleniye.amd_status
        response["amd_number"] = iss.napravleniye.amd_number
        response["confirmed_at"] = None if not iss.time_confirmation else time.mktime(timezone.localtime(iss.time_confirmation).timetuple())
        response["execData"] = {
            "whoSaved": None if not iss.doc_save or not iss.time_save else f"{iss.doc_save}, {strdatetime(iss.time_save)}",
            "whoConfirmed": (None if not iss.doc_confirmation or not iss.time_confirmation else f"{iss.doc_confirmation}, {strdatetime(iss.time_confirmation)}"),
            "whoExecuted": None if not iss.time_confirmation or not iss.executor_confirmation else str(iss.executor_confirmation),
        }
        Log(key=pk, type=13, body="", user=request.user.doctorprofile).save()
        if with_confirm:
            if iss.napravleniye:
                iss.napravleniye.send_task_result()
            if stationar_research != -1:
                iss.gen_after_confirm(request.user)
            transfer_d = Napravleniya.objects.filter(parent_auto_gen=iss, cancel=False).first()
            response["transfer_direction"] = None if not transfer_d else transfer_d.pk
            response["transfer_direction_iss"] = [] if not transfer_d else [r.research.title for r in Issledovaniya.objects.filter(napravleniye=transfer_d.pk)]
            if iss.maybe_onco:
                card_pk = iss.napravleniye.client.pk
                dstart_onco = strdate(current_time(only_date=True))
                dispensery_onco = json.dumps(
                    {'card_pk': card_pk, 'pk': -1, 'data': {'date_start': dstart_onco, 'date_end': '', 'why_stop': '', 'close': False, 'diagnos': 'U999 Онкоподозрение', 'illnes': ''}}
                )
                dispensery_obj = HttpRequest()
                dispensery_obj._body = dispensery_onco
                dispensery_obj.user = request.user
                save_dreg(dispensery_obj)

            parent_child_data = rb.get('parent_child_data', None)
            if parent_child_data:
                parent = int(parent_child_data.get('parent_iss', -1))
                if parent > -1:
                    parent_iss = Issledovaniya.objects.get(pk=parent)
                    Napravleniya.objects.filter(pk=parent_child_data['current_direction']).update(parent=parent_iss, cancel=False)
                if parent == -1:
                    Napravleniya.objects.filter(pk=parent_child_data['current_direction']).update(parent=None)

                parent = int(parent_child_data.get('current_iss', -1))
                child = int(parent_child_data.get('child_iss', -1))
                if parent > -1 and child > -1:
                    parent_iss = Issledovaniya.objects.get(pk=parent)
                    child_iss = Issledovaniya.objects.values_list('napravleniye_id').get(pk=child)
                    child_direction = Napravleniya.objects.get(pk=child_iss[0])
                    if child_direction.parent:
                        Napravleniya.objects.filter(pk=child_iss[0]).update(parent=parent_iss, cancel=False)

            if iss.research.cpp_template_files:
                patient = iss.napravleniye.client.get_data_individual()
                company = iss.napravleniye.client.work_place_db
                price = PriceName.get_company_price_by_date(company.pk, current_time(only_date=True), current_time(only_date=True))
                patient['uuid'] = str(uuid.uuid4())

                data = {
                    "company": Company.as_json(company),
                    "contract": PriceName.as_json(price),
                    "patient": patient
                }
                field_titles = [
                    "СНИЛС",
                    "Дата осмотра",
                    "Результат медицинского осмотра",
                    "Группы риска",
                    "Группы риска по SCORE",
                    "Дата присвоения группы здоровья",
                    "Вредные факторы",
                    "Группа здоровья",
                    "Номер справки",
                    "Дата выдачи справки",
                ]
                result_protocol = fields_result_only_title_fields(iss, field_titles)
                data["result"] = result_protocol
                gen_resul_cpp_file(iss, iss.research.cpp_template_files, data)

            Log(key=pk, type=14, body="", user=request.user.doctorprofile).save()
        forbidden_edit = forbidden_edit_dir(iss.napravleniye_id)
        response["forbidden_edit"] = forbidden_edit or more_forbidden
        response["soft_forbidden"] = not forbidden_edit
    return JsonResponse(response)


@group_required("Врач параклиники", "Врач консультаций", "Врач стационара", "t, ad, p")
def directions_paraclinic_confirm(request):
    TADP = SettingManager.get("tadp", default='Температура', default_type='s')
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)
    diss = Issledovaniya.objects.filter(pk=pk, time_confirmation__isnull=True)
    if diss.filter(
        Q(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
        | Q(research__is_doc_refferal=True)
        | Q(research__is_treatment=True)
        | Q(research__is_slave_hospital=True)
        | Q(research__is_stom=True)
    ).exists():
        iss = Issledovaniya.objects.get(pk=pk)
        g = [str(x) for x in request.user.groups.all()]
        tadp = TADP in iss.research.title
        more_forbidden = "Врач параклиники" not in g and "Врач консультаций" not in g and "Врач стационара" not in g and "t, ad, p" in g
        if forbidden_edit_dir(iss.napravleniye_id) or (more_forbidden and not tadp):
            response["message"] = "Редактирование запрещено"
            return JsonResponse(response)
        t = timezone.now()
        if not iss.napravleniye.visit_who_mark or not iss.napravleniye.visit_date:
            iss.napravleniye.visit_who_mark = request.user.doctorprofile
            iss.napravleniye.visit_date = t
            iss.napravleniye.save()
        iss.doc_confirmation = request.user.doctorprofile
        if iss.napravleniye:
            iss.napravleniye.qr_check_token = None
            iss.napravleniye.save(update_fields=['qr_check_token'])
        iss.time_confirmation = t
        iss.save()
        if iss.napravleniye:
            iss.napravleniye.sync_confirmed_fields()
        iss.gen_after_confirm(request.user)
        for i in Issledovaniya.objects.filter(parent=iss):
            i.doc_confirmation = request.user.doctorprofile
            i.time_confirmation = t
            i.save()
            if i.napravleniye:
                i.napravleniye.sync_confirmed_fields()
            if i.napravleniye:
                i.napravleniye.qr_check_token = None
                i.napravleniye.save(update_fields=['qr_check_token'])

        if iss.napravleniye:
            iss.napravleniye.send_task_result()

        response["ok"] = True
        response["amd"] = iss.napravleniye.amd_status
        response["amd_number"] = iss.napravleniye.amd_number
        response["forbidden_edit"] = forbidden_edit_dir(iss.napravleniye_id)
        response["confirmed_at"] = None if not iss.time_confirmation else time.mktime(timezone.localtime(iss.time_confirmation).timetuple())
        Log(key=pk, type=14, body=json.dumps(request_data), user=request.user.doctorprofile).save()
    return JsonResponse(response)


@group_required(
    "Врач параклиники", "Сброс подтверждений результатов", "Врач консультаций", "Врач стационара", "Сброс подтверждения переводного эпикриза", "Сброс подтверждения выписки", "t, ad, p"
)
def directions_paraclinic_confirm_reset(request):
    TADP = SettingManager.get("tadp", default='Температура', default_type='s')
    response = {"ok": False, "message": ""}
    request_data = json.loads(request.body)
    pk = request_data.get("iss_pk", -1)

    if Issledovaniya.objects.filter(pk=pk).exists():
        iss: Issledovaniya = Issledovaniya.objects.get(pk=pk)
        is_transfer = iss.research.can_transfer
        is_extract = iss.research.is_extract

        g = [str(x) for x in request.user.groups.all()]
        tadp = TADP in iss.research.title
        more_forbidden = "Врач параклиники" not in g and "Врач консультаций" not in g and "Врач стационара" not in g and "t, ad, p" in g

        allow_reset = iss.allow_reset_confirm(request.user) and (not more_forbidden or tadp)

        if not allow_reset:
            response["message"] = "Редактирование запрещено. Запросите сброс подтверждения у администратора"
            return JsonResponse(response)

        if allow_reset:
            predoc = {"fio": iss.doc_confirmation_fio, "pk": iss.doc_confirmation_id, "direction": iss.napravleniye_id}
            iss.doc_confirmation = iss.executor_confirmation = iss.time_confirmation = None
            iss.n3_odii_uploaded_task_id = None
            iss.save()
            if iss.napravleniye:
                iss.napravleniye.sync_confirmed_fields()
            transfer_d = Napravleniya.objects.filter(parent_auto_gen=iss, cancel=False).first()
            if transfer_d:
                # transfer_d.cancel = True
                transfer_d.save()
            if iss.napravleniye.result_rmis_send:
                c = Client()
                c.directions.delete_services(iss.napravleniye, request.user.doctorprofile)
            response["ok"] = True
            for i in Issledovaniya.objects.filter(parent=iss):
                i.doc_confirmation = None
                i.executor_confirmation = None
                i.time_confirmation = None
                i.save()
                if i.napravleniye:
                    i.napravleniye.sync_confirmed_fields()
            if iss.napravleniye:
                n: Napravleniya = iss.napravleniye
                n.need_resend_amd = False
                n.eds_total_signed = False
                n.eds_total_signed_at = None
                n.eds_main_signer_cert_thumbprint = None
                n.eds_main_signer_cert_details = None
                n.vi_id = None
                n.save(update_fields=['eds_total_signed', 'eds_total_signed_at', 'need_resend_amd', 'vi_id'])
            Log(key=pk, type=24, body=json.dumps(predoc), user=request.user.doctorprofile).save()
        else:
            response["message"] = "Сброс подтверждения разрешен в течении %s минут" % (str(SettingManager.get("lab_reset_confirm_time_min")))
        response["amd"] = iss.napravleniye.amd_status
        response["amd_number"] = iss.napravleniye.amd_number
        response["is_transfer"] = is_transfer
        response["is_extract"] = is_extract
        if is_transfer:
            response["forbidden_edit"] = forbidden_edit_dir(iss.napravleniye_id)
    return JsonResponse(response)


@group_required("Врач параклиники", "Врач консультаций", "Заполнение мониторингов", "Свидетельство о смерти-доступ")
def directions_paraclinic_history(request):
    response = {"directions": []}
    request_data = json.loads(request.body)
    date_start, date_end = try_parse_range(request_data["date"])
    has_dirs = []

    for direction in (
        Napravleniya.objects.filter(
            Q(issledovaniya__doc_save=request.user.doctorprofile)
            | Q(issledovaniya__doc_confirmation=request.user.doctorprofile)
            | Q(issledovaniya__executor_confirmation=request.user.doctorprofile)
        )
        .filter(Q(issledovaniya__time_confirmation__range=(date_start, date_end)) | Q(issledovaniya__time_save__range=(date_start, date_end)))
        .order_by("-issledovaniya__time_save", "-issledovaniya__time_confirmation")
    ):
        if direction.pk in has_dirs:
            continue
        has_dirs.append(direction.pk)
        d = {
            "pk": direction.pk,
            "date": strdate(direction.data_sozdaniya),
            "patient": direction.client.individual.fio(full=True, direction=direction),
            "card": direction.client.number_with_type(),
            "iss": [],
            "all_confirmed": True,
            "all_saved": True,
            "amd": direction.amd_status,
            "amd_number": direction.amd_number,
            "is_need_send_egisz": True,
        }
        for i in Issledovaniya.objects.filter(napravleniye=direction).order_by("pk"):
            iss = {"title": i.research.get_title(), "saved": i.time_save is not None, "confirmed": i.time_confirmation is not None, "is_need_send_egisz": i.research.is_need_send_egisz}
            d["iss"].append(iss)
            if not iss["saved"]:
                d["all_saved"] = False
            if not iss["confirmed"]:
                d["all_confirmed"] = False
            if not iss["is_need_send_egisz"]:
                d["is_need_send_egisz"] = False
        response["directions"].append(d)
    return JsonResponse(response)


def directions_patient_history(request):
    data = []
    request_data = json.loads(request.body)

    iss = Issledovaniya.objects.get(pk=request_data["pk"])
    researches_pk = [iss.research.pk]
    if iss.research.speciality:
        reserches_speciality = list(Researches.objects.values_list('pk', flat=True).filter(speciality=iss.research.speciality))
        if len(reserches_speciality) > 0:
            researches_pk.extend(reserches_speciality)
    filtered = Issledovaniya.objects.filter(time_confirmation__isnull=False, research_id__in=researches_pk, napravleniye__client__individual=iss.napravleniye.client.individual)

    is_same_parent = request_data.get("isSameParent", False)

    hospital_research = HospitalService.objects.filter(slave_research=iss.research).first()
    site_type = -1
    if hospital_research:
        site_type = hospital_research.site_type

    if is_same_parent and site_type == 1:
        filtered = filtered.filter(napravleniye__parent=iss.napravleniye.parent)

    for i in filtered.order_by('-time_confirmation').exclude(pk=request_data["pk"]):
        data.append({"pk": i.pk, "direction": i.napravleniye_id, "date": strdate(i.time_confirmation) + ' ' + i.research.short_title + ' (' + i.doc_confirmation.get_fio() + ')'})

    return JsonResponse({"data": data})


def directions_data_by_fields(request):
    data = {}
    request_data = json.loads(request.body)
    i = Issledovaniya.objects.get(pk=request_data["pk"])
    pk_dest = request_data.get("pk_dest", request_data["pk"])
    i_dest = Issledovaniya.objects.get(pk=pk_dest)
    if i.time_confirmation:
        if i.research == i_dest.research:
            for field in ParaclinicInputField.objects.filter(group__research=i.research, group__hide=False, hide=False):
                if ParaclinicResult.objects.filter(issledovaniye=i, field=field).exists() and field.field_type != 30:
                    data[field.pk] = ParaclinicResult.objects.filter(issledovaniye=i, field=field)[0].value
            return JsonResponse({"data": data})
        else:
            for field in ParaclinicInputField.objects.filter(group__research=i.research, group__hide=False, hide=False):
                if ParaclinicResult.objects.filter(issledovaniye=i, field=field).exists():
                    for field_dest in ParaclinicInputField.objects.filter(group__research=i_dest.research, group__hide=False, hide=False):
                        if field_dest.attached and field_dest.attached == field.attached and field_dest.field_type != 30:
                            data[field_dest.pk] = ParaclinicResult.objects.filter(issledovaniye=i, field=field)[0].value
                            break
            return JsonResponse({"data": data})


@login_required
def last_fraction_result(request):
    request_data = json.loads(request.body)
    client_pk = request_data["clientPk"]
    fraction_pk = int(request_data["fractionPk"])
    rows = get_fraction_result(client_pk, fraction_pk)
    result = None
    if rows:
        row = rows[0]
        result = {"direction": row[1], "date": row[4], "value": row[5]}
    return JsonResponse({"result": result})


@login_required
def last_field_result(request):
    request_data = {"fieldPk": "null", **json.loads(request.body)}
    client_pk = request_data["clientPk"]
    logical_or, logical_and, logical_group_or = False, False, False
    field_is_link, field_is_aggregate_operation, field_is_aggregate_proto_description = False, False, False
    field_pks, operations_data, aggregate_data = None, None, None
    result = None

    c = Card.objects.get(pk=client_pk)
    data = c.get_data_individual()
    mother_obj = None
    mother_data = None
    num_dir = -1
    if request_data.get("iss_pk", None):
        if Issledovaniya.objects.get(pk=request_data["iss_pk"]).time_confirmation:
            return JsonResponse({"result": ""})
        num_dir = get_current_direction(request_data["iss_pk"])
    if c.mother:
        mother_obj = c.mother
        mother_data = mother_obj.get_data_individual()
    if request_data["fieldPk"].find('%work_place') != -1:
        if c.work_place:
            work_place = c.work_place
        elif c.work_place_db:
            work_place = c.work_place_db.title
        else:
            work_place = ""
        result = {"value": work_place}
    elif request_data["fieldPk"].find('%district') != -1:
        if c.district:
            district = c.district.title
        else:
            district = ""
        result = {"value": district}
    elif request_data["fieldPk"].find('%hospital') != -1:
        hosp_title = Napravleniya.objects.get(pk=num_dir).hospital_title
        result = {"value": hosp_title}
    elif request_data["fieldPk"].find('%parent_dir_data') != -1:
        iss_parent = Napravleniya.objects.get(pk=num_dir).parent
        research = iss_parent.research.title
        direction_num = iss_parent.napravleniye_id
        patient_data = f"Пациент-{data['fio']}. Д/р-{data['born']}. Полис-{data['enp']}. СНИЛС-{data['snils']}." f"\nДокумент-{research} №-{direction_num}"
        result = {"value": patient_data}
    elif request_data["fieldPk"].find('%main_address') != -1:
        result = {"value": c.main_address}
    elif request_data["fieldPk"].find('%mother_full_main_address') != -1:
        result = {"value": mother_obj.main_address_full}
    elif request_data["fieldPk"].find('%full_main_address') != -1:
        result = {"value": c.main_address_full}
    elif request_data["fieldPk"].find('%docprofile') != -1:
        result = {"value": request.user.doctorprofile.get_full_fio()}
    elif request_data["fieldPk"].find('%doc_position') != -1:
        result = {"value": request.user.doctorprofile.get_position()}
    elif request_data["fieldPk"].find('%patient_fio') != -1:
        result = {"value": data['fio']}
    elif request_data["fieldPk"].find('%patient_family') != -1:
        result = {"value": data['family']}
    elif request_data["fieldPk"].find('%patient_name') != -1:
        result = {"value": data['name']}
    elif request_data["fieldPk"].find('%patient_patronymic') != -1:
        result = {"value": data['patronymic']}
    elif request_data["fieldPk"].find('%mother_family') != -1:
        result = {"value": mother_data['family']}
    elif request_data["fieldPk"].find('%mother_name') != -1:
        result = {"value": mother_data['name']}
    elif request_data["fieldPk"].find('%mother_patronymic') != -1:
        result = {"value": mother_data['patronymic']}
    elif request_data["fieldPk"].find('%patient_born') != -1:
        result = {"value": data['born']}
    elif request_data["fieldPk"].find('%mother_born') != -1:
        result = {"value": mother_data['born']}
    elif request_data["fieldPk"].find('%snils') != -1:
        result = {"value": data['snils']}
    elif request_data["fieldPk"].find('%harmfull_factors') != -1:
        result = {"value": data['harmfull_factors']}
    elif request_data["fieldPk"].find('%sex_full') != -1:
        if data['sex'] == 'м':
            sex = 'мужской'
        else:
            sex = 'женский'
        result = {"value": sex}
    elif request_data["fieldPk"].find('%sex_short') != -1:
        result = {"value": data['sex']}
    elif request_data["fieldPk"].find('%mother_snils') != -1:
        result = {"value": mother_data['snils']}
    elif request_data["fieldPk"].find('%polis_enp') != -1:
        result = {"value": data['enp']}
    elif request_data["fieldPk"].find('%mother_polis_enp') != -1:
        result = {"value": mother_data['enp']}
    elif request_data["fieldPk"].find('%tfoms-attachment') != -1:
        tfoms_data = c.individual.match_tfoms()
        if not tfoms_data or not isinstance(tfoms_data, dict):
            return status_response(False, 'Пациент не найден в базе ТФОМС', {'value': '000000 — не найдено'})
        idt = tfoms_data['idt']
        from tfoms.integration import get_attachment_by_idt

        attachment_data = get_attachment_by_idt(idt)
        if not attachment_data or not isinstance(attachment_data, dict) or not attachment_data.get('unit_code') or not attachment_data.get('area_name'):
            return status_response(False, 'Не найдено прикрепление пациента по базе ТФОМС', {'value': '000000 — не найдено'})
        return status_response(True, data={'value': f'{attachment_data["unit_code"]} — {attachment_data["area_name"]}'})
    elif request_data["fieldPk"].find('%document_type') != -1:
        if data['passport_num']:
            result = {"value": "1-Паспорт гражданина Российской Федерации"}
        elif not data['passport_num'] and data['bc_num']:
            result = {"value": "6-Свидетельство о рождении"}
    elif request_data["fieldPk"].find('%mother_document_type') != -1:
        if mother_data['passport_num']:
            result = {"value": "1-Паспорт гражданина Российской Федерации"}
    elif request_data["fieldPk"].find('%doc_serial') != -1:
        if data['passport_num']:
            result = {"value": data["passport_serial"]}
        elif not data['passport_serial'] and data['bc_num']:
            result = {"value": data["bc_serial"]}
    elif request_data["fieldPk"].find('%mother_passport_serial') != -1:
        if mother_data['passport_num']:
            result = {"value": mother_data["passport_serial"]}
    elif request_data["fieldPk"].find('%doc_number') != -1:
        if data['passport_num']:
            result = {"value": data["passport_num"]}
        elif not data['passport_serial'] and data['bc_num']:
            result = {"value": data["bc_num"]}
    elif request_data["fieldPk"].find('%mother_passport_num') != -1:
        if mother_data['passport_num']:
            result = {"value": mother_data["passport_num"]}
    elif request_data["fieldPk"].find('%doc_who_issue') != -1:
        if data['passport_num']:
            result = {"value": data["passport_issued"]}
        elif not data['passport_serial'] and data['bc_num']:
            result = {"value": data["bc_issued"]}
    elif request_data["fieldPk"].find('%mother_passport_who') != -1:
        if mother_data['passport_num']:
            result = {"value": mother_data["passport_issued"]}
    elif request_data["fieldPk"].find('%doc_date_issue') != -1:
        if data['passport_num']:
            result = {"value": data["passport_date_start"]}
        elif not data['passport_serial'] and data['bc_num']:
            result = {"value": data["bc_date_start"]}
    elif request_data["fieldPk"].find('%mother_passport_date_issue') != -1:
        if mother_data['passport_num']:
            result = {"value": mother_data["passport_date_start"]}
    elif request_data["fieldPk"].find('%fact_address') != -1:
        result = {"value": c.fact_address}
    elif request_data["fieldPk"].find('%full_fact_address') != -1:
        result = {"value": c.fact_address_full}
    elif request_data["fieldPk"].find('%phone') != -1:
        result = {"value": c.phone}
    elif request_data["fieldPk"].find('%current_manager') != -1:
        hospital_manager = Napravleniya.objects.get(pk=num_dir).hospital.current_manager
        result = {"value": hospital_manager}
    elif request_data["fieldPk"].find('%work_position') != -1:
        work_position = ""
        work_data = c.work_position.split(';')
        if len(work_data) >= 1:
            work_position = work_data[0]
        result = {"value": work_position.strip()}
    elif request_data["fieldPk"].find('%work_code_position') != -1:
        work_position = ""
        work_data = c.work_position.split(';')
        if len(work_data) >= 1:
            work_position = work_data[0]
        nsi_position = ProfessionsWorkersPositionsRefbook.objects.values_list("code", flat=True).filter(title=work_position).first()
        result = {"value": nsi_position.strip()}
    elif request_data["fieldPk"].find('%work_department') != -1:
        work_department = ""
        work_data = c.work_position.split(';')
        if len(work_data) >= 2:
            work_department = work_data[1]
        result = {"value": work_department.strip()}
    elif request_data["fieldPk"].find('%db_department') != -1:
        work_data = ""
        if c.work_department_db:
            work_data = c.work_department_db.title
        result = {"value": work_data.strip()}
    elif request_data["fieldPk"].find('%harmful_factor') != -1:
        result = {"value": c.harmful_factor}
    elif request_data["fieldPk"].find('%proto_operation') != -1:
        # получить все направления в истории по типу hosp
        main_hosp_dir = hosp_get_hosp_direction(num_dir)[0]
        operations_data = hosp_get_operation_data(main_hosp_dir['direction'])
        field_is_aggregate_operation = True
    elif request_data["fieldPk"].find('%directionparam') != -1:
        id_field = request_data["fieldPk"].split(":")
        val = DirectionParamsResult.objects.values_list('value', flat=True).filter(napravleniye_id=num_dir, field_id=id_field[1]).first()
        if not val:
            val = ""
        result = {"value": val}
    elif request_data["fieldPk"].find('%direction#date_gistology_receive') != -1:
        val = Napravleniya.objects.values_list('time_gistology_receive', flat=True).filter(pk=num_dir).first()
        val = val.astimezone(pytz.timezone(settings.TIME_ZONE))
        result = {"value": val.strftime("%Y-%m-%d")}
    elif request_data["fieldPk"].find('%direction#time_gistology_receive') != -1:
        val = Napravleniya.objects.values_list('time_gistology_receive', flat=True).filter(pk=num_dir).first()
        val = val.astimezone(pytz.timezone(settings.TIME_ZONE))
        result = {"value": val.strftime("%H:%M")}
    elif request_data["fieldPk"].find('%direction#date_visit_date') != -1:
        val = Napravleniya.objects.values_list('visit_date', flat=True).filter(pk=num_dir).first()
        val = val.astimezone(pytz.timezone(settings.TIME_ZONE))
        result = {"value": val.strftime("%Y-%m-%d")}
    elif request_data["fieldPk"].find('%direction#time_visit_date') != -1:
        val = Napravleniya.objects.values_list('visit_date', flat=True).filter(pk=num_dir).first()
        val = val.astimezone(pytz.timezone(settings.TIME_ZONE))
        result = {"value": val.strftime("%H:%M")}
    elif request_data["fieldPk"].find('%direction#register_number') != -1:
        val = Napravleniya.objects.values_list('register_number', flat=True).filter(pk=num_dir).first()
        result = {"value": val}
    elif request_data["fieldPk"].find('%paramhospital#') != -1:
        hospital_param = request_data["fieldPk"].split("#")
        hospital_param = hospital_param[1]
        param_result = HospitalParams.objects.filter(hospital=Napravleniya.objects.get(pk=num_dir).hospital, param_title=hospital_param).first()
        result = {"value": param_result.param_value if param_result else ""}
    elif request_data["fieldPk"].find('%prevDirectionFieldValue') != -1:
        _, field_id = request_data["fieldPk"].split(":")
        current_iss = request_data["iss_pk"]
        client_id = Issledovaniya.objects.get(pk=current_iss).napravleniye.client_id
        val = (
            ParaclinicResult.objects.filter(field_id=field_id, issledovaniye__napravleniye__client=client_id)
            .exclude(issledovaniye_id=current_iss)
            .exclude(issledovaniye__time_confirmation__isnull=True)
            .order_by('issledovaniye__time_confirmation')
            .values_list('value', flat=True)
            .first()
        )
        result = {"value": val, "isJson": False if not val or not isinstance(val, str) else ((val.startswith("{") and val.endswith("}")) or (val.startswith("[") and val.endswith("]")))}
    elif request_data["fieldPk"].find('%proto_description') != -1 and 'iss_pk' in request_data:
        aggregate_data = hosp_get_text_iss(request_data['iss_pk'], True, 'desc')
        field_is_aggregate_proto_description = True
    elif request_data["fieldPk"].find('%field_link#') != -1:
        data = request_data["fieldPk"].split('#')
        field_pks = [data[1]]
        logical_or = True
        result = field_get_link_data(field_pks, client_pk, logical_or, logical_and, logical_group_or)
    elif request_data["fieldPk"].find('%receive_gistology_date') != -1:
        date_time = Napravleniya.objects.get(pk=num_dir).time_gistology_receive
        val = ""
        if date_time:
            val = date_time.strftime("%d.%m.%Y")
        result = {"value": val}
    elif request_data["fieldPk"].find('%receive_gistology_time') != -1:
        date_time = Napravleniya.objects.get(pk=num_dir).time_gistology_receive
        val = ""
        if date_time:
            val = date_time.strftime("%H:%M")
        result = {"value": val}
    elif request_data["fieldPk"].find("|") > -1:
        field_is_link = True
        logical_or = True
        field_pks = request_data["fieldPk"].split('|')
        if request_data["fieldPk"].find('@') > -1:
            logical_group_or = True
    elif request_data["fieldPk"].find("&") > -1:
        field_is_link = True
        logical_and = True
        field_pks = request_data["fieldPk"].split('&')
    elif request_data["fieldPk"].find('%current_year#') != -1:
        data = request_data["fieldPk"].split('#')
        field_pks = [data[1]]
        logical_or = True
        result = field_get_link_data(field_pks, client_pk, logical_or, logical_and, logical_group_or, use_current_year=True)
    elif request_data["fieldPk"].find('%months_ago#') != -1:
        data = request_data["fieldPk"].split('#')
        if len(data) < 3:
            result = {"value": ""}
        else:
            field_pks = [data[1]]
            logical_or = True
            result = field_get_link_data(field_pks, client_pk, logical_or, logical_and, logical_group_or, use_current_year=False, months_ago=f"{data[2]} month")
    elif request_data["fieldPk"].find('%current_hosp') != -1:
        data = request_data["fieldPk"].split('#')
        if len(data) < 2:
            result = {"value": ""}
        else:
            field_pks = [data[1]]
            logical_or = True
            parent_iss = Napravleniya.objects.get(pk=num_dir).parent_id
            result = field_get_link_data(field_pks, client_pk, logical_or, logical_and, logical_group_or, use_current_hosp=True, parent_iss=(parent_iss,))
    elif request_data["fieldPk"].find('%root_hosp') != -1:
        data = request_data["fieldPk"].split('#')
        if len(data) < 2:
            result = {"value": ""}
        else:
            field_pks = [data[1]]
            logical_or = True
            hosp_dirs = hosp_get_hosp_direction(num_dir)
            parent_iss = [i['issledovaniye'] for i in hosp_dirs]
            result = field_get_link_data(field_pks, client_pk, logical_or, logical_and, logical_group_or, use_root_hosp=True, parent_iss=tuple(parent_iss))
    elif request_data["fieldPk"].find('%control_param#') != -1:
        # %control_param#code#period#find_val
        data = request_data["fieldPk"].split('#')
        if len(data) < 4:
            result = {"value": ""}
        param_code = int(data[1])
        param_period = data[2]
        param_find_val = data[3]
        end_year = current_year()
        if param_period == 'current_year':
            start_year = end_year
        else:
            start_year = param_period
        unique_month_result = get_card_control_param(client_pk, start_year, end_year, code_param_id=param_code)
        # [{'title': 'Параметр', 'purposeValue': 'Целевое значение', 'dates': {'2022-07': {}}},
        # {'controlParamId': 5, 'title': 'сопутствующие диагнозы', 'purposeValue': '',
        # 'dates': {'2022-07': {'11.07.2022': [{'dir': 227779, 'value': 'K22.1'}]}}}]
        result = {"value": "Нет"}
        for element in unique_month_result:
            if element.get('controlParamId') == param_code:
                for k, v in element.get('dates').items():
                    for data in v.values():
                        for d in data:
                            if d['value'].find(param_find_val) != -1:
                                return JsonResponse({"result": {"value": "да"}})
    elif request_data["fieldPk"].find('%vital_param#') != -1:
        # %vital_param#code#current_hosp
        data = request_data["fieldPk"].split('#')
        if len(data) < 3:
            result = {"value": ""}
        param_code = int(data[1])
        search_place = data[2]
        parent_iss = (-1,)
        if search_place == 'current_hosp':
            parent_iss = (Napravleniya.objects.get(pk=num_dir).parent_id,)
        elif search_place == 'root_hosp':
            hosp_dirs = hosp_get_hosp_direction(num_dir)
            parent_iss = tuple([i['issledovaniye'] for i in hosp_dirs])
        vital_result = get_vital_param_in_hosp(client_pk, parent_iss, param_code)
        result = {"value": vital_result}
    else:
        field_pks = [request_data["fieldPk"]]
        logical_or = True
        field_is_link = True

    if field_is_link:
        result = field_get_link_data(field_pks, client_pk, logical_or, logical_and, logical_group_or)
    elif field_is_aggregate_operation:
        result = field_get_aggregate_operation_data(operations_data)
    elif field_is_aggregate_proto_description:
        result = field_get_aggregate_text_protocol_data(aggregate_data)

    return JsonResponse({"result": result})


def get_current_direction(current_iss):
    return Issledovaniya.objects.get(pk=current_iss).napravleniye_id


def field_get_link_data(
    field_pks, client_pk, logical_or, logical_and, logical_group_or, use_current_year=False, months_ago='-1', use_root_hosp=False, use_current_hosp=False, parent_iss=(-1,)
):
    result, value, temp_value = None, None, None
    for current_field_pk in field_pks:
        group_fields = [current_field_pk]
        logical_and_inside = logical_and
        logical_or_inside = logical_or
        if current_field_pk.find('@') > -1:
            group_fields = get_input_fields_by_group(current_field_pk)
            logical_and_inside = True
            logical_or_inside = False
        for field_pk in group_fields:
            if field_pk.isdigit():
                if use_current_year:
                    c_year = current_year()
                    c_year = f"{c_year}-01-01 00:00:00"
                else:
                    c_year = "1900-01-01 00:00:00"
                use_parent_iss = '-1'
                if use_root_hosp or use_current_hosp:
                    use_parent_iss = '1'
                rows = get_field_result(client_pk, int(field_pk), count=1, current_year=c_year, months_ago=months_ago, parent_iss=parent_iss, use_parent_iss=use_parent_iss)
                if rows:
                    row = rows[0]
                    value = row[5]
                    match = re.fullmatch(r'\d{4}-\d\d-\d\d', value)
                    if match:
                        value = normalize_date(value)
                    if logical_or_inside:
                        result = {"directicheck_use_current_hosp(on": row[1], "date": row[4], "value": value}
                        if value:
                            break
                    if logical_and_inside:
                        r = ParaclinicInputField.objects.get(pk=field_pk)
                        titles = r.get_title()
                        if result is None:
                            result = {"direction": row[1], "date": row[4], "value": value}
                        else:
                            temp_value = result.get('value', ' ')
                            if value:
                                result["value"] = f"{temp_value} {titles} - {value};"

        if logical_group_or and temp_value or logical_or_inside and value:
            break
    return result


def field_get_aggregate_operation_data(operations_data):
    result = None
    count = 0
    if len(operations_data) > 0:
        for i in operations_data:
            count += 1
            value = (
                f"{count}) Название операции: {i['name_operation']}, Проведена: {i['date']} {i['time_start']}-{i['time_end']}, Метод обезболивания: {i['anesthesia method']}, "
                f"Осложнения: {i['complications']}, Оперировал: {i['doc_fio']}"
            )
            if i.get("Заключение", None):
                value = f"{value}, Заключение: {i['final']}"

            if result is None:
                result = {"direction": '', "date": '', "value": value}
            else:
                temp_value = result.get('value', ' ')
                result["value"] = f"{temp_value}\n{value};"

    return result


def field_get_aggregate_text_protocol_data(data):
    value = ''
    for research in data:
        value = f"{value}[{research['title_research']}]"
        for res in research['result']:
            value = f"{value}\n[{res.get('date', '')}]\n"
            if res.get('data', ''):
                for g in res['data']:
                    value = f"{value}{g.get('group_title', '')}"
                    group_fields = g.get('fields', '')
                    if group_fields:
                        for fied_data in group_fields:
                            value = f"{value}{fied_data['title_field']}: {fied_data['value']}"
        value = f"{value}\n"

    result = {"direction": '', "date": '', "value": value}
    return result


def get_input_fields_by_group(group_pk):
    group_pk = group_pk[0:-1]
    fields_group = ParaclinicInputField.objects.values_list('id').filter(group__pk=group_pk).order_by('order')
    field_result = [str(i[0]) for i in fields_group]
    return field_result


@group_required("Врач параклиники", "Врач консультаций")
def send_amd(request):
    request_data = json.loads(request.body)
    for direction in Napravleniya.objects.filter(pk__in=request_data["pks"]):
        if direction.amd_status in ['error', 'need']:
            direction.need_resend_amd = True
            direction.amd_number = None
            direction.error_amd = False
            direction.save()
    return JsonResponse({"ok": True})


@group_required("Управление отправкой в АМД")
def reset_amd(request):
    request_data = json.loads(request.body)
    for direction in Napravleniya.objects.filter(pk__in=request_data["pks"]):
        direction.need_resend_amd = False
        direction.amd_number = None
        direction.error_amd = False
        direction.save()
    return JsonResponse({"ok": True})


def purposes(request):
    result = [{"pk": "NONE", "title": " – Не выбрано"}]
    for p in Napravleniya.PURPOSES:
        result.append(
            {
                "pk": p[0],
                "title": p[1],
            }
        )
    return JsonResponse({"purposes": result})


def external_organizations(request):
    result = [
        {"pk": "NONE", "title": " – Не выбрано"},
    ]
    for e in ExternalOrganization.objects.filter(hide=False).order_by('pk'):
        result.append(
            {
                "pk": e.pk,
                "title": e.title,
            }
        )
    data = {"organizations": result}
    if hasattr(request, 'plain_response') and request.plain_response:
        return data
    return JsonResponse(data)


@login_required
def direction_in_favorites(request):
    request_data = json.loads(request.body)
    pk = request_data['pk']
    doc: DoctorProfile = request.user.doctorprofile

    is_update = request_data.get("update", False)
    if is_update and 'status' in request_data:
        new_status = request_data.get("status", False)
        if not new_status:
            DirectionToUserWatch.objects.filter(doc=doc, direction_id=pk).delete()
        else:
            DirectionToUserWatch(doc=doc, direction_id=pk).save()
        return JsonResponse({"ok": True})

    dtuw = DirectionToUserWatch.objects.filter(doc=doc, direction_id=pk)
    return JsonResponse({"status": dtuw.exists()})


@login_required
def all_directions_in_favorites(request):
    doc: DoctorProfile = request.user.doctorprofile

    data = [
        {
            "pk": x.pk,
            "direction": x.direction_id,
            "card": x.direction.client.number_with_type(),
            "client": x.direction.client.individual.fio(full=True),
        }
        for x in DirectionToUserWatch.objects.filter(doc=doc).order_by('pk')
    ]

    return JsonResponse({"data": data})


@login_required
def directions_type_date(request):
    podr = request.user.doctorprofile.podrazdeleniye
    doc_pk = request.user.doctorprofile.pk
    request_data = json.loads(request.body)
    is_lab = request_data.get('is_lab', False)
    is_paraclinic = request_data.get('is_paraclinic', False)
    is_doc_refferal = request_data.get('is_doc_refferal', False)
    by_doc = request_data.get('by_doc', False)
    date = request_data['date']
    date = normalize_date(date)
    d1 = datetime.strptime(date, '%d.%m.%Y')
    start_date = datetime.combine(d1, dtime.min)
    end_date = datetime.combine(d1, dtime.max)

    if not is_lab and not is_doc_refferal and not is_paraclinic:
        return JsonResponse({"results": []})

    if is_lab:
        lab_podr = get_lab_podr()
        lab_podr = [i[0] for i in lab_podr]
    else:
        lab_podr = [-1]

    confirm_direction = get_confirm_direction(start_date, end_date, lab_podr, is_lab, is_paraclinic, is_doc_refferal)
    if not confirm_direction:
        return JsonResponse({"results": []})

    confirm_direction = [i[0] for i in confirm_direction]

    if not by_doc:
        confirm_direction_department = filter_direction_department(confirm_direction, int(podr.pk))
    else:
        confirm_direction_department = filter_direction_doctor(confirm_direction, doc_pk)
    confirm_direction = [i[0] for i in confirm_direction_department]

    not_confirm_direction = get_not_confirm_direction(confirm_direction)
    not_confirm_direction = [i[0] for i in not_confirm_direction]
    result_direction = list(set(confirm_direction) - set(not_confirm_direction))

    return JsonResponse({"results": result_direction})


@login_required
def directions_created_date(request):
    request_data = json.loads(request.body)
    user = request_data.get('user') or -1
    dep = request_data.get('dep') or -1
    date = request_data['date']
    date = normalize_date(date)
    d1 = datetime.strptime(date, '%d.%m.%Y')
    date_start = datetime.combine(d1, dtime.min)
    date_end = datetime.combine(d1, dtime.max)
    user_creater = (user,)
    if int(dep) > 0:
        user_creater = tuple(DoctorProfile.objects.values_list('pk', flat=True).filter(podrazdeleniye_id=dep))
    result_sql = get_directions_by_user(date_start, date_end, user_creater)
    result = [i.direction_id for i in result_sql]

    return JsonResponse({"results": result})


@login_required
@group_required("Управление иерархией истории")
def change_owner_direction(request):
    user = request.user.doctorprofile
    request_data = json.loads(request.body)
    new_card_number = request_data['new_card_number']
    old_card_number = request_data['old_card_number']
    directions = DirectionsHistory.move_directions(old_card_number, new_card_number, user)
    directions = ', '.join([str(d.pk) for d in directions])

    return JsonResponse({"directions": directions})


@login_required
def directions_result_year(request):
    request_data = json.loads(request.body)
    is_lab = request_data.get('isLab', False)
    is_paraclinic = request_data.get('isParaclinic', False)
    is_doc_refferal = request_data.get('isDocReferral', False)
    year = request_data['current_year']
    d1 = datetime.strptime(f'01.01.{year}', '%d.%m.%Y')
    start_date = datetime.combine(d1, dtime.min)
    d2 = datetime.strptime(f'31.12.{year}', '%d.%m.%Y')
    end_date = datetime.combine(d2, dtime.max)
    card_pk = request_data.get('card_pk', -1)

    if not is_lab and not is_doc_refferal and not is_paraclinic or card_pk == -1:
        return JsonResponse({"results": []})

    if is_lab:
        lab_podr = get_lab_podr()
        lab_podr = [i[0] for i in lab_podr]
    else:
        lab_podr = [-1]

    card_pk = int(card_pk)
    confirmed_directions = get_confirm_direction_patient_year(start_date, end_date, lab_podr, card_pk, is_lab, is_paraclinic, is_doc_refferal)
    if not confirmed_directions:
        return JsonResponse({"results": []})

    directions = {}

    for d in confirmed_directions:
        pacs_study_uid = None
        if d.study_instance_uid:
            pacs_study_uid = d.study_instance_uid
        if d.direction not in directions:
            directions[d.direction] = {'dir': d.direction, 'date': d.ch_time_confirmation, 'researches': [], 'pacsStudyUid': pacs_study_uid}

        directions[d.direction]['researches'].append(d.research_title)
    return JsonResponse({"results": list(directions.values())})


@login_required
def get_study_url(request):
    request_data = json.loads(request.body)
    study_uid = request_data.get("studyUid")
    if study_uid and len(DICOM_SERVERS) > 1:
        study_url = check_dicom_study_instance_uid(DICOM_SERVERS, study_uid)
    elif study_uid and len(DICOM_SERVERS) <= 1:
        study_url = f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={study_uid}'
    return JsonResponse({"studyUrl": study_url})


@login_required
def results_by_direction(request):
    request_data = json.loads(request.body)
    is_lab = request_data.get('isLab', False)
    is_paraclinic = request_data.get('isParaclinic', False)
    is_doc_refferal = request_data.get('isDocReferral', False)
    direction = request_data.get('dir')

    directions = request_data.get('directions', [])
    if not directions and direction:
        directions = [direction]
    objs_result = {}
    if is_lab:
        directions = tuple(directions)
        direction_result = get_laboratory_results_by_directions(directions)

        for r in direction_result:
            if r.direction not in objs_result:
                objs_result[r.direction] = {'dir': r.direction, 'date': r.date_confirm, 'researches': {}}

            if r.iss_id not in objs_result[r.direction]['researches']:
                objs_result[r.direction]['researches'][r.iss_id] = {'title': r.research_title, 'fio': short_fio_dots(r.fio), 'dateConfirm': r.date_confirm, 'fractions': []}

            objs_result[r.direction]['researches'][r.iss_id]['fractions'].append({'title': r.fraction_title, 'value': r.value, 'units': r.units})

    if is_paraclinic or is_doc_refferal:
        results = desc_to_data(directions, force_all_fields=True)
        for i in results:
            direction_data = i['result'][0]["date"].split(' ')
            if direction_data[1] not in objs_result:
                objs_result[direction_data[1]] = {'dir': direction_data[1], 'date': direction_data[0], 'researches': {}}
            if i['result'][0]["iss_id"] not in objs_result[direction_data[1]]['researches']:
                objs_result[direction_data[1]]['researches'][i['result'][0]["iss_id"]] = {
                    'title': i['title_research'],
                    'fio': short_fio_dots(i['result'][0]["docConfirm"]),
                    'dateConfirm': direction_data[0],
                    'fractions': [],
                }

            values = values_from_structure_data(i['result'][0]["data"])
            objs_result[direction_data[1]]['researches'][i['result'][0]["iss_id"]]["fractions"].append({'value': values})

    return JsonResponse({"results": list(objs_result.values())})


def get_research_for_direction_params(pk):
    response = {}
    if isinstance(pk, Researches):
        research_obj = pk
    elif isinstance(pk, (int, str)) and int(pk) > -1:
        research_obj = Researches.objects.get(pk=int(pk))
    else:
        return response
    response["research"] = {
        "title": research_obj.title,
        "version": research_obj.pk * 10000,
        "is_paraclinic": research_obj.is_paraclinic or research_obj.is_citology or research_obj.is_gistology,
        "is_doc_refferal": research_obj.is_doc_refferal,
        "is_microbiology": research_obj.is_microbiology,
        "is_treatment": research_obj.is_treatment,
        "is_stom": research_obj.is_stom,
        "wide_headers": research_obj.wide_headers,
        "groups": [],
        "show": False,
        "status": 'LOADED',
    }
    for group in research_obj.paraclinicinputgroups_set.all().filter(hide=False):
        g = {
            "pk": group.pk,
            "order": group.order,
            "title": group.title,
            "show_title": group.show_title,
            "hide": group.hide,
            "display_hidden": False,
            "fields": [],
            "visibility": group.visibility,
        }
        for field in group.paraclinicinputfield_set.all().filter(hide=False).order_by("order"):
            field_type = field.field_type
            g["fields"].append(
                {
                    "pk": field.pk,
                    "order": field.order,
                    "lines": field.lines,
                    "title": field.title,
                    "hide": field.hide,
                    "values_to_input": ([] if not field.required or field_type not in [10, 12] else ['- Не выбрано']) + json.loads(field.input_templates),
                    "value": (field.default_value if field_type not in [3, 11, 13, 14] else '') if field_type not in [1, 20] else (get_default_for_field(field_type, field.default_value)),
                    "field_type": field_type,
                    "default_value": field.default_value,
                    "visibility": field.visibility,
                    "required": field.required,
                    "helper": field.helper,
                }
            )
        response["research"]["groups"].append(g)

    return response


@login_required
def tubes_for_get(request):
    parse_params = {
        'pk': str,
    }

    try:
        direction_pk = int(data_parse(request.body, parse_params)[0])
        if direction_pk >= 4600000000000:
            direction_pk -= 4600000000000
            direction_pk //= 10
        direction: Napravleniya = (
            Napravleniya.objects.select_related('hospital')
            .select_related('doc')
            .select_related('doc__podrazdeleniye')
            .select_related('imported_org')
            .select_related('client')
            .select_related('client__individual')
            .prefetch_related(
                Prefetch(
                    'issledovaniya_set',
                    Issledovaniya.objects.filter(research__fractions__isnull=False)
                    .select_related('research')
                    .select_related('research__podrazdeleniye')
                    .prefetch_related(
                        Prefetch('research__fractions_set', Fractions.objects.filter(hide=False).select_related('relation').prefetch_related('fupper').prefetch_related('flower'))
                    )
                    .prefetch_related(Prefetch('tubes', TubesRegistration.objects.select_related('type').select_related('doc_get').select_related('type__tube')))
                    .order_by("research__title"),
                )
            )
            .get(pk=direction_pk)
        )
    except:
        return status_response(False, "Направление не найдено")

    user_groups = [str(x) for x in request.user.groups.all()]
    if direction.get_hospital() != request.user.doctorprofile.get_hospital() and "Направления-все МО" not in user_groups:
        return status_response(False, "Направление для другой организации")

    data = {}

    imported_org = None

    if direction.imported_org:
        imported_org = direction.imported_org.title
    elif direction.external_order:
        imported_org = direction.external_order.organization.safe_short_title

    data["direction"] = {
        "pk": direction.pk,
        "cancel": direction.cancel,
        "date": str(dateformat.format(direction.data_sozdaniya.date(), settings.DATE_FORMAT)),
        "doc": {"fio": "" if not direction.doc else direction.doc.get_fio(), "otd": "" if not direction.doc or not direction.doc.podrazdeleniye else direction.doc.podrazdeleniye.title},
        "imported_from_rmis": direction.imported_from_rmis,
        "isExternal": bool(direction.external_order),
        "imported_org": imported_org or "",
        "full_confirm": True,
        "has_not_completed": False,
    }

    data["tubes"] = {}
    tubes_buffer = {}

    fresearches = {}
    fuppers = {}
    flowers = {}

    iss_cached = list(direction.issledovaniya_set.all())

    for i in iss_cached if not direction.external_order else []:
        for fr in i.research.fractions_set.all():
            absor = fr.fupper.all()
            if absor.exists():
                fuppers[fr.pk] = True
                fresearches[fr.research_id] = True
                for absor_obj in absor:
                    flowers[absor_obj.flower_id] = True
                    fresearches[absor_obj.flower.research_id] = True

    relation_researches_count = {}
    for v in iss_cached:
        if data["direction"]["full_confirm"] and not v.time_confirmation:
            data["direction"]["full_confirm"] = False

        if direction.external_order or SettingManager.get("auto_create_tubes_with_direction", default='false', default_type='b'):
            ntube: Optional[TubesRegistration] = v.tubes.all().first()
            if ntube:
                vrpk = ntube.type_id
                if vrpk not in tubes_buffer.keys():
                    tubes_buffer[vrpk] = {"researches": set(), "labs": set(), "tube": ntube}
                tubes_buffer[vrpk]["researches"].add(v.research.title)

                podr = v.research.get_podrazdeleniye()
                if podr:
                    tubes_buffer[vrpk]["labs"].add(podr.get_title())
            continue
        x: TubesRegistration  # noqa: F842
        has_rels = {x.type_id if not x.chunk_number else f"{x.type_id}_{x.chunk_number}": x for x in v.tubes.all()}
        new_tubes = []

        chunk_number = None
        vrpk_for_research = None
        if v.research.count_volume_material_for_tube and TUBE_MAX_RESEARCH_WITH_SHARE:
            relation_tube = Fractions.objects.filter(research=v.research).first()
            rel = relation_tube.relation
            vrpk = relation_tube.relation_id

            actual_volume_share = relation_researches_count.get(rel.pk, 0) + v.research.count_volume_material_for_tube
            relation_researches_count[rel.pk] = actual_volume_share
            chunk_number = math.ceil(actual_volume_share / 1)
            vrpk_for_research = f"{vrpk}_{chunk_number}"

        for val in v.research.fractions_set.all():
            vrpk = val.relation_id
            rel = val.relation

            if vrpk not in has_rels and v.time_confirmation:
                continue

            if val.research_id in fresearches and val.pk in flowers and not v.time_confirmation:
                absor = val.flower.all().first()
                if absor.fupper_id in fuppers:
                    vrpk = absor.fupper.relation_id
                    rel = absor.fupper.relation

            if rel.max_researches_per_tube and not TUBE_MAX_RESEARCH_WITH_SHARE:
                actual_count = relation_researches_count.get(rel.pk, 0) + 1
                relation_researches_count[rel.pk] = actual_count
                chunk_number = math.ceil(actual_count / rel.max_researches_per_tube)
                vrpk = f"{vrpk}_{chunk_number}"
            elif v.research.count_volume_material_for_tube and TUBE_MAX_RESEARCH_WITH_SHARE:
                vrpk = vrpk_for_research
            else:
                chunk_number = None

            if vrpk not in tubes_buffer:
                if vrpk not in has_rels:
                    with transaction.atomic():
                        try:
                            if direction.hospital:
                                hospital_for_generator_tube = direction.hospital
                            elif direction.external_executor_hospital:
                                hospital_for_generator_tube = direction.external_executor_hospital
                            else:
                                hospital_for_generator_tube = request.user.doctorprofile.get_hospital()
                            generator_pk = TubesRegistration.get_tube_number_generator_pk(hospital_for_generator_tube)
                            generator = NumberGenerator.objects.select_for_update().get(pk=generator_pk)
                            number = generator.get_next_value()
                        except NoGenerator as e:
                            return status_response(False, str(e))
                        except GeneratorValuesAreOver as e:
                            return status_response(False, str(e))
                        ntube = TubesRegistration(type=rel, number=number, chunk_number=chunk_number)
                        ntube.save()

                        has_rels[vrpk] = ntube
                        new_tubes.append(ntube)
                else:
                    ntube = has_rels[vrpk]
                tubes_buffer[vrpk] = {"researches": set(), "labs": set(), "tube": ntube}
            else:
                ntube = tubes_buffer[vrpk]["tube"]

            tubes_buffer[vrpk]["researches"].add(v.research.title)

            podr = v.research.get_podrazdeleniye()
            if podr:
                tubes_buffer[vrpk]["labs"].add(podr.get_title())
        if new_tubes:
            v.tubes.add(*new_tubes)

    data["details"] = {}

    for key in tubes_buffer:
        v = tubes_buffer[key]
        tube = v["tube"]

        barcode = ""
        if tube.barcode:
            barcode = tube.barcode

        lab = '; '.join(sorted(v["labs"]))

        if lab not in data["tubes"]:
            data["tubes"][lab] = {}

        if tube.number not in data["tubes"][lab]:
            tube_title = tube.type.tube.title
            tube_color = tube.type.tube.color

            status = tube.getstatus()

            data["tubes"][lab][tube.number] = {
                "researches": list(v["researches"]),
                "status": status,
                "checked": True,
                "color": tube_color,
                "title": tube_title,
                "id": tube.number,
                "barcode": barcode,
            }

            data['details'][tube.number] = tube.get_details()

            if not data["direction"]["has_not_completed"] and not status:
                data["direction"]["has_not_completed"] = True

    if not data["tubes"]:
        return status_response(False, 'Направление не в лабораторию')

    individual = direction.client.individual
    data["client"] = {
        "card": direction.client.number_with_type(),
        "fio": individual.fio(),
        "sex": individual.sex,
        "birthday": individual.bd(),
        "age": individual.age_s(direction=direction),
    }
    return status_response(True, data=data)


@login_required
def tubes_register_get(request):
    pks = data_parse(request.body, {'pks': list})[0]
    data = json.loads(request.body)
    manual_select_get_time = data.get('selectGetTime')

    get_details = {}

    for pk in pks:
        val = TubesRegistration.objects.get(number=pk)
        issledovanie_in_tube = Issledovaniya.objects.filter(tubes__id=val.pk).first()
        if issledovanie_in_tube:
            napravleniye_id = issledovanie_in_tube.napravleniye_id
            all_issledovania = Issledovaniya.objects.filter(napravleniye_id=napravleniye_id)
            for issledovanie in all_issledovania:
                if len(issledovanie.tubes.all()) == 0:
                    issledovanie.tubes.add(val.pk)
                    issledovanie.save()
            napravleniye = Napravleniya.objects.filter(pk=napravleniye_id).first()
            if napravleniye.external_executor_hospital and napravleniye.external_executor_hospital.is_external_performing_organization:
                napravleniye.need_order_redirection = True
        if not val.doc_get and not val.time_get:
            val.set_get(request.user.doctorprofile, manual_select_get_time)
        get_details[pk] = val.get_details()

    return status_response(True, data={'details': get_details})


@login_required
def tubes_for_confirm(request):
    tmprows = {}
    res = {"rows": []}

    date_start = datetime.now() - timedelta(days=6)
    date_end = datetime.now()
    naps = Napravleniya.objects.filter(
        Q(data_sozdaniya__range=(date_start, date_end), doc_who_create=request.user.doctorprofile, cancel=False)
        | Q(data_sozdaniya__range=(date_start, date_end), doc=request.user.doctorprofile, cancel=False)
    )
    for n in naps:
        for i in Issledovaniya.objects.filter(napravleniye=n):
            for t in i.tubes.filter(doc_get__isnull=True):
                tmprows[t.number] = {
                    "direction": n.pk,
                    "patient": n.client.individual.fio(short=True, dots=True),
                    "title": t.type.tube.title,
                    "pk": t.number,
                    "color": t.type.tube.color,
                    "checked": True,
                }
    for pk in tmprows.keys():
        res["rows"].append(tmprows[pk])
    res["rows"] = sorted(res["rows"], key=lambda k: k['pk'])
    res["rows"] = sorted(res["rows"], key=lambda k: k['patient'])

    return JsonResponse(res)


@login_required
def tubes_get_history(request):
    data = json.loads(request.body)
    pks = data.get('pks')

    res = {"rows": []}
    tubes = TubesRegistration.objects.filter(doc_get=request.user.doctorprofile).order_by('-time_get').exclude(time_get__lt=datetime.now().date())

    if pks:
        tubes = tubes.filter(number__in=pks)

    for v in tubes:
        iss = Issledovaniya.objects.filter(tubes__number=v.number)

        res["rows"].append(
            {
                "pk": v.number,
                "direction": iss[0].napravleniye_id,
                "title": v.type.tube.title,
                "color": v.type.tube.color,
                "researches": ', '.join(str(x.research.title) for x in iss),
                "time": strtime(v.time_get),
                "checked": True,
            }
        )
    return JsonResponse(res)


@login_required
def gen_number(request):
    data = json.loads(request.body)
    key = data['numberKey']
    iss_pk = data['issPk']
    field_pk = data['fieldPk']

    with transaction.atomic():
        iss: Issledovaniya = Issledovaniya.objects.get(pk=iss_pk)

        if iss.time_confirmation:
            return status_response(False, 'Протокол уже подтверджён')

        gen: NumberGenerator = NumberGenerator.objects.select_for_update().filter(key=key, year=current_year(), hospital=iss.napravleniye.get_hospital(), is_active=True).first()

        if not gen:
            return status_response(False, 'Активный генератор на текущий год для организации направления не зарегистрирован')

        field: ParaclinicResult = ParaclinicResult.objects.filter(issledovaniye=iss, field_id=field_pk).first()

        if not field:
            field = ParaclinicResult.objects.create(issledovaniye=iss, field_id=field_pk, field_type=30)

        if field.field_type != 30:
            field.field_type = 30
            field.save()

        if field.value:
            return status_response(True, 'Значение уже было сгенерировано', {'number': field.value})

        try:
            number = gen.get_prepended_next_value()
        except GeneratorValuesAreOver as e:
            return status_response(False, str(e))

        total_free_numbers = len([x for x in gen.free_numbers if x <= gen.last]) + (gen.end - gen.last)
        total_numbers = (gen.end - gen.start) + 1

        field.value = number
        field.save()
        return status_response(True, None, {'number': number, 'totalFreeNumbers': total_free_numbers, 'totalNumbers': total_numbers})


@login_required
def free_number(request):
    data = json.loads(request.body)
    key = data['numberKey']
    iss_pk = data['issPk']
    field_pk = data['fieldPk']

    with transaction.atomic():
        iss: Issledovaniya = Issledovaniya.objects.get(pk=iss_pk)

        if iss.time_confirmation:
            return status_response(False, 'Протокол уже подтверджён')

        gen: NumberGenerator = NumberGenerator.objects.select_for_update().filter(key=key, year=current_year(), hospital=iss.napravleniye.get_hospital(), is_active=True).first()

        if not gen:
            return status_response(False, 'Активный генератор на текущий год для организации направления не зарегистрирован')

        field: ParaclinicResult = ParaclinicResult.objects.filter(issledovaniye=iss, field_id=field_pk).first()

        if key == "deathPerinatalNumber":
            field_type = 37
        else:
            field_type = 30

        if not field:
            field = ParaclinicResult.objects.create(issledovaniye=iss, field_id=field_pk, field_type=field_type)

        if field.field_type != 30 and key == "deathFormNumber":
            field.field_type = 30
            field.save()

        if field.field_type != 37 and key == "deathPerinatalNumber":
            field.field_type = 37
            field.save()

        if not field.value:
            return status_response(True)

        value = int(field.value)
        field.value = ''
        field.save()

        if value >= gen.start and value <= gen.end:
            gen.free_numbers = [*gen.free_numbers, value]
            gen.save(update_fields=['free_numbers'])

        return status_response(True)


@login_required
def eds_required_signatures(request):
    data = json.loads(request.body)
    pk = data['pk']
    direction: Napravleniya = Napravleniya.objects.get(pk=pk)

    if SettingManager.l2('required_equal_hosp_for_eds', default='true') and direction.get_hospital() != request.user.doctorprofile.get_hospital():
        return status_response(False, 'Направление не в вашу организацию!')

    if not direction.is_all_confirm():
        return status_response(False, 'Направление должно быть подтверждено!')

    rs = direction.required_signatures(fast=True, need_save=True)

    result = {'documents': []}
    ltc = direction.last_time_confirm()

    for r in rs['docTypes']:
        dd: DirectionDocument = DirectionDocument.objects.filter(direction=direction, is_archive=False, last_confirmed_at=ltc, file_type=r.lower()).first()

        has_signatures = []
        empty_signatures = rs['signsRequired']
        if dd:
            for s in DocumentSign.objects.filter(document=dd):
                has_signatures.append(s.sign_type)

                empty_signatures = [x for x in empty_signatures if x != s.sign_type]
        status = len(empty_signatures) == 0
        result['documents'].append(
            {
                'type': r,
                'status': status,
                'has': has_signatures,
                'empty': empty_signatures,
            }
        )

    return JsonResponse(result)


@login_required
def eds_documents(request):
    data = json.loads(request.body)
    pk = data['pk']
    direction: Napravleniya = Napravleniya.objects.get(pk=pk)
    iss_obj = Issledovaniya.objects.filter(napravleniye=direction).first()
    doctor_data = iss_obj.doc_confirmation.dict_data if iss_obj.doc_confirmation else None
    error_doctor = ""
    if (len(REMD_ONLY_RESEARCH) > 0 and iss_obj.research.pk not in REMD_ONLY_RESEARCH) or iss_obj.research.pk in REMD_EXCLUDE_RESEARCH or not doctor_data:
        return JsonResponse({"documents": [], "edsTitle": "", "executors": "", "error": True, "message": "Данная услуга не настроена для подписания"})

    for k, v in doctor_data.items():
        if v in ["", None]:
            error_doctor = f"{k} - не верно;{error_doctor}"

    # if not iss_obj.doc_confirmation.podrazdeleniye.n3_id or not iss_obj.doc_confirmation.hospital.code_tfoms:
    #     return JsonResponse({"documents": [], "edsTitle": "", "executors": "", "error": True, "message": "UUID подразделения или код ТФОМС не заполнен"})

    base = SettingManager.get_cda_base_url()
    if base != "empty":
        available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
        if not available:
            return JsonResponse({"documents": [], "edsTitle": "", "executors": "", "error": True, "message": "CDA-сервер недоступен"})

    if error_doctor:
        error_doctor = error_doctor.replace("position", "должность").replace("speciality", "специальность").replace("snils", "СНИЛС")
        error_doctor = f"В профиле врача {iss_obj.doc_confirmation.get_fio()} ошибки: {error_doctor}"
        return JsonResponse({"documents": [], "edsTitle": "", "executors": "", "error": True, "message": error_doctor})

    if not direction.client.get_card_documents(check_has_type=['СНИЛС']):
        # direction.client.individual.sync_with_tfoms()
        snils_used = direction.client.get_card_documents(check_has_type=['СНИЛС'])
        if not snils_used:
            return JsonResponse({"documents": "", "edsTitle": "", "executors": "", "error": True, "message": "У пациента некорректный СНИЛС"})

    if SettingManager.l2('required_equal_hosp_for_eds', default='true') and direction.get_hospital() != request.user.doctorprofile.get_hospital():
        return status_response(False, 'Направление не в вашу организацию!')

    if not direction.is_all_confirm():
        return status_response(False, 'Направление должно быть подтверждено!')

    documents = process_to_sign_direction(direction, pk, request.user, iss_obj)

    return JsonResponse({"documents": documents, "edsTitle": direction.get_eds_title(), "executors": direction.get_executors()})


def process_to_sign_direction(direction, pk, user, iss_obj):
    required_signatures = direction.required_signatures(need_save=True)

    documents = []

    has_types = {}
    last_time_confirm = direction.last_time_confirm()
    d: DirectionDocument
    for d in DirectionDocument.objects.filter(direction=direction, last_confirmed_at=last_time_confirm, is_archive=False):
        has_types[d.file_type.lower()] = True

    for t in [x for x in required_signatures['docTypes'] if x.lower() not in has_types]:
        DirectionDocument.objects.create(direction=direction, last_confirmed_at=last_time_confirm, file_type=t.lower())

    DirectionDocument.objects.filter(direction=direction, is_archive=False).exclude(last_confirmed_at=last_time_confirm).update(is_archive=True)
    cda_eds_data = get_cda_data(pk)

    for d in DirectionDocument.objects.filter(direction=direction, last_confirmed_at=last_time_confirm):
        signatures = {}
        has_signatures = DocumentSign.objects.filter(document=d)

        sgn: DocumentSign
        for sgn in has_signatures:
            signatures[sgn.sign_type] = {
                'pk': sgn.pk,
                'executor': str(sgn.executor),
                'signedAt': strfdatetime(sgn.signed_at),
                'signValue': sgn.sign_value,
            }

        for s in [x for x in required_signatures['signsRequired'] if x not in signatures]:
            signatures[s] = None
        if not d.file:
            file = None
            filename = None
            if d.file_type.lower() != d.file_type:
                d.file_type = d.file_type.lower()
                d.save()

            if d.file_type == DirectionDocument.PDF:
                request_tuple = collections.namedtuple('HttpRequest', ('GET', 'user', 'plain_response'))
                req = {
                    'GET': {
                        "pk": f'[{pk}]',
                        "split": '1',
                        "leftnone": '0',
                        "inline": '1',
                        "protocol_plain_text": '1',
                    },
                    'user': user,
                    'plain_response': True,
                }
                filename = f'{pk}-{last_time_confirm}.pdf'
                file = ContentFile(result_print(request_tuple(**req)), filename)
            elif d.file_type == DirectionDocument.CDA and "generatorName" in cda_eds_data:
                if SettingManager.l2('l2vi'):
                    cda_data = gen_cda_xml(pk=pk)
                    cda_xml = cda_data.get('result', {}).get('content')
                elif SettingManager.l2('cdator'):
                    if not iss_obj.research.cda_template_file:
                        cda_data = cdator_gen_xml(cda_eds_data["generatorName"], direction_data=cda_eds_data["data"])
                        cda_xml = cda_data.get('result', {}).get('content')
                    else:
                        cda_xml = gen_result_cda_files(iss_obj.research.cda_template_file, cda_eds_data["data"])
                else:
                    cda_xml = render_cda(service=cda_eds_data['title'], direction_data=cda_eds_data)
                filename = f"{pk}–{last_time_confirm}.cda.xml"
                if cda_xml:
                    file = ContentFile(cda_xml.encode('utf-8'), filename)
                else:
                    file = None
            if file:
                d.file.save(filename, file)

        file_content = None

        if d.file:
            if d.file_type == DirectionDocument.PDF:
                file_content = base64.b64encode(d.file.read()).decode('utf-8')
            elif d.file_type == DirectionDocument.CDA:
                file_content = d.file.read().decode('utf-8')

        document = {
            "pk": d.pk,
            "type": d.file_type.upper(),
            "fileName": os.path.basename(d.file.name) if d.file else None,
            "fileContent": file_content,
            "signatures": signatures,
            "vi_id": direction.vi_id,
        }

        documents.append(document)
    return documents


@login_required
def eds_add_sign(request):
    data = json.loads(request.body)
    pk = data['pk']
    sign = data['sign']
    sign_type = data['mode']
    cert_thumbprint = data.get('certThumbprint')
    cert_details = data.get('certDetails')
    direction_document: DirectionDocument = DirectionDocument.objects.get(pk=pk)
    direction: Napravleniya = direction_document.direction

    if SettingManager.l2('required_equal_hosp_for_eds', default='true') and direction.get_hospital() != request.user.doctorprofile.get_hospital():
        return status_response(False, 'Направление не в вашу организацию!')

    if not direction.is_all_confirm():
        return status_response(False, 'Направление должно быть подтверждено!')

    if not sign:
        return status_response(False, 'Некорректная подпись!')

    user_roles = request.user.doctorprofile.get_eds_allowed_sign()

    if sign_type not in user_roles:
        return status_response(False, 'У пользователя нет такой роли!')

    required_signatures = direction.required_signatures(need_save=True)

    if sign_type not in required_signatures['signsRequired']:
        return status_response(False, 'Некорректная роль!')

    last_time_confirm = direction.last_time_confirm()
    if direction_document.last_confirmed_at != last_time_confirm:
        return status_response(False, 'Документ был обновлён. Обновите страницу!')

    if DocumentSign.objects.filter(document=direction_document, sign_type=sign_type).exists():
        return status_response(False, 'Документ уже был подписан с такой ролью')

    executors = direction.get_executors()

    if sign_type == 'Врач' and request.user.doctorprofile.pk not in executors:
        return status_response(False, 'Подтвердить может только исполнитель')

    sign_certificate = SignatureCertificateDetails.get_or_update(cert_thumbprint, cert_details)

    DocumentSign.objects.create(document=direction_document, sign_type=sign_type, executor=request.user.doctorprofile, sign_value=sign, sign_certificate=sign_certificate)

    direction.get_eds_total_signed(forced=True)

    return status_response(True)


@login_required
def eds_to_sign(request):
    data = json.loads(request.body)
    page = max(int(data["page"]), 1)
    filters = data['filters']
    mode = filters['mode']
    department = filters['department']
    status = filters['status']
    number = filters['number']

    rows = []
    base = SettingManager.get_cda_base_url()
    if base != 'empty':
        available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
        if not available:
            return JsonResponse({"rows": rows, "page": page, "pages": 0, "total": 0, "error": True, "message": "CDA-сервер недоступен"})

    d_qs = Napravleniya.objects.filter(total_confirmed=True)
    if number:
        d_qs = d_qs.filter(pk=number if number.isdigit() else -1)
    else:
        date = filters['date']
        day1 = try_strptime(
            date,
            formats=(
                '%Y-%m-%d',
                '%d.%m.%Y',
            ),
        )
        day2 = day1 + timedelta(days=1)
        d_qs = d_qs.filter(last_confirmed_at__range=(day1, day2))
        if mode == 'mo':
            d_qs = d_qs.filter(eds_required_signature_types__contains=['Медицинская организация'])
            if department == -1:
                d_qs = d_qs.filter(issledovaniya__doc_confirmation__hospital=request.user.doctorprofile.get_hospital())
            else:
                d_qs = d_qs.filter(issledovaniya__doc_confirmation__podrazdeleniye_id=department)
        elif mode == 'my':
            if not request.user.doctorprofile.podrazdeleniye.n3_id or not request.user.doctorprofile.hospital.code_tfoms:
                return JsonResponse({"rows": rows, "page": page, "pages": 0, "total": 0, "error": True, "message": "UUID подразделения или код ТФОМС не заполнен"})
            doctor_data = request.user.doctorprofile.dict_data
            error_doctor = ""
            for k, v in doctor_data.items():
                if v in ["", None]:
                    error_doctor = f"{k} - не верно;{error_doctor}"

            if error_doctor:
                error_doctor = error_doctor.replace("position", "должность").replace("speciality", "специальность").replace("snils", "СНИЛС")
                error_doctor = f"В профиле врача {request.user.doctorprofile.get_fio()} ошибки: {error_doctor}"
                return JsonResponse({"rows": rows, "page": page, "pages": 0, "total": 0, "error": True, "message": error_doctor})
            d_qs = d_qs.filter(eds_required_signature_types__contains=['Врач'], issledovaniya__doc_confirmation=request.user.doctorprofile)
        if len(REMD_ONLY_RESEARCH) > 0:
            d_qs = d_qs.filter(issledovaniya__research_id__in=REMD_ONLY_RESEARCH)

        if len(REMD_EXCLUDE_RESEARCH) > 0:
            d_qs = d_qs.exclude(issledovaniya__research_id__in=REMD_EXCLUDE_RESEARCH)
        if status == 'ok-full':
            d_qs = d_qs.filter(eds_total_signed=True)
        elif status == 'ok-role':
            d_qs = d_qs.filter(eds_total_signed=False)
            if mode == 'mo':
                d_qs = d_qs.filter(directiondocument__documentsign__sign_type='Медицинская организация', directiondocument__is_archive=False)
            elif mode == 'my':
                d_qs = d_qs.filter(directiondocument__documentsign__sign_type='Врач', directiondocument__is_archive=False)
        else:
            if mode == 'mo':
                d_qs = d_qs.filter(directiondocument__documentsign__sign_type='Врач', directiondocument__is_archive=False)
            elif mode == 'my':
                d_qs = d_qs.exclude(directiondocument__documentsign__sign_type='Врач')
            d_qs = d_qs.filter(eds_total_signed=False)

    d: Napravleniya
    p = Paginator(d_qs.order_by('pk', 'last_confirmed_at').distinct('pk'), SettingManager.get("eds-to-sign_page-size", default='40', default_type='i'))
    for d in p.page(page).object_list:
        documents = []
        ltc = d.last_time_confirm()
        ldc = d.last_doc_confirm()
        signs_required = d.eds_required_signature_types

        for r in d.eds_required_documents:
            dd: DirectionDocument = DirectionDocument.objects.filter(direction=d, is_archive=False, last_confirmed_at=ltc, file_type=r.lower()).first()
            has_signatures = []
            empty_signatures = signs_required
            if dd:
                for s in DocumentSign.objects.filter(document=dd):
                    has_signatures.append(s.sign_type)

                    empty_signatures = [x for x in empty_signatures if x != s.sign_type]
            status = len(empty_signatures) == 0
            documents.append(
                {
                    'pk': dd.pk if dd else None,
                    'type': r,
                    'status': status,
                    'has': has_signatures,
                    'empty': empty_signatures,
                }
            )
        if not d.client.get_card_documents(check_has_type=['СНИЛС']):
            d.client.individual.sync_with_tfoms()

        rows.append(
            {
                'pk': d.pk,
                'totallySigned': d.eds_total_signed,
                'confirmedAt': strfdatetime(ltc),
                'docConfirmation': ldc,
                'documents': documents,
                'services': [x.research.get_title() for x in d.issledovaniya_set.all()],
                'n3number': d.n3_odli_id or d.n3_iemk_ok,
                'hasSnils': d.client.get_card_documents(check_has_type=['СНИЛС']),
            }
        )

    return JsonResponse({"rows": rows, "page": page, "pages": p.num_pages, "total": p.count, "error": False, "message": ''})


@login_required
def need_send_ecp(request):
    data = json.loads(request.body)
    filters = data['filters']
    mode = filters['mode']
    status = filters['status']
    department = filters['department']
    number = filters['number']
    page = max(int(data["page"]), 1)

    rows = []
    base = SettingManager.get_api_ecp_base_url()
    if base != 'empty':
        available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
        if not available:
            return JsonResponse({"rows": rows, "page": page, "pages": 0, "total": 0, "error": True, "message": "Cервер отправки в ЕЦП не доступен"})

    if status == "need":
        d_qs = Napravleniya.objects.filter(total_confirmed=True, ecp_direction_number=None, rmis_resend_services=False)
    else:
        d_qs = Napravleniya.objects.filter(total_confirmed=True, rmis_resend_services=True)
    if number:
        d_qs = d_qs.filter(pk=number if number.isdigit() else -1)
    else:
        date = filters['date']
        day1 = try_strptime(
            date,
            formats=(
                '%Y-%m-%d',
                '%d.%m.%Y',
            ),
        )
        day2 = day1 + timedelta(days=1)
        d_qs = d_qs.filter(last_confirmed_at__range=(day1, day2))
        if mode == 'department' and department != -1:
            d_qs = d_qs.filter(issledovaniya__doc_confirmation__podrazdeleniye_id=department)
        elif mode == 'my':
            if not request.user.doctorprofile.additional_info:
                return JsonResponse({"rows": rows, "page": page, "pages": 0, "total": 0, "error": True, "message": "Сведения по доктору не заполнены"})
            d_qs = d_qs.filter(issledovaniya__doc_confirmation=request.user.doctorprofile)

    d: Napravleniya
    p = Paginator(d_qs.order_by('pk', 'last_confirmed_at').distinct('pk'), SettingManager.get("eds-to-sign_page-size", default='40', default_type='i'))
    for d in p.page(page).object_list:
        ltc = d.last_time_confirm()
        ldc = d.last_doc_confirm()

        result_send = "Не отправлены"
        if d.rmis_resend_services:
            result_send = "отправлены"

        rows.append(
            {
                'pk': d.pk,
                "totallySigned": False,
                'confirmedAt': strfdatetime(ltc),
                'docConfirmation': ldc,
                'services': [x.research.get_title() for x in d.issledovaniya_set.all()],
                'ecpDirectionNumber': d.ecp_direction_number if d.ecp_direction_number else result_send,
            }
        )

    return JsonResponse({"rows": rows, "page": page, "pages": p.num_pages, "total": p.count, "error": False, "message": ''})


@login_required
def send_ecp(request):
    data = json.loads(request.body)
    directions = data['directions']

    base = SettingManager.get_api_ecp_base_url()
    if base != 'empty':
        available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
        if not available:
            return JsonResponse({"error": True, "message": "Cервер отправки в ЕЦП не доступен"})
    res = send_lab_direction_to_ecp(directions)

    num_dir = Napravleniya.objects.filter(pk__in=directions)
    for n in num_dir:
        n.rmis_resend_services = True
        n.save()
    return JsonResponse({"ok": True, "data": res})


@login_required
def expertise_status(request):
    data = json.loads(request.body)
    pk = data.get('pk', -1)

    return JsonResponse(get_expertise(pk, with_check_available=True))


@login_required
def expertise_create(request):
    data = json.loads(request.body)
    pk = data.get('pk', -1)

    n = Napravleniya.objects.get(pk=pk)
    iss: Issledovaniya = n.issledovaniya_set.all().first()
    created_pk = None
    if iss and iss.research and iss.research.expertise_params:
        result = Napravleniya.gen_napravleniya_by_issledovaniya(
            n.client_id,
            "",
            None,
            "",
            None,
            request.user.doctorprofile,
            {-1: [iss.research.expertise_params_id]},
            {},
            False,
            {},
            vich_code="",
            count=1,
            discount=0,
            parent_iss=iss.pk,
            rmis_slot=None,
        )

        created_pk = result["list_id"][0]

    return JsonResponse({"pk": created_pk})


@login_required
def send_to_l2vi(request):
    data = json.loads(request.body)
    pk = data.get('pk', -1)

    doc: DirectionDocument = DirectionDocument.objects.get(pk=pk)

    res = None
    if doc.file:
        res = send_cda_xml(doc.direction_id, doc.file.read().decode('utf-8'))

    return JsonResponse({"ok": True, "data": res})


@login_required
@group_required("Врач параклиники", "Врач консультаций", "Врач-лаборант", "Лаборант", "Заполнение мониторингов", "Свидетельство о смерти-доступ")
def add_file(request):
    file = request.FILES.get('file')
    form = request.FILES['form'].read()
    request_data = json.loads(form)
    pk = request_data["pk"]

    iss_files = IssledovaniyaFiles.objects.filter(issledovaniye_id=pk)

    if file and iss_files.count() >= 5:
        return JsonResponse(
            {
                "ok": False,
                "message": "Вы добавили слишком много файлов в одну заявку",
            }
        )

    if file and file.size > 5242880:
        return JsonResponse(
            {
                "ok": False,
                "message": "Файл слишком большой",
            }
        )

    iss = IssledovaniyaFiles(issledovaniye_id=pk, uploaded_file=file, who_add_files=request.user.doctorprofile)
    iss.save()

    return JsonResponse(
        {
            "ok": True,
        }
    )


@login_required
def file_log(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    rows = []
    for row in IssledovaniyaFiles.objects.filter(issledovaniye_id=pk).order_by('-created_at'):
        rows.append(
            {
                'pk': row.pk,
                'author': row.who_add_files.get_fio() if row.who_add_files else "-",
                'createdAt': strfdatetime(row.created_at, "%d.%m.%Y %X"),
                'file': row.uploaded_file.url if row.uploaded_file else None,
                'fileName': os.path.basename(row.uploaded_file.name) if row.uploaded_file else None,
            }
        )
    return JsonResponse(
        {
            "rows": rows,
        }
    )


def get_userdata(doc: DoctorProfile):
    if doc is None:
        return ""
    # return "%s (%s) - %s" % (doc.fio, doc.user.username, doc.podrazdeleniye.title)
    podr = ""
    if doc.podrazdeleniye:
        podr = doc.podrazdeleniye.title
    return f"{doc.fio}, {doc.user.username}, {podr}"


@login_required
def direction_history(request):
    yesno = {True: "да", False: "нет"}
    data = []
    request_data = json.loads(request.body)
    pk = request_data.get("q", "-1") or -1

    try:
        pk = int(pk)
    except ValueError:
        pk = -1

    if pk != -1 and Napravleniya.objects.filter(pk=pk).exists():
        dr = Napravleniya.objects.get(pk=pk)
        data.append(
            {
                'type': "Направление №%s" % pk,
                'events': [
                    [
                        ["title", strdatetime(dr.data_sozdaniya) + " Направление создано"],
                        ["Создатель", get_userdata(dr.doc_who_create)],
                        ["От имени", "" if not dr.doc else get_userdata(dr.doc)],
                        ["Пациент", "%s, %s, Пол: %s" % (dr.client.individual.fio(), dr.client.individual.bd(), dr.client.individual.sex)],
                        ["Карта", "%s %s" % (dr.client.number, dr.client.base.title)],
                        ["Архив", yesno[dr.client.is_archive]],
                        ["Источник финансирования", dr.fin_title],
                        ["Диагноз", dr.diagnos],
                        ["Направление создано на основе направления из РМИС", yesno[dr.imported_from_rmis]],
                        ["Направивляющая организация из РМИС", "" if not dr.imported_org else dr.imported_org.title],
                        ["Направление отправлено в РМИС", yesno[dr.imported_directions_rmis_send if dr.imported_from_rmis else dr.rmis_number not in ["", None, "NONERMIS"]]],
                        ["Номер РМИС направления", dr.rmis_number if dr.rmis_number not in [None, "NONERMIS"] else ""],
                        ["Направление привязано к случаю РМИС", yesno[dr.rmis_case_id not in ["", None, "NONERMIS"]]],
                        ["Направление привязано к записи отделения госпитализации РМИС", yesno[dr.rmis_hosp_id not in ["", None, "NONERMIS"]]],
                        ["Результат отправлен в РМИС", yesno[dr.result_rmis_send]],
                        ["Результат отправлен в ИЭМК", yesno[dr.n3_iemk_ok]],
                        ["Результат отправлен в ECP", yesno[dr.ecp_ok]],
                    ]
                ],
            }
        )
        if dr.visit_date and dr.visit_who_mark:
            d = {
                "type": "Посещение по направлению",
                "events": [
                    [
                        ["title", strdatetime(dr.visit_date) + " Регистрация посещения"],
                        ["Регистратор", dr.visit_who_mark.fio + ", " + dr.visit_who_mark.podrazdeleniye.title],
                    ]
                ],
            }
            data.append(d)

        client_send = []

        for lg in (
            Log.objects.filter(
                key=str(pk),
                type__in=(
                    180000,
                    180001,
                    180002,
                    180003,
                ),
            )
            .distinct()
            .order_by('time')
        ):
            client_send.append([["title", "{}, {}".format(strdatetime(lg.time), lg.get_type_display())], *[[k, v] for k, v in json.loads(lg.body).items()]])

        if client_send:
            data.append(
                {
                    "type": "Отправка пациенту",
                    "events": client_send,
                }
            )

        for lg in Log.objects.filter(key=str(pk), type__in=(5002,)):
            data[0]["events"].append([["title", "{}, {}".format(strdatetime(lg.time), lg.get_type_display())], ["Отмена", "{}, {}".format(lg.body, get_userdata(lg.user))]])
        for lg in Log.objects.filter(key=str(pk), type__in=(60000, 60001, 60002, 60003, 60004, 60005, 60006, 60007, 60008, 60009, 60010, 60011, 60022, 60023, 60024, 60025, 60026, 60027)):
            data[0]["events"].append([["title", lg.get_type_display()], ["Дата и время", strdatetime(lg.time)]])
        for tube in TubesRegistration.objects.filter(issledovaniya__napravleniye=dr).distinct():
            d = {"type": "Ёмкость №%s" % tube.number, "events": []}
            if tube.time_get is not None:
                d["events"].append([["title", strdatetime(tube.time_get) + " Забор"], ["Заборщик", get_userdata(tube.doc_get)]])
            for lg in Log.objects.filter(key=str(tube.number), type__in=(4000, 12, 11)).distinct():
                tdata = [["Приёмщик", get_userdata(lg.user)], ["title", strdatetime(lg.time) + " " + lg.get_type_display() + " (#%s)" % lg.pk]]
                if lg.body and lg.body != "":
                    tdata.append(["json_data", lg.body])
                d["events"].append(tdata)
            data.append(d)
        for iss in Issledovaniya.objects.filter(napravleniye=dr):
            d = {'type': "Исследование: %s (#%s)" % (iss.research.title, iss.pk), 'events': []}
            for lg in Log.objects.filter(key=str(iss.pk), type__in=(13, 14, 24)).distinct():
                tdata = [["Исполнитель", get_userdata(lg.user)], ["title", strdatetime(lg.time) + " " + lg.get_type_display() + " (#%s)" % lg.pk]]
                if lg.body and lg.body != "" and lg.type != 24:
                    tdata.append(["json_data", lg.body])
                d["events"].append(tdata)
            data.append(d)
        Log(key=str(pk), type=5000, body="", user=request.user.doctorprofile).save()
    return JsonResponse(data, safe=False)


@login_required
def check_direction(request):
    request_data = json.loads(request.body)
    pk = request_data.get("q", "-1") or -1

    return JsonResponse({"ok": Napravleniya.objects.filter(pk=pk).exists()})


@login_required
@group_required("Отправка результатов в организации")
def send_results_to_hospital(request):
    if not SettingManager.l2("send_orgs_email_results"):
        return status_response(False, "Отправка результатов в организации отключена")

    request_data = json.loads(request.body)
    hospital_pk = request_data.get("hospitalId")
    if not hospital_pk:
        return status_response(False, "Invalid hospital id")

    hospital = Hospitals.objects.get(pk=hospital_pk)

    if hospital.pk == request.user.doctorprofile.get_hospital_id():
        return status_response(False, "Нельзя отправить результаты в свою организацию")

    if not hospital.need_send_result:
        return status_response(False, "Отправка результатов в эту организацию отключена")

    if not hospital.email:
        return status_response(False, "У организации не указан email")

    directions_ids = request_data.get("directionsIds")

    for direction_id in directions_ids:
        n = Napravleniya.objects.get(pk=direction_id)
        if n.hospital != hospital:
            return status_response(False, "Направление №{} не принадлежит организации {}".format(n.pk, hospital.title))
        if not n.total_confirmed:
            return status_response(False, "Направление №{} не подтверждено".format(n.pk))

    directions_ids = list(set(directions_ids))
    directions_ids.sort(key=lambda x: Napravleniya.objects.get(pk=x).last_confirmed_at, reverse=True)

    if not directions_ids:
        return status_response(False, "Empty directions ids")

    directions_ids_chunks = [directions_ids[i : i + 20] for i in range(0, len(directions_ids), 20)]

    for directions_ids_chunk in directions_ids_chunks:
        ids_from = directions_ids_chunk[0]
        ids_to = directions_ids_chunk[-1]
        pdf = directions_pdf_result(directions_ids_chunk)
        filename = "results_{}_{}.pdf".format(ids_from, ids_to)
        file = ContentFile(base64.b64decode(pdf), name=filename)

        body_lines = [
            "Результаты с номерами от {} до {}".format(ids_from, ids_to),
            "",
        ]

        for direction_id in directions_ids_chunk:
            n = Napravleniya.objects.get(pk=direction_id)
            body_lines.append("Результат №{} от {}".format(n.pk, strdatetime(n.data_sozdaniya)))
            for iss in Issledovaniya.objects.filter(napravleniye=n):
                body_lines.append(" - {}".format(iss.research.title))
            body_lines.append("")

        body_lines.append("")

        body_lines.append("Отправлено из {}".format(request.user.doctorprofile.get_hospital_title()))
        body_lines.append("Отправлено в {}".format(hospital.title))
        body_lines.append("")
        body = "\n".join(body_lines)
        hospital.send_email_with_pdf_file("Результаты исследований", body, file)

        for direction_id in directions_ids_chunk:
            n = Napravleniya.objects.get(pk=direction_id)
            n.email_with_results_sent = True
            n.save(update_fields=["email_with_results_sent"])
            Log.log(
                direction_id,
                140000,
                request.user.doctorprofile,
                {
                    "hospital": hospital.title,
                    "hospital_id": hospital.pk,
                    "directions_ids": directions_ids_chunk,
                },
            )

    return status_response(True)


@login_required
@group_required("Отправка результатов в организации")
def get_directions_by_hospital_sent(request):
    request_data = json.loads(request.body)
    date = request_data["date"]
    hospital_pk = request_data["hospitalId"]
    d1 = try_strptime(date, ('%d.%m.%Y', '%Y-%m-%d'))
    start_date = datetime.combine(d1, dtime.min)
    end_date = datetime.combine(d1, dtime.max)
    if hospital_pk == -1:
        hospitlas_need_email_send = tuple(Hospitals.objects.values_list("pk", flat=True).filter(need_send_result=True).exclude(pk=request.user.doctorprofile.get_hospital_id()))
    else:
        hospitlas_need_email_send = (hospital_pk,)
    confirm_direction = get_confirm_direction_by_hospital(hospitlas_need_email_send, start_date, end_date)
    rows = []
    for obj in confirm_direction:
        rows.append(
            {
                "pk": obj.direction,
                "emailWasSent": obj.email_with_results_sent,
                "hospitalId": obj.hospital,
            }
        )
    return JsonResponse({"rows": rows})


@login_required
def meta_info(request):
    request_data = json.loads(request.body)
    res_direction = tuple(list(request_data["directions"]))
    if not res_direction:
        return JsonResponse({"rows": []})
    result = get_directions_meta_info(res_direction)
    lab_podr = get_lab_podr()
    lab_podr = [i[0] for i in lab_podr]
    type_slave_research = dict(HospitalService.TYPES)

    data_directions = []
    tmp_direction = {}
    last_direction = None

    for i in result:
        if last_direction != i.napravleniye_id and len(tmp_direction) > 0:
            data_directions.append(tmp_direction.copy())
            tmp_direction = {}
        tmp_direction["direction"] = i.napravleniye_id
        tmp_direction["researches"] = f"{tmp_direction.get('researches', '')} {i.title}"
        if i.is_paraclinic:
            tmp_direction["type"] = "Диагностика"
        elif i.is_doc_refferal:
            tmp_direction["type"] = "Консультация"
        elif i.is_stom:
            tmp_direction["type"] = "Стоматология"
        elif i.is_microbiology:
            tmp_direction["type"] = "Бак.исследование"
        elif i.is_gistology:
            tmp_direction["type"] = "Гистология"
        elif i.is_form:
            tmp_direction["type"] = "Произвольный протокол"

        if i.is_slave_hospital:
            tmp_direction["type"] = type_slave_research.get(i.site_type)
        tmp_direction["timeConfirm"] = i.ch_time_confirm
        last_direction = i.napravleniye_id

        tmp_direction["isLab"] = False
        tmp_direction["isDocReferral"] = True
        tmp_direction["isParaclinic"] = True

        if i.podrazdeleniye_id in lab_podr:
            tmp_direction["type"] = "Лаборатория"
            tmp_direction["isLab"] = True
            tmp_direction["isDocReferral"] = False
            tmp_direction["isParaclinic"] = False

    data_directions.append(tmp_direction.copy())
    sort_result = [{} for k in range(len(res_direction))]
    for i in data_directions:
        index_num = res_direction.index(i['direction'])
        sort_result[index_num] = i
    return JsonResponse({"rows": sort_result})


@login_required
def patient_open_case(request):
    request_data = json.loads(request.body)
    card_pk = request_data.get("card_pk", None)
    data_case = []
    date_start = datetime.now() - timedelta(days=60)
    date_end = datetime.now()

    if card_pk:
        open_case = get_patient_open_case_data(card_pk, date_start, date_end)
        data_case = []
        for o_case in open_case:
            n = Napravleniya.objects.filter(parent_case_id=o_case.iss_id).first()
            iss = Issledovaniya.objects.filter(napravleniye=n).first()
            if iss:
                title = iss.research.short_title if iss.research.short_title else iss.research.title
            else:
                title = "Случай пустой"
            data_case.append({"id": o_case.iss_id, "label": f"{title} от {o_case.date_create}"})

    data = {"data": data_case}
    return JsonResponse(data)
