import logging
from typing import List, Optional
from urllib.parse import urljoin, urlencode

import requests

from appconf.manager import SettingManager
from tfoms.l2 import check_l2_enp, check_l2_patient

logger = logging.getLogger(__name__)


def get_url(path, query=None):
    if query is None:
        query = {}
    return urljoin(SettingManager.get("tfoms_api_url", default='http://localhost/', default_type='s'), path) + ('?{}'.format(urlencode(query)) if query else '')


def get_headers():
    return {"Authorization": "Bearer {}".format(SettingManager.get("tfoms_api_token", default='token', default_type='s'))}


def make_request(path, query=None, **kwargs):
    if query is None:
        query = {}
    try:
        url = get_url(path, query=query)
        headers = get_headers()
        data = requests.post(url, headers=headers, **kwargs).json()
        return data
    except Exception as e:
        print(e)  # noqa: T001
        return {}


def match_patient(family, name, patronymic, birthday) -> List[dict]:
    logger.exception(f"match_patient: {(family, name, patronymic, birthday)}")
    if SettingManager.get("l2_patients_is_active", default='f', default_type='b'):
        logger.exception("l2_patients_is_active")
        resp = check_l2_patient(family, name, patronymic, birthday)
        logger.exception(f"resp: {resp}")
        if not isinstance(resp, dict) or not resp.get('ok') or not resp.get('list'):
            return []
        return resp.get('list')
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
    data = make_request("match-patient-by-enp-set2", {"enp": enp}, timeout=5)
    if isinstance(data, list) and len(data) > 0:
        return data[0]
    return data


def get_attachment_by_idt(idt) -> Optional[dict]:
    logger.exception(f"tfms: get_attachment_by_idt: {idt}")
    data = make_request("get-attachment-info-by-idt", {"idt": idt}, timeout=5)
    if isinstance(data, list) and len(data) > 0:
        return data[0]
    return data


def get_ud_info_by_enp(enp) -> Optional[dict]:
    logger.exception(f"tfms: get_ud_info_by_enp: {enp}")
    data = make_request("get-ud-info-by-enp", {"enp": enp}, timeout=5)
    return data


def get_dn_info_by_enp(enp) -> Optional[dict]:
    logger.exception(f"tfms: get_dn_info_by_enp: {enp}")
    data = make_request("get-dn-info-by-enp", {"enp": enp}, timeout=5)
    return data


def match_patient_by_snils(snils) -> Optional[dict]:
    logger.exception(f"tfms: get_patient_by_snils: {snils}")
    data = make_request("match-patient-by-snils", {"snils": snils}, timeout=5)
    return data
