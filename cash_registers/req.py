import requests
from laboratory.settings import CASH_REGISTER_SERVER_ADDRESS, CASH_REGISTER_SERVER_TOKEN


def get_authorization_header():
    headers = {"Authorization": f"Bearer {CASH_REGISTER_SERVER_TOKEN}"}
    return headers


def check_cash_server():
    headers = get_authorization_header()
    try:
        response = requests.post(CASH_REGISTER_SERVER_ADDRESS, headers=headers, timeout=3)
        response_data = response.json()
    except Exception as e:
        return {"ok": False, "message": "Ошибка", "data": f"{e}", "connection_error": True}
    return response_data


def check_cash_register(cash_register_data: dict):
    headers = get_authorization_header()
    body = {"cashRegister": cash_register_data}
    try:
        response = requests.post(f"{CASH_REGISTER_SERVER_ADDRESS}get-cash-register-status", json=body, headers=headers, timeout=3)
        response_data = response.json()
    except Exception as e:
        return {"ok": False, "message": "Ошибка", "data": f"{e}", "connection_error": True}
    return response_data


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
    return send_job(body)


def close_shift(uuid: str, cash_register: dict, operator: dict):
    body = {"cashRegister": cash_register, "uuid": uuid, "job": [{"type": "closeShift", "operator": operator}]}
    return send_job(body)
