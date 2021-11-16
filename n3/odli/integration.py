import logging
from typing import Union
import uuid
from urllib.parse import urljoin, urlencode
from django.utils import timezone

import requests

from laboratory.settings import N3_ODLI_BASE_URL, N3_ODLI_SYSTEM_ID, N3_ODLI_TOKEN, RMIS_PROXY, DEFAULT_N3_DOCTOR

logger = logging.getLogger(__name__)


def get_url(path, query=None):
    if query is None:
        query = {}
    return urljoin(N3_ODLI_BASE_URL, path) + ('?{}'.format(urlencode(query)) if query else '')


def make_request(path, query=None, as_json=True, **kwargs):
    if query is None:
        query = {}
    try:
        url = get_url(path, query=query)
        headers = {"Content-Type": "application/json", "Authorization": f"N3 {N3_ODLI_TOKEN}"}
        data = requests.post(url, headers=headers, **kwargs, proxies=RMIS_PROXY, timeout=7)
        if as_json:
            return data.json()
        return data.text
    except Exception as e:
        print(e)  # noqa: T001
        return {}

