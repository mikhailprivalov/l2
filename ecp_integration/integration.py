import logging
from urllib.parse import urljoin
import requests

from appconf.manager import SettingManager
import simplejson as json

from ecp_integration.sql_func import get_doctors_rmis_location_by_research
from laboratory.utils import current_time
from rmis_integration.client import Settings
from utils.dates import normalize_dash_date
from django.core.cache import cache
from laboratory.settings import RMIS_PROXY
from datetime import timedelta
import datetime

logger = logging.getLogger(__name__)


def get_url_ecp(path, query=""):
    if query is None:
        query = {}
    return urljoin(SettingManager.get("ecp_api_url", default='http://localhost/', default_type='s'), path) + (f'?{query}')


def get_headers_ecp(sess_id):
    return {'Authorization': f'Basic {sess_id}', 'Cookie': f'PHPSESSID={sess_id}'}


def make_request_get(path, query="", sess_id="", method="GET", get_sess_id=False):
    if query is None:
        query = {}
    try:
        url = get_url_ecp(path, query=query)
        headers = get_headers_ecp(sess_id)
        data = requests.request(method, url, headers=headers, proxies=RMIS_PROXY)
        if get_sess_id:
            return json.loads(data.content.decode()).get("sess_id")
        else:
            return json.loads(data.content.decode())
    except Exception as e:
        logger.exception(e)
        return {}


def request_get_sess_id():
    login = Settings.get("login")
    password = Settings.get("password")
    data = make_request_get("user/login", query=f"Login={login}&Password={password}", get_sess_id=True)
    return data


def get_reserves_ecp(date, med_staff_fact_id):
    sess_id = request_get_sess_id()
    time_end = f"{date} 23:00:00"
    time_start = f"{date} 06:00:00"
    result = make_request_get(
        "TimeTableGraf/TimeTableGrafbyMedStaffFact",
        query=f"Sess_id={sess_id}&MedStaffFact_id={med_staff_fact_id}&TimeTableGraf_end={time_end}&TimeTableGraf_beg={time_start}",
        sess_id=sess_id,
    )
    time_table = []
    for r in result.get('data') or []:
        cache_key = f"ecp-fio:{r['Person_id']}"
        fio = cache.get(cache_key)
        if not fio:
            patient = make_request_get("Person", query=f"Sess_id={sess_id}&Person_id={r['Person_id']}", sess_id=sess_id)
            data_patient = patient.get('data')
            fio_parts = [
                data_patient[0].get('PersonSurName_SurName'),
                data_patient[0].get('PersonFirName_FirName'),
                data_patient[0].get('PersonSecName_SecName'),
            ]
            fio = " ".join([part for part in fio_parts if part])
            cache.set(cache_key, fio, 60 * 60 * 6)
        time_table.append(
            {
                "uid": r["Person_id"],
                "patient": fio,
                "slot": r["TimeTableGraf_id"],
                "timeStart": r["TimeTableGraf_begTime"].split(" ")[1][:5],
                "timeEnd": r["TimeTableGraf_begTime"].split(" ")[1][:5],
            }
        )
    return sorted(time_table, key=lambda k: k['timeStart'])


def get_slot_ecp(person_id, slot_id):
    sess_id = request_get_sess_id()
    req_result = make_request_get("TimeTableGraf/TimeTableGrafStatus", query=f"Sess_id={sess_id}&Person_id={person_id}&TimeTableGraf_id={slot_id}", sess_id=sess_id)
    d = req_result['data'][0]
    req_result = make_request_get("TimeTableGraf/TimeTableGrafById", query=f"Sess_id={sess_id}&TimeTableGraf_id={slot_id}", sess_id=sess_id)
    r = req_result['data'][0]
    date_time_data = r["TimeTableGraf_begTime"].split(" ")
    dash_date = normalize_dash_date(date_time_data[0])
    date_time = date_time_data[1][:5]
    return (
        {
            "status": d["EvnStatus_id"],
            "datetime": f"{dash_date} {date_time}",
        }
        if d
        else {}
    )


def search_patient_ecp_by_person_id(person_id):
    sess_id = request_get_sess_id()
    result = make_request_get("Person", query=f"Sess_id={sess_id}&Person_id={person_id}", sess_id=sess_id)
    patient = result['data'][0]
    patient_snils = patient.get("PersonSnils_Snils", "")
    result = make_request_get(
        "PersonList",
        query=f"Sess_id={sess_id}&"
        f"PersonSurName_SurName={patient['PersonSurName_SurName']}&"
        f"PersonFirName_FirName={patient['PersonFirName_FirName']}&"
        f"PersonBirthDay_BirthDay={patient['PersonBirthDay_BirthDay']}&PersonSnils_Snils={patient_snils}",
        sess_id=sess_id,
    )
    individual = result['data'][0]
    if individual['Person_id'] == patient['Person_id'] and individual['PolisType_id'] in ['2', '4']:
        patient['enp'] = individual['Polis_Num']
    return patient


