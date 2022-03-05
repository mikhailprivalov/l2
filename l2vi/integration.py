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


def make_request(path, query=None, as_json=True, **kwargs):
    if query is None:
        query = {}
    try:
        url = get_url(path, query=query)
        headers = {"Content-Type": "application/json"}
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

