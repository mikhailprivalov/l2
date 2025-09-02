import json
import logging
from urllib.parse import urljoin, urlencode

import requests

from appconf.manager import SettingManager
from laboratory.settings import API_SERVER_SEND_PARACLINIC_DIRECTION

logger = logging.getLogger(__name__)


def get_url(path, query=None):
    if query is None:
        query = {}
    base = SettingManager.get_l2vi_base_url()
    if not base or base == 'empty':
        return {}
    return urljoin(base, path) + ('?{}'.format(urlencode(query)) if query else '')


def make_request(path, query=None, as_json=True, gen_url=True, auth_token=None, **kwargs):
    if query is None:
        query = {}
    try:
        if gen_url:
            url = get_url(path, query=query)
        else:
            url = path
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        data = requests.post(url, headers=headers, **kwargs)
        if as_json:
            return data.json()
        return data.text
    except Exception as e:
        print(e)  # noqa: T001
        return {}


def gen_cda_xml(pk: int) -> dict:
    return make_request('/perform', data=json.dumps({"pk": pk, "mode": "genXml"}))


def send_cda_xml(pk: int, xml: str) -> dict:
    return make_request('/perform', data=json.dumps({"pk": pk, "mode": "sendXml", "xml": xml}))


def send_lab_direction_to_ecp(directions) -> dict:
    url = SettingManager.get_api_ecp_base_url()
    path = SettingManager.get("endpoint_ecp_send_lab", default='', default_type='s')
    enpoint = 'send-lab-result-ecp'
    if path:
        enpoint = path
    return make_request(f"{url}/{enpoint}", data=json.dumps({"directions": directions}), gen_url=False, auth_token="a-super-secret-key")


def search_patient_to_ecp(data) -> dict:
    url = SettingManager.get_api_ecp_base_url()
    return make_request(f"{url}/patient-search-ecp", data=json.dumps(data), gen_url=False, auth_token="a-super-secret-key")


def send_paraclinic_direction_to_ecp(directions) -> dict:
    url = API_SERVER_SEND_PARACLINIC_DIRECTION
    return make_request(f"{url}/send-paraclinic-direction", data=json.dumps({"dirsToUpload": directions}), gen_url=False, auth_token="a-super-secret-key")


def send_gistology_direction_to_ecp(directions) -> dict:
    url = SettingManager.get_api_ecp_base_url()
    return make_request(f"{url}/send-gistology-result", data=json.dumps({"dirsToUpload": directions}), gen_url=False, auth_token="a-super-secret-key")


def send_medexam_to_ecp(directions) -> dict:
    url = SettingManager.get_api_ecp_base_url()
    return make_request(f"{url}/med-exam", data=json.dumps({"directions": directions}), gen_url=False, auth_token="a-super-secret-key")
