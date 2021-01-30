import logging
from urllib.parse import urljoin

import requests

from appconf.manager import SettingManager

logger = logging.getLogger(__name__)


def get_url(path, base=None):
    return urljoin(base or SettingManager.get("l2_patients_url", default='http://localhost/if', default_type='s'), path)


def get_headers(token=None):
    return {"Authorization": "Bearer {}".format(token or SettingManager.get("l2_patients_token", default='token', default_type='s'))}


def make_request(path, json_data=None, base=None, token=None):
    if json_data is None:
        json_data = {}
    text_resp = None
    try:
        url = get_url(path, base=base)
        headers = get_headers(token=token)
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


def update_doc_call_status(external_num, status, oid, code_tfoms) -> dict:
    data = make_request("doc-call-update-status", {"externalNum": external_num, "status": status, "org": {"oid": oid, "codeTFOMS": code_tfoms}})
    return data


def send_doc_call(base, token, data) -> dict:
    data = make_request("doc-call-send", data, base=base, token=token)
    return data
