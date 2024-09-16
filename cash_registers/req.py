import requests
from laboratory.settings import CASH_REGISTER_SERVER_ADDRESS, CASH_REGISTER_SERVER_TOKEN


def get_authorization_header():
    headers = {"Authorization": f"Bearer {CASH_REGISTER_SERVER_TOKEN}"}
    return headers


def check_cash_register_status(cash_register_data: dict) -> dict:
    headers = get_authorization_header()
    body = {"cashRegister": cash_register_data}
    try:
        response = requests.post(f"{CASH_REGISTER_SERVER_ADDRESS}/get-cash-register-status", json=body, headers=headers, timeout=30)
        response_data = response.json()
    except Exception as e:
        return {
            "ok": False,
            "connection_middle_server_error": True,
            "data": f"{e}",
        }
    return response_data


def check_cash_register(cash_register_data: dict):
    result = {"ok": True, "message": ""}
    cash_register_check = check_cash_register_status(cash_register_data)
    if cash_register_check["ok"]:
        device_status = cash_register_check["data"]["deviceStatus"]
        if not device_status["paperPresent"]:
            result = {"ok": False, "message": "В кассе нет бумаги"}
        elif device_status["blocked"]:
            result = {"ok": False, "message": "Касса заблокирована"}
    else:
        if cash_register_check.get("connection_middle_server_error"):
            result = {"ok": False, "message": "Кассовый middle сервер недоступен"}
        elif cash_register_check.get("connectionWebRequestError"):
            result = {"ok": False, "message": "Кассовый web-request atol сервер недоступен"}
        elif cash_register_check.get("cashRegisterConnectionError"):
            # todo - логировать ошибку из ключа "data"
            result = {"ok": False, "message": "Ошибка при подключении к кассе"}
    return result


def send_job(body: dict):
    headers = get_authorization_header()
    try:
        response = requests.post(f"{CASH_REGISTER_SERVER_ADDRESS}/push-job", json=body, headers=headers, timeout=5)
        response_data = response.json()
    except Exception as e:
        return {"ok": False, "message": "Ошибка", "data": f"{e}", "connection_middle_server_error": True}
    return response_data


def get_job_status(uuid: str, cash_register: dict):
    body = {"cashRegister": cash_register, "uuid": uuid}
    headers = get_authorization_header()
    try:
        response = requests.post(f"{CASH_REGISTER_SERVER_ADDRESS}/get-job-status", json=body, headers=headers, timeout=5)
        response_data = response.json()
    except Exception as e:
        return {"ok": False, "message": "Ошибка", "data": f"{e}", "connection_middle_server_error": True}
    return response_data
