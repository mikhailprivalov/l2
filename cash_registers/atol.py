import requests
from laboratory.settings import CASH_REGISTER_SERVER_ADDRESS, CASH_REGISTER_SERVER_TOKEN


def send_request(json_data: dict):
    headers = {"Authorization": f"bearer {CASH_REGISTER_SERVER_TOKEN}"}
    response = requests.post(CASH_REGISTER_SERVER_ADDRESS, json=json_data, headers=headers)
    response_data = response.json()
    return response_data
