import requests
from laboratory.settings import CASH_REGISTER_SERVER_ADDRESS, CASH_REGISTER_SERVER_TOKEN


def get_authorization_header():
    headers = {"Authorization": f"Bearer {CASH_REGISTER_SERVER_TOKEN}"}
    return headers


def check_cash_register_status(cash_register_data: dict) -> dict:
    headers = get_authorization_header()
    body = {"cashRegister": cash_register_data}
    try:
        response = requests.post(f"{CASH_REGISTER_SERVER_ADDRESS}get-cash-register-status", json=body, headers=headers)
        response_data = response.json()
    except Exception as e:
        return {
            "ok": False,
            "connection_middle_server_error": True,
            "data": f"{e}",
        }
    return response_data


def check_cash_register(cash_register_data: dict):
    cash_register_check = check_cash_register_status(cash_register_data)
    message = ""
    if not cash_register_check["ok"]:
        if cash_register_check.get("connection_middle_server_error"):
            message = "Кассовый middle сервер недоступен"
        elif cash_register_check.get("connection_web_request_error"):
            message = "Кассовый web-request atol сервер недоступен"
        elif cash_register_check.get("cash_register_connection_error"):
            # todo - логировать ошибку из ключа "data"
            message = "Ошибка при подключении к кассе"
        return {"ok": False, "message": message}
    else:
        # todo - проверять состояние кассы (бумага, очередь заданий, фискальник)
        device_status = cash_register_check["data"]["deviceStatus"]
        if not device_status["paperPresent"]:
            return {"ok": False, "message": "В кассе нет бумаги"}
        if device_status["blocked"]:
            return {"ok": False, "message": "Касса заблокирована"}
        return {"ok": True}


def send_job(body: dict):
    headers = get_authorization_header()
    try:
        response = requests.post(f"{CASH_REGISTER_SERVER_ADDRESS}push-job", json=body, headers=headers, timeout=5)
        response_data = response.json()
    except Exception as e:
        return {"ok": False, "message": "Ошибка", "data": f"{e}", "connection_error": True}
    return response_data


def get_job_status(uuid: str, cash_register: dict):
    body = {"cashRegister": cash_register, "uuid": uuid}
    headers = get_authorization_header()
    try:
        response = requests.post(f"{CASH_REGISTER_SERVER_ADDRESS}get-job-status", json=body, headers=headers, timeout=5)
        response_data = response.json()
    except Exception as e:
        return {"ok": False, "message": "Ошибка", "data": f"{e}", "connection_error": True}
    return response_data


def open_shift(uuid: str, cash_register: dict, operator: dict):
    body = {"cashRegister": cash_register, "uuid": uuid, "job": [{"type": "openShift", "operator": operator}]}
    result = send_job(body)
    return result


def close_shift(uuid: str, cash_register: dict, operator: dict):
    body = {"cashRegister": cash_register, "uuid": uuid, "job": [{"type": "closeShift", "operator": operator}]}
    result = send_job(body)
    return result
