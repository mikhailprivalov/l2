import datetime

import magic
import pytz_deprecation_shim as pytz

from appconf.manager import SettingManager
from clients.models import HarmfulFactor
from external_system.models import InstrumentalResearchRefbook
from laboratory import settings
import simplejson as json
from dateutil.relativedelta import relativedelta
from django.core.files.uploadedfile import InMemoryUploadedFile
import directions.models as directions
from directory.models import Fractions
from laboratory.settings import (
    DEATH_RESEARCH_PK,
    DEF_LABORATORY_AUTH_PK,
    DEF_LABORATORY_LEGAL_AUTH_PK,
    ODII_METHODS,
    REMD_RESEARCH_USE_GLOBAL_LEGAL_AUTH,
    LEGAL_AUTH_CODE_POSITION,
    REMD_FIELDS_BY_TYPE_DOCUMENT,
    JSON_LOADS_FIELDS_CDA,
)

from results.sql_func import get_paraclinic_results_by_direction, get_laboratory_results_by_directions
from users.models import DoctorProfile
from utils.dates import normalize_dots_date
from directions.models import Napravleniya
from utils.nsi_directories import NSI


def get_json_protocol_data(pk, is_paraclinic=False):
    result_protocol = get_paraclinic_results_by_direction(pk)
    data = {}
    document = {}
    for r in result_protocol:
        if "{" in r.value and "}" in r.value:
            try:
                val = json.loads(r.value)
                if not val or not isinstance(val, dict):
                    pass
            except Exception:
                val = r.value
        else:
            val = r.value
        if "rows" in val:
            for k in val['rows']:
                count = 0
                for el in k:
                    if "{" in el and "}" in el:
                        try:
                            el = json.loads(el)
                            if not el or not isinstance(el, dict):
                                pass
                            else:
                                k[count] = el
                        except Exception:
                            pass
                    count += 1
        if isinstance(val, str):
            if val.strip() in ('-', ''):
                val = ""
        if r.title == "Страховая ОМС":
            nsi_smo_code = NSI.get("1.2.643.5.1.13.13.99.2.183_smo_id", None)
            if val and nsi_smo_code:
                smo_id = nsi_smo_code["values"][val.get("code", "")]
                val["id"] = smo_id
        data[r.title] = val

    iss = directions.Issledovaniya.objects.get(napravleniye_id=pk)

    if iss.research_id == DEATH_RESEARCH_PK:
        data_direct_death = data.get("а) Болезнь или состояние, непосредственно приведшее к смерти", None)
        if data_direct_death:
            period_befor_death = data_direct_death["rows"][0][0]
            type_period_befor_death = data_direct_death["rows"][0][1]
            date_death = data["Дата смерти"]
            time_death = data.get("Время смерти", "00:00")
            if period_befor_death and type_period_befor_death:
                data["Начало патологии"] = start_pathological_process(f"{date_death} {time_death}", int(period_befor_death), type_period_befor_death)
        data["Номер"] = f"{data['Префикс номера']}{data['Номер']}"
    doctor_confirm_obj = iss.doc_confirmation
    if iss.doc_confirmation.hospital.legal_auth_doc_id and SettingManager.get("use_def_hospital_legal_auth", default='false', default_type='b'):
        doctor_legal_confirm_obj = DoctorProfile.objects.get(pk=int(iss.doc_confirmation.hospital.legal_auth_doc_id))
    author_data = author_doctor(doctor_confirm_obj)

    legal_auth = data.get("Подпись от организации", None)
    legal_auth_data = legal_auth_get(legal_auth)
    if (
        legal_auth_data["positionCode"] not in LEGAL_AUTH_CODE_POSITION or "" in [legal_auth_data["positionCode"], legal_auth_data["positionName"], legal_auth_data["snils"]]
    ) and iss.research_id in REMD_RESEARCH_USE_GLOBAL_LEGAL_AUTH:
        legal_auth_data = author_doctor(doctor_legal_confirm_obj)
    else:
        legal_auth_data = author_data

    hosp_obj = doctor_confirm_obj.hospital
    hosp_oid = hosp_obj.oid

    if is_paraclinic:
        result_paraclinic = {"протокол": "", "заключение": "", "рекомендации": ""}
        for k, v in data.items():
            if k.lower() == "заключение":
                result_paraclinic["заключение"] = v
            if k.lower() == "рекомендации":
                result_paraclinic["рекомендации"] = v
            else:
                tmp_protocol = result_paraclinic["протокол"]
                tmp_protocol = f"{tmp_protocol} {k}-{v}"
                result_paraclinic["протокол"] = tmp_protocol
        if not result_paraclinic["заключение"]:
            for r in result_protocol:
                if r.group_title.lower() == "заключение":
                    result_paraclinic["заключение"] = f"{result_paraclinic.get('заключение')}; {r.value}"
        data = result_paraclinic

    if iss.research.is_doc_refferal or iss.research.is_form or iss.research.is_extract:
        try:
            val = data.get("Cостояние пациента", None)
            if not val or not isinstance(val, dict):
                pass
            else:
                data["Состояние код"] = val["code"]
                data["Состояние наименование"] = val["title"]
        except Exception:
            data["Состояние код"] = "1"
            data["Состояние наименование"] = "Удовлетворительное"

        try:
            val = data.get("Вредные факторы", None)
            if not val:
                pass
            else:
                harm_full_factors = val.split(";")
                harm_full_factors = [h.strip() for h in harm_full_factors]
                harm_full_factors_object = [{"nsi_id": hf.nsi_id, "nsi_title": hf.description, "code": hf.title} for hf in HarmfulFactor.objects.filter(title__in=harm_full_factors)]
                data["Вредные факторы"] = harm_full_factors_object
        except Exception:
            pass

        try:
            val = data.get("Группа здоровья", None)
            if not val or not isinstance(val, dict):
                pass
            else:
                data["Группа здоровья код"] = val["code"]
                data["Группа здоровья наименование"] = val["title"]
        except Exception:
            pass

        for i in REMD_FIELDS_BY_TYPE_DOCUMENT.get(iss.research.generator_name, []):
            data[i] = "-"
        for r in result_protocol:
            if r.value:
                if r.cda_title_field is None:
                    data[r.cda_title_group] = f"{data.get(r.cda_title_group)}; {r.title}:{r.value}"
                else:
                    data[r.cda_title_field] = f"{r.value.strip()}"
                data = check_title_field(data, r)
        data["Код услуги"] = iss.research.code
        if not data.get("Состояние код"):
            data["Состояние код"] = "1"
            data["Состояние наименование"] = "Удовлетворительное"
        if not data.get("Дата осмотра"):
            data["Дата осмотра"] = iss.medical_examination.strftime("%Y-%m-%d")
        if data.get("Дата заключения"):
            val = data.get("Дата заключения")
            data["Дата заключения"] = normalize_dots_date(val).replace("-", "")
        data = add_absent_field(data, iss.research)

    direction_params_obj = directions.DirectionParamsResult.objects.filter(napravleniye_id=pk)
    direction_params = {}
    for dp in direction_params_obj:
        try:
            val = json.loads(dp.value)
            if not val or not isinstance(val, dict):
                pass
        except Exception:
            val = dp.value
        direction_params[dp.title] = val

    document["id"] = pk
    time_confirm = iss.time_confirmation
    confirmed_time = time_confirm.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%Y%m%d%H%M')
    document["confirmedAt"] = f"{confirmed_time}+0800"
    document["legalAuthenticator"] = legal_auth_data
    document["author"] = author_data
    document["content"] = data
    document["content"]["Код ОКПО"] = hosp_obj.okpo
    document["oidMo"] = hosp_oid
    document["organization"] = organization_get(hosp_obj)
    document["orgName"] = hosp_obj.title
    document["tel"] = hosp_obj.phones
    document["direction_params"] = direction_params
    document["nsi_id"] = iss.research.nsi_id
    nsi_res = InstrumentalResearchRefbook.objects.filter(code_nsi=iss.research.nsi_id).first()
    document["nsi_title"] = nsi_res.title if nsi_res else ""
    document["odii_code_method"] = ODII_METHODS.get(nsi_res.method) if nsi_res else None
    document["codeService"] = iss.research.code
    document["oidDepartment"] = iss.doc_confirmation.podrazdeleniye.oid
    return document


