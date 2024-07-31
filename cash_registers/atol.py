import requests
from laboratory.settings import CASH_REGISTER_SERVER_ADDRESS, CASH_REGISTER_SERVER_TOKEN


def send_request(body: dict):
    headers = {"Authorization": f"bearer {CASH_REGISTER_SERVER_TOKEN}"}
    try:
        response = requests.post(f"{CASH_REGISTER_SERVER_ADDRESS}/push-job", json=body, headers=headers)
        response_data = response.json()
    except Exception as e:
        return {"ok": False, "message": "Ошибка", "data": f"{e}"}
    return response_data


def open_shift(uuid: str, cash_register: dict, operator: dict):
    body = {
        "cashRegister": cash_register,
        "job": {
            "uuid": uuid,
            "request": [
                {
                    "type": "openShift",
                    "operator": operator
                }
            ]
        }
    }
    return send_request(body)


def close_shift(uuid: str, cash_register: dict, operator: dict):
    body = {
        "cashRegister": cash_register,
        "job": {
            "uuid": uuid,
            "request": [
                {
                    "type": "closeShift",
                    "operator": operator
                }
            ]
        }
    }
    return send_request(body)