def get_doctors_ecp_free_dates_by_research(research_pk, date_start, date_end, hospital_id):
    doctors = get_doctors_rmis_location_by_research(research_pk, hospital_id)
    doctors_has_free_date = {}
    unique_date = []
    for d in doctors:
        sess_id = request_get_sess_id()
        if "@R" in d.rmis_location:
            key_time = "TimeTableResource_begTime"
            rmis_location_resource = d.rmis_location[:-2]
            date_start_r = f"{date_start} 08:00:00"
            date_end_r = f"{date_end} 23:00:00"
            req_result = make_request_get(
                "TimeTableResource/TimeTableResourceFreeDateTime",
                query=f"Sess_id={sess_id}&Resource_id={rmis_location_resource}&TimeTableResource_beg={date_start_r}&TimeTableResource_end={date_end_r}",
                sess_id=sess_id,
            )
        else:
            key_time = "TimeTableGraf_begTime"
            req_result = make_request_get(
                "TimeTableGraf/TimeTableGrafFreeDate",
                query=f"Sess_id={sess_id}&MedStaffFact_id={d.rmis_location}&TimeTableGraf_beg={date_start}&TimeTableGraf_end={date_end}",
                sess_id=sess_id,
            )
        schedule_data = req_result['data']
        if len(schedule_data) > 0:
            message = ""
            if d.age_limit > -1:
                years = d.age_limit // 12
                months = d.age_limit % 12
                message_parts = ['не старше']
                letter_year = "г."
                if years > 0:
                    if int(str(years)[-1]) > 4 or int(str(years)[-1]) == 0:
                        letter_year = "л."
                    message_parts.append(f"{years}{letter_year}")
                if months > 0:
                    message_parts.append(f"{months}м.")
                message = ' '.join(message_parts)
            district = d.district_title if d.district_title else ""
            doctors_has_free_date[d.rmis_location] = {
                "fio": f"{district} {d.family} {d.name[:1]}. {d.patronymic[:1]}. {message}".strip(),
                "pk": d.id,
                "dates": [],
                "message_age_limit": message,
            }
            doctors_has_free_date[d.rmis_location]["dates"] = [s[key_time][:10] for s in schedule_data]
            unique_date.extend(doctors_has_free_date[d.rmis_location]["dates"])
    return {"doctors_has_free_date": doctors_has_free_date, "unique_date": sorted(set(unique_date))}


def get_doctor_ecp_free_slots_by_date(rmis_location, date):
    sess_id = request_get_sess_id()
    if "@R" in rmis_location:
        key_time = "TimeTableResource_begTime"
        type_slot = "TimeTableResource_id"
        rmis_location_resource = rmis_location[:-2]
        date = f"{date} 08:00:00"
        req_result = make_request_get(
            "TimeTableResource/TimeTableResourceFreeDateTime", query=f"Sess_id={sess_id}&Resource_id={rmis_location_resource}&TimeTableResource_beg={date}", sess_id=sess_id
        )
    else:
        key_time = "TimeTableGraf_begTime"
        type_slot = "TimeTableGraf_id"
        req_result = make_request_get("TimeTableGraf/TimeTableGrafFreeTime", query=f"Sess_id={sess_id}&MedStaffFact_id={rmis_location}&TimeTableGraf_begTime={date}", sess_id=sess_id)
    free_slots = req_result['data']
    if len(free_slots) > 0:
        slots = sorted(free_slots, key=lambda k: k[key_time])
        free_slots_params = [{"pk": x[type_slot], "title": datetime.datetime.strptime(x[key_time], '%Y-%m-%d %H:%M:%S').strftime('%H:%M'), "typeSlot": type_slot} for x in slots]
        if type_slot == "TimeTableGraf_id":
            for param in free_slots_params:
                slot_type_id = get_time_table_graf_by_id(param["pk"], sess_id)
                param["slotTypeId"] = slot_type_id
        return free_slots_params
    return []


def get_time_table_graf_by_id(graf_id, sess_id):
    req_result = make_request_get("TimeTableGraf/TimeTableGrafById", query=f"Sess_id={sess_id}&TimeTableGraf_id={graf_id}", sess_id=sess_id)
    graf_data = req_result['data']
    if len(graf_data) > 0:
        return graf_data[0]['TimeTableType_id']
    return ""