def add_absent_field(data, research_data):
    tmp_data = {}
    if research_data.is_extract:
        for k in data.keys():
            if k == "вэ-Состояние при выписке" and data[k] == "-":
                tmp_data[k] = {"code": "1", "title": "Удовлетворительное"}
            elif k == "вэ-Состояние при поступлении" and data[k] == "-":
                tmp_data[k] = {"code": "1", "title": "Удовлетворительное"}
            elif k == "вэ-Вид госпитализации" and data[k] == "-":
                tmp_data[k] = {"code": "1", "title": "Плановая госпитализация"}
            elif k == "вэ-Исход" and data[k] == "-":
                tmp_data[k] = {"code": "1", "title": "Выписан"}
            elif k == "вэ-Исход" and data[k] != "-":
                out_res = NSI.get("1.2.643.5.1.13.13.11.1373")["values"]
                for key, val in out_res.items():
                    if val.lower() == data[k].lower():
                        tmp_data[k] = {"code": key, "title": val}
            elif k == "вэ-результат стационарного лечения" and data[k] == "-":
                tmp_data[k] = {"code": "3", "title": "Без изменения"}
            elif k == "вэ-результат стационарного лечения" and data[k] != "-":
                out_res = NSI.get("1.2.643.5.1.13.13.11.1046")["values"]
                for key, val in out_res.items():
                    if val.lower() == data[k].lower():
                        tmp_data[k] = {"code": key, "title": val}
            elif k == "вэ-Время окончания":
                data[k] = data[k].replace(":", "")
            elif k == "вэ-Время начала":
                data[k] = data[k].replace(":", "")
            elif k == "вэ-Дата начала госпитализации":
                data[k] = normalize_dots_date(data[k]).replace("-", "")
            elif k == "вэ-Дата выписки":
                data[k] = data[k].replace("-", "")
            elif k == "вэ-Проведенное лечение":
                res_treatment = json.loads(data[k])
                data[k] = " ".join([f"{res_t['pharmaTitle']} - {res_t['mode']};" for res_t in res_treatment])

    return {**data, **tmp_data}


