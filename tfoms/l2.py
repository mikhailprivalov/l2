import logging
from urllib.parse import urljoin

import requests

from appconf.manager import SettingManager

logger = logging.getLogger(__name__)


def get_url(path):
    return urljoin(SettingManager.get("l2_patients_url", default='http://localhost/if', default_type='s'), path)


def get_headers():
    return {"Authorization": "Bearer {}".format(SettingManager.get("l2_patients_token", default='token', default_type='s'))}


def make_request(path, json_data=None):
    if json_data is None:
        json_data = {}
    text_resp = None
    try:
        url = get_url(path)
        headers = get_headers()
        data = requests.post(url, headers=headers, json=json_data)
        text_resp = data.text
        data = data.json()
        return data
    except Exception as e:
        logger.exception(e)
        logger.exception(text_resp)
        return {}


def check_l2_enp(enp) -> dict:
    data = make_request("check-enp", {"enp": enp, "check_mode": "l2-enp"})
    return data


def check_l2_patient(family, name, patronymic, bd) -> dict:
    data = make_request("check-enp", {"family": family, "name": name, "patronymic": patronymic, "bd": bd, "check_mode": "l2-enp-full"})
    return data
