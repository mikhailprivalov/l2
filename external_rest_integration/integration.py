import logging
import requests
import simplejson as json
from hospitals.models import Hospitals
from django.core.cache import cache


logger = logging.getLogger(__name__)


def get_url_auth_data(hospital_id):
    auth_data = Hospitals.objects.values_list("auth_data_for_rest", flat=True).filter(id=hospital_id)
    data = None
    if auth_data:
        data = json.loads(auth_data[0])
    return data


def make_request_get_token(hosp_data, method="GET", get_new_token=False):
    try:
        k = f"{hosp_data.get('hospital_id')}_hosp_key_auth"
        cv = cache.get(k)
        if cv and not get_new_token:
            return json.loads(cv)
        else:
            headers = {"login": hosp_data.get("login"), "password": hosp_data.get("password")}
            auth = (hosp_data.get("auth_login"), hosp_data.get("auth_password"))
            url = f"{hosp_data.get('url')}/ky"
            response = requests.request(method, url, headers=headers, auth=auth)
            data = response.json()
            cache.set(k, json.dumps(data.get("key")), 60 * 60 * 96)
            return data.get("key")
    except Exception as e:
        logger.exception(e)
        return {}


def rest_make_request_get(default_part_url, path, token, auth_data, data, method="GET"):
    if data is None:
        data = {}
    try:
        url = f"{default_part_url}/{path}"
        headers = {"x-auth-token": token, "Content-Type": "application/json"}
        auth = (auth_data.get("auth_login"), auth_data.get("auth_password"))
        data = requests.request(method, url, auth=auth, headers=headers, data=(json.dumps(data, ensure_ascii=False)).encode('utf-8'))
        return json.loads(data.content.decode())
    except Exception as e:
        logger.exception(e)
        return {}