def register_patient_ecp_slot(patient_ecp_id, slot_id, slot_type):
    sess_id = request_get_sess_id()
    req_result = None
    if slot_type == "TimeTableGraf_id":
        req_result = make_request_get("TimeTableGraf/TimeTableGrafWrite", query=f"Sess_id={sess_id}&Person_id={patient_ecp_id}&TimeTableGraf_id={slot_id}", sess_id=sess_id, method="POST")
    elif slot_type == "TimeTableResource_id":
        req_result = make_request_get(
            "TimeTableResource/TimeTableResourceWrite", query=f"Sess_id={sess_id}&Person_id={patient_ecp_id}&TimeTableResource_id={slot_id}", sess_id=sess_id, method="POST"
        )
    if req_result:
        register_result = req_result['data']
        if req_result['error_code'] == 0 and register_result[slot_type] == slot_id and patient_ecp_id == register_result['Person_id']:
            return {'register': True}

    return {'register': False, "message": "Неудачная попытка записи"}


def search_patient_ecp_by_fio(patient):
    sess_id = request_get_sess_id()
    result = make_request_get(
        "PersonList",
        query=f"Sess_id={sess_id}&"
        f"PersonSurName_SurName={patient['family']}&"
        f"PersonFirName_FirName={patient['name']}&"
        f"PersonSecName_SecName={patient['patronymic']}&"
        f"PersonBirthDay_BirthDay={patient['birthday']}&PersonSnils_Snils={patient['snils']}",
        sess_id=sess_id,
    )
    if not result or not result.get("data"):
        return None
    individual = result['data'][0]
    return individual['Person_id']


def get_ecp_time_table_list_patient(patient_ecp_id):
    sess_id = request_get_sess_id()
    current_date = current_time()
    start_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date = (current_date + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    req_result = make_request_get("TimeTableListbyPatient", query=f"Sess_id={sess_id}&Person_id={patient_ecp_id}&TimeTable_beg={start_date}&TimeTable_end={end_date}", sess_id=sess_id)
    result_tt = req_result['data']['TimeTable']
    if len(result_tt) > 0:
        return [
            {
                "date": normalize_dash_date(i['TimeTable_begTime'].split(" ")[0], short_year=True),
                "time": i['TimeTable_begTime'].split(" ")[1][:5],
                "Post_name": i['Post_name'],
                "TimeTable_id": i['TimeTable_id'],
                "full_time": i['TimeTable_begTime'],
                "rmis_location": i["MedStaffFact_id"],
                "type_slot": "graf",
            }
            for i in result_tt
        ]
    return []


def get_ecp_evn_direction(patient_ecp_id):
    sess_id = request_get_sess_id()
    current_date = current_time()
    end_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
    start_date = (current_date - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    req_result = make_request_get(
        "EvnDirection", query=f"Sess_id={sess_id}&Person_id={patient_ecp_id}&EvnDirection_beg={start_date}&EvnDirection_end={end_date}&DirType_id=10", sess_id=sess_id
    )
    direction_time_table = []
    if req_result and len(req_result['data']) > 0:
        for i in req_result['data']:
            if i["TimeTableResource_id"]:
                req_result_resource = make_request_get("TimeTableResourceById", query=f"Sess_id={sess_id}&TimeTableResource_id={i['TimeTableResource_id']}", sess_id=sess_id)
                if len(req_result_resource['data']) > 0:
                    date_time_resource = req_result_resource['data'][0]['TimeTableResource_begTime']
                    if date_time_resource >= end_date:
                        direction_time_table.append(
                            {
                                "date": normalize_dash_date(date_time_resource.split(" ")[0], short_year=True),
                                "time": date_time_resource.split(" ")[1][:5],
                                "Post_name": i['Resource_Name'],
                                "TimeTable_id": i['TimeTableResource_id'],
                                "full_time": date_time_resource,
                                "rmis_location": i["Resource_id"],
                                "type_slot": "resource",
                            }
                        )
    return direction_time_table


def cancel_ecp_patient_record(time_table_id, type_slot, reason_cancel=1):
    sess_id = request_get_sess_id()
    if type_slot != "resource":
        del_result = make_request_get("TimeTable", query=f"Sess_id={sess_id}&TimeTable_id={time_table_id}&TimeTableSource=Graf&FailCause={reason_cancel}", sess_id=sess_id, method="DELETE")
        if del_result.get("error_code") == 0:
            return True
    else:
        direction_data = make_request_get("TimeTableResourceById", query=f"Sess_id={sess_id}&TimeTableResource_id={time_table_id}", sess_id=sess_id)
        if len(direction_data['data']) > 0:
            evn_direction_id = direction_data['data'][0].get('EvnDirection_id', '')
            cancel_direction = make_request_get("EvnDirectionCancel", query=f"Sess_id={sess_id}&EvnDirection_id={evn_direction_id}", sess_id=sess_id, method="PUT")
            if cancel_direction["error_code"] == 0:
                return True
    return False