def check_title_field(data, r):
    if r.cda_title_field == "Шифр по МКБ-10":
        diag_data = r.value.split(" ")
        data["Шифр по МКБ-10 код"] = diag_data.pop(0)
        data["Шифр по МКБ-10 наименование"] = " ".join(diag_data)
    if r.cda_title_field in JSON_LOADS_FIELDS_CDA:
        tmp_data = json.loads(r.value)
        data[f"{r.cda_title_field} код"] = tmp_data["code"]
        data[f"{r.cda_title_field} наименование"] = tmp_data["title"]
    return data


def get_json_labortory_data(pk):
    result_protocol = get_laboratory_results_by_directions(tuple([pk]))
    document = {}
    confirmed_at = ""
    date_reiceve = ""
    data = []
    prev_research_title = ""
    count = 0
    tests = []
    author_data = None
    iss = None
    for k in result_protocol:
        iss_s = directions.Issledovaniya.objects.get(pk=k.iss_id)
        if not iss_s.doc_confirmation:
            return {}
        iss = iss_s
        next_research_title = iss.research.title
        if (prev_research_title != next_research_title) and count != 0:
            if len(tests) > 0:
                data.append({"title": prev_research_title, "tests": tests, "confirmedAt": confirmed_at, "receivedAt": date_reiceve, "author_data": author_data})
            tests = []
        author_data = author_doctor(iss.doc_confirmation)
        time_confirm = iss.time_confirmation
        confirmed_time = time_confirm.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%Y%m%d%H%M')
        fraction_id = k.fraction_id
        frac_obj = Fractions.objects.get(pk=fraction_id)
        if not frac_obj.unit or not frac_obj.fsli:
            continue
        unit_obj = frac_obj.unit
        unit_val = {"code": unit_obj.code, "full_title": unit_obj.title, "ucum": unit_obj.ucum, "short_title": unit_obj.short_title}
        flsi_param = {"code": frac_obj.fsli, "title": frac_obj.title}
        result_val = k.value.replace(",", ".") if k.value else ""
        confirmed_at = f"{confirmed_time}+0800"
        date_reiceve = normalize_dots_date(k.date_confirm).replace("-", "")
        date_reiceve = f"{date_reiceve}0800+0800"
        tests.append({"unit_val": unit_val, "flsi_param": flsi_param, "result_val": result_val})
        prev_research_title = next_research_title
        count += 1
    if len(tests) > 0:
        data.append({"title": prev_research_title, "tests": tests, "confirmedAt": confirmed_at, "receivedAt": date_reiceve, "author_data": author_data})

    if not iss:
        return {}

    hosp_obj = iss.doc_confirmation.hospital
    hosp_oid = hosp_obj.oid

    document["id"] = pk
    legal_auth_data = legal_auth_get({"id": iss.legal_authenticator_id})
    document["legalAuthenticator"] = legal_auth_data
    document["author"] = author_data
    document["content"] = {}
    document["content"]["Лаборатория"] = data
    document["content"]["Код ОКПО"] = hosp_obj.okpo
    document["content"]["payment"] = {"code": "1", "title": "Средства обязательного медицинского страхования"}
    document["oidMo"] = hosp_oid
    document["orgName"] = hosp_obj.title
    direction_obj = Napravleniya.objects.get(pk=pk)
    direction_create = direction_obj.data_sozdaniya
    direction_create = direction_create.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%Y%m%d%H%M')
    document["createdAt"] = f"{direction_create}+0800"
    document["lastConfirmedAt"] = f"{confirmed_at}"
    document["confirmedAt"] = f"{confirmed_at}"
    document["organization"] = organization_get(hosp_obj)

    return document


