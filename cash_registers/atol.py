import requests

from laboratory.settings import CASH_REGISTER_SERVER_ADDRESS


def send_request(json_data: dict):
    response = requests.post(CASH_REGISTER_SERVER_ADDRESS, json=json_data)
    response_data = response.json()
    return response_data



