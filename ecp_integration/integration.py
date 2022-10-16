import logging
from urllib.parse import urljoin
import requests

from appconf.manager import SettingManager
import simplejson as json

from ecp_integration.sql_func import get_doctors_rmis_location_by_research
from rmis_integration.client import Settings
from utils.dates import normalize_dash_date
from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_url_ecp(path, query=""):
    if query is None:
        query = {}
    return urljoin(SettingManager.get("ecp_api_url", default='http://localhost/', default_type='s'), path) + (f'?{query}')


def get_headers_ecp(sess_id):
    return {'Authorization': f'Basic {sess_id}', 'Cookie': f'PHPSESSID={sess_id}'}


def make_request_get(path, query="", sess_id=""):
    if query is None:
        query = {}
    try:
        url = get_url_ecp(path, query=query)
        headers = get_headers_ecp(sess_id)
        data = requests.get(url, headers=headers)
        return data
    except Exception as e:
        logger.exception(e)
        return {}


def request_get_sess_id():
    login = Settings.get("login")
    password = Settings.get("password")
    data = make_request_get("user/login", query=f"Login={login}&Password={password}")
    return json.loads(data.content.decode()).get("sess_id")


def get_reserves_ecp(date, med_staff_fact_id):
    sess_id = request_get_sess_id()
    time_end = f"{date} 23:00:00"
    time_start = f"{date} 06:00:00"
    req = make_request_get(
        "TimeTableGraf/TimeTableGrafbyMedStaffFact",
        query=f"Sess_id={sess_id}&MedStaffFact_id={med_staff_fact_id}&TimeTableGraf_end={time_end}&TimeTableGraf_beg={time_start}",
        sess_id=sess_id,
    )
    result = json.loads(req.content.decode())
    time_table = []
    for r in result.get('data'):
        cache_key = f"ecp-fio:{r['Person_id']}"
        fio = cache.get(cache_key)
        if not fio:
            req = make_request_get("Person", query=f"Sess_id={sess_id}&Person_id={r['Person_id']}", sess_id=sess_id)
            patient = json.loads(req.content.decode())
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
    req = make_request_get("TimeTableGraf/TimeTableGrafStatus", query=f"Sess_id={sess_id}&Person_id={person_id}&TimeTableGraf_id={slot_id}", sess_id=sess_id)
    req_result = json.loads(req.content.decode())
    d = req_result['data'][0]
    req = make_request_get("TimeTableGraf/TimeTableGrafById", query=f"Sess_id={sess_id}&TimeTableGraf_id={slot_id}", sess_id=sess_id)
    req_result = json.loads(req.content.decode())
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
    req = make_request_get("Person", query=f"Sess_id={sess_id}&Person_id={person_id}", sess_id=sess_id)
    result = json.loads(req.content.decode())
    patient = result['data'][0]
    patient_snils = patient.get("PersonSnils_Snils", "")
    req = make_request_get(
        "PersonList",
        query=f"Sess_id={sess_id}&"
        f"PersonSurName_SurName={patient['PersonSurName_SurName']}&"
        f"PersonFirName_FirName={patient['PersonFirName_FirName']}&"
        f"PersonBirthDay_BirthDay={patient['PersonBirthDay_BirthDay']}&PersonSnils_Snils={patient_snils}",
        sess_id=sess_id,
    )
    result = json.loads(req.content.decode())
    individual = result['data'][0]
    if individual['Person_id'] == patient['Person_id'] and individual['PolisType_id'] == '2':
        patient['enp'] = individual['Polis_Num']
    return patient


def get_doctors_ecp_free_dates_by_research(research_pk, date_start, date_end):
    doctors = get_doctors_rmis_location_by_research(research_pk)
    doctors_has_free_date = {}
    unique_date = []
    for d in doctors:
        sess_id = request_get_sess_id()
        req = make_request_get(
            "TimeTableGraf/TimeTableGrafFreeDate", query=f"Sess_id={sess_id}&MedStaffFact_id={d.rmis_location}&TimeTableGraf_beg={date_start}&TimeTableGraf_end={date_end}", sess_id=sess_id
        )
        req_result = json.loads(req.content.decode())
        schedule_data = req_result['data']
        if len(schedule_data) > 0:
            doctors_has_free_date[d.rmis_location] = {"fio": f"{d.family} {d.name} {d.patronymic}", "pk": d.id, "dates": []}
            doctors_has_free_date[d.rmis_location]["dates"] = [s["TimeTableGraf_begTime"] for s in schedule_data]
            unique_date.extend(doctors_has_free_date[d.rmis_location]["dates"])

    return {"doctors_has_free_date": doctors_has_free_date, "unique_date": sorted(set(unique_date))}


def get_doctors_ecp_free_slots_by_date(rmis_location, date):
    sess_id = request_get_sess_id()
    req = make_request_get("TimeTableGraf/TimeTableGrafFreeTime", query=f"Sess_id={sess_id}&MedStaffFact_id={rmis_location}&TimeTableGraf_begTime={date}", sess_id=sess_id)
    req_result = json.loads(req.content.decode())
    free_slots = req_result['data']
    if len(free_slots) > 0:
        return sorted(free_slots, key=lambda k: k['TimeTableGraf_begTime'])
    return []
