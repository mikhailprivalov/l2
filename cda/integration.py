import json
import logging
from urllib.parse import urljoin, urlencode

import requests

from appconf.manager import SettingManager

logger = logging.getLogger(__name__)


def get_url(path, query=None):
    if query is None:
        query = {}
    base = SettingManager.get_cda_base_url()
    if not base or base == 'empty':
        return {}
    return urljoin(base, path) + ('?{}'.format(urlencode(query)) if query else '')


def make_request(path, query=None, as_json=True, **kwargs):
    if query is None:
        query = {}
    try:
        url = get_url(path, query=query)
        headers = {"Content-Type": "application/json", "Authorization": "Bearer a-super-secret-key"}
        data = requests.post(url, headers=headers, **kwargs)
        if as_json:
            return data.json()
        return data.text
    except Exception as e:
        print(e)  # noqa: T001
        return {}


def get_required_signatures(service: str) -> dict:
    return make_request('/required-signatures', {"title": str(service)})


def render_cda(service: str, direction_data: dict) -> dict:
    return make_request('/render/njk.xml', as_json=False, data=json.dumps({"title": str(service), **direction_data}))


def cdator_gen_xml(eds_generator: str, direction_data: dict) -> dict:
    print(eds_generator)
    print(direction_data)
    return make_request('/generate', data=json.dumps({"generatorName": eds_generator, "data": direction_data}))
