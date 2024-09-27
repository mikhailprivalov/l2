import json
import logging
from urllib.parse import urljoin, urlencode

import requests

from appconf.manager import SettingManager

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
    return make_request(f"{url}/send-lab-result-ecp", data=json.dumps({"directions": directions}), gen_url=False, auth_token="a-super-secret-key")


def send_gistology_direction_to_ecp(directions) -> dict:
    url = SettingManager.get_api_ecp_base_url()
    return make_request(f"{url}/send-gistology-result", data=json.dumps({"directions": directions}), gen_url=False, auth_token="a-super-secret-key")


def send_medexam_to_ecp(directions) -> dict:
    url = SettingManager.get_api_ecp_base_url()
    return make_request(f"{url}/med-exam", data=json.dumps({"directions": directions}), gen_url=False, auth_token="a-super-secret-key")