def organization_get(hosp_obj_f):
    return {
        "name": hosp_obj_f.title,
        "tel": hosp_obj_f.phones if hosp_obj_f.phones else "",
        "address": {
            "text": hosp_obj_f.address if hosp_obj_f.address else "г. Иркутск",
            "subjectCode": "38",
            "subjectName": "Иркутская область",
        },
    }


def author_doctor(doctor_confirm_obj, is_recursion=False):
    author = {}
    author["id"] = doctor_confirm_obj.pk
    author["positionCode"] = doctor_confirm_obj.position.n3_id if doctor_confirm_obj.position else ""
    author["positionName"] = doctor_confirm_obj.position.title if doctor_confirm_obj.position else ""
    author["snils"] = doctor_confirm_obj.snils if doctor_confirm_obj.snils else ""
    if "" in [author["positionCode"], author["positionName"], author["snils"]] and DEF_LABORATORY_AUTH_PK and not is_recursion:
        return author_doctor(DoctorProfile.objects.get(pk=DEF_LABORATORY_AUTH_PK), True)
    author["name"] = {}
    author["name"]["family"] = doctor_confirm_obj.family
    author["name"]["name"] = doctor_confirm_obj.name
    author["name"]["patronymic"] = doctor_confirm_obj.patronymic
    author["rmis_login"] = doctor_confirm_obj.rmis_login
    author["rmis_password"] = doctor_confirm_obj.rmis_password
    author["rmis_employee_id"] = doctor_confirm_obj.rmis_employee_id
    author["rmis_resource_id"] = doctor_confirm_obj.rmis_resource_id
    author["rmis_department_id"] = doctor_confirm_obj.podrazdeleniye.ecp_code
    additional_data = None
    if doctor_confirm_obj.additional_info:
        if "{" in doctor_confirm_obj.additional_info and "}" in doctor_confirm_obj.additional_info:
            try:
                additional_data = json.loads(doctor_confirm_obj.additional_info)
                if not additional_data or not isinstance(additional_data, dict):
                    additional_data = {}
            except Exception:
                additional_data = None

    author["additional_data"] = additional_data

    return author


def legal_auth_get(legal_auth_doc, is_recursion=False, as_uploading_data=False):
    legal_auth = {"id": "", "snils": "", "positionCode": "", "positionName": "", "name": {"family": "", "name": "", "patronymic": ""}}
    if legal_auth_doc and legal_auth_doc["id"]:
        id_doc = legal_auth_doc["id"]
        legal_doctor = DoctorProfile.objects.get(pk=id_doc)
        if as_uploading_data:
            legal_auth = {
                "id": legal_doctor.pk,
                **legal_auth,
                **legal_doctor.uploading_data,
            }
        else:
            legal_auth["id"] = legal_doctor.pk
            legal_auth["snils"] = legal_doctor.snils
            legal_auth["positionCode"] = legal_doctor.position.n3_id
            legal_auth["positionName"] = legal_doctor.position.title
            legal_auth["name"]["family"] = legal_doctor.family
            legal_auth["name"]["name"] = legal_doctor.name
            legal_auth["name"]["patronymic"] = legal_doctor.patronymic
    if (
        (legal_auth["positionCode"] not in LEGAL_AUTH_CODE_POSITION or "" in [legal_auth["positionCode"], legal_auth["positionName"], legal_auth["snils"]])
        and DEF_LABORATORY_LEGAL_AUTH_PK
        and not is_recursion
    ):
        return legal_auth_get({"id": DEF_LABORATORY_LEGAL_AUTH_PK}, True, as_uploading_data=as_uploading_data)
    return legal_auth


def start_pathological_process(date_death, time_data, type_period):
    dt = datetime.datetime.strptime(date_death, '%Y-%m-%d %H:%M')
    period = {
        "часов": relativedelta(hours=-time_data),
        "минут": relativedelta(minutes=-time_data),
        "дней": relativedelta(days=-time_data),
        "суток": relativedelta(days=-time_data),
        "месяцев": relativedelta(months=-time_data),
        "лет": relativedelta(years=-time_data),
    }
    delta = dt + period[type_period]
    delta.strftime("%Y%m%d%H:%M:%S")
    return f"{delta.strftime('%Y%m%d%H%M')}+0800"


def check_type_file(file_path=None, file_in_memory: InMemoryUploadedFile = None):
    first_bytes = b''
    if file_path:
        first_bytes = open(file_path).read(2048)
    elif file_in_memory:
        first_bytes = file_in_memory.open().read(2048)
    type_file = magic.from_buffer(first_bytes).lower()
    return "pdf" in type_file or "jpeg" in type_file
