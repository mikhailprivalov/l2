import logging
from typing import List, Optional
from urllib.parse import urljoin, urlencode

import requests

from appconf.manager import SettingManager
from tfoms.l2 import check_l2_enp

logger = logging.getLogger(__name__)


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
        data = requests.post(url, headers=headers).json()
        return data
    except Exception as e:
        print(e)
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


def match_enp(enp) -> Optional[dict]:
    logger.exception(f"tfms: match enp: {enp}")
    if SettingManager.get("l2_patients_is_active", default='f', default_type='b'):
        logger.exception("l2_patients_is_active")
        resp = check_l2_enp(enp)
        logger.exception(f"resp: {resp}")
        if not isinstance(resp, dict) or not resp.get('ok') or not resp.get('patient_data'):
            return None
        return resp.get('patient_data')
    data = make_request("match-patient-by-enp-set2", {"enp": enp})
    if isinstance(data, list) and len(data) > 0:
        return data[0]
    return data
