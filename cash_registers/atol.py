import requests

from laboratory.settings import CASH_REGISTER_SERVER_ADDRESS


def send_request():
    request = requests.post(CASH_REGISTER_SERVER_ADDRESS)
