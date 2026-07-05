import logging
import sys
import requests
import simplejson as json
from hospitals.models import Hospitals
from django.core.cache import cache


logger = logging.getLogger(__name__)


def is_interactive_console():
    return sys.stdout.isatty()


def interactive_log(message):
    if is_interactive_console():
        sys.stdout.write(f"{message}\n")
        sys.stdout.flush()


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
            interactive_log(f"[REST] Токен из кэша, hospital_id={hosp_data.get('hospital_id')}")
            return json.loads(cv)
        url = f"{hosp_data.get('url')}/ky"
        interactive_log(f"[REST] Запрос ключа: {method} {url}")
        interactive_log(
            f"[REST] login={hosp_data.get('login')}, password={hosp_data.get('password')}, " f"auth_login={hosp_data.get('auth_login')}, auth_password={hosp_data.get('auth_password')}"
        )
        headers = {"login": hosp_data.get("login"), "password": hosp_data.get("password")}
        auth = (hosp_data.get("auth_login"), hosp_data.get("auth_password"))
        response = requests.request(method, url, headers=headers, auth=auth)
        data = response.json()
        cache.set(k, json.dumps(data.get("key")), 60 * 60 * 96)
        interactive_log(f"[REST] Ключ получен: {'да' if data.get('key') else 'нет'}")
        return data.get("key")
    except Exception as e:
        interactive_log(f"[REST] Ошибка получения ключа: {e}")
        logger.exception(e)
        return {}


def _short_repr(value, limit=500):
    text = str(value)
    if len(text) > limit:
        return f"{text[:limit]}..."
    return text


def rest_make_request_get(default_part_url, path, token, auth_data, data, method="GET"):
    if data is None:
        data = {}
    try:
        url = f"{default_part_url}/{path}"
        interactive_log(f"[REST] {method} {url}")
        headers = {"x-auth-token": token, "Content-Type": "application/json"}
        auth = (auth_data.get("auth_login"), auth_data.get("auth_password"))
        response = requests.request(method, url, auth=auth, headers=headers, data=(json.dumps(data, ensure_ascii=False)).encode('utf-8'))
        result = json.loads(response.content.decode())
        if path == "result":
            interactive_log(f"[REST] Ответ {path} (полный): {json.dumps(result, ensure_ascii=False)}")
        else:
            interactive_log(f"[REST] Ответ {path}: {_short_repr(result)}")
        return result
    except Exception as e:
        interactive_log(f"[REST] Ошибка запроса {path}: {e}")
        logger.exception(e)
        return {}


def rest_make_request_get_result(default_part_url, token, auth_data, order_number, only_new=False):
    path = "result"
    rest_api_data = {
        "number": order_number,
        "format": "pdf",
        "combine": False,
        "article": "",
        "new": only_new,
    }
    return rest_make_request_get(default_part_url, path, token, auth_data, rest_api_data, method="POST")
