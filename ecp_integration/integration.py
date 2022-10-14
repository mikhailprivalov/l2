import logging
from urllib.parse import urljoin, urlencode
import requests

from appconf.manager import SettingManager
import simplejson as json

from rmis_integration.client import Settings
from utils.dates import normalize_dash_date

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
        req = make_request_get("Person", query=f"Sess_id={sess_id}&Person_id={r['Person_id']}", sess_id=sess_id)
        patient = json.loads(req.content.decode())
        data_patient = patient.get('data')
        fio_patient = f'{data_patient[0]["PersonSurName_SurName"]} {data_patient[0]["PersonFirName_FirName"]} {data_patient[0]["PersonSecName_SecName"]}'
        time_table.append(
            {
                "uid": r["Person_id"],
                "patient": fio_patient,
                "slot": r["TimeTableGraf_id"],
                "timeStart": r["TimeTableGraf_begTime"].split(" ")[1][:5],
                "timeEnd": r["TimeTableGraf_begTime"].split(" ")[1][:5],
                "patientdata": data_patient[0],
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
