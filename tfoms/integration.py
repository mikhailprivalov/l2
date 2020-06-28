from typing import List
from urllib.parse import urljoin, urlencode

import requests

from appconf.manager import SettingManager


def get_url(path, query=None):
    if query is None:
        query = {}
    return urljoin(SettingManager.get("tfoms_api_url", default='http://localhost/', default_type='s'), path) + ('?{}'.format(urlencode(query)) if query else '')


def get_headers():
    return {"Authorization": "Bearer {}".format(SettingManager.get("tfoms_api_token", default='token', default_type='s'))}


def make_request(path, query=None):
    if query is None:
        query = {}
    try:
        url = get_url(path, query=query)
        headers = get_headers()
        return requests.post(url, headers=headers).json()
    except:
        return {}


def match_patient(family, name, patronymic, birthday) -> List[dict]:
    q = {
        "family": family,
        "name": name,
        "birthdate": birthday,
    }

    if patronymic:
        q["patronymic"] = patronymic

    return make_request("match-patient", q)


def match_enp(enp) -> dict:
    return make_request("match-patient-by-enp", {"enp": enp})
