import logging
from typing import List, Optional
from urllib.parse import urljoin, urlencode
import requests
from appconf.manager import SettingManager
import simplejson as json

from rmis_integration.client import Settings

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
        print(e)  # noqa: T001
        return {}


def request_get_sess_id():
    login = Settings.get("login")
    password = Settings.get("password")
    data = make_request_get("user/login", query=f"Login={login}&Password={password}")
    return json.loads(data.content.decode()).get("sess_id")


def get_timetable_doctor(date, med_staff_fact_id):
    sess_id = request_get_sess_id()
    # # med_staff_fact_id = 380101000019040
    time_end = f"{date} 23:00:00"
    time_start = f"{date} 06:00:00"
    req = make_request_get("TimeTableGraf/TimeTableGrafbyMedStaffFact", query=f"Sess_id={sess_id}&MedStaffFact_id={med_staff_fact_id}&TimeTableGraf_end={time_end}&TimeTableGraf_beg={time_start}", sess_id=sess_id)
    result = json.loads(req.content.decode())
    print(result.get('data'))
    # time_table = {}
    # for r in result.get('data'):
    #     url_patient = f"http://ecp38.is-mis.ru/api//Person?Sess_id={sess_id}&Person_id="
    #     url_patient = f"{url_patient}{r['Person_id']}"
    #     req = requests.get(url_patient, headers=headers)
    #     result = json.loads(req.content.decode())
    #     print(result)
    #     patient_data = result.get('data')[0]
    #     time_table[r.get('TimeTableGraf_begTime')] = {
    #         'TimeTableGraf_id': r['TimeTableGraf_id'],
    #         'Person_id': r['Person_id'],
    #         'fio': f'{patient_data["PersonSurName_SurName"]} {patient_data["PersonFirName_FirName"]} {patient_data["PersonSecName_SecName"]}'
    #     }
    #
    # data = sorted(time_table.keys())
    # print(time_table)
