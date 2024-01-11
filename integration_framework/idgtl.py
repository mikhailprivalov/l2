from typing import List

import requests
from urllib.parse import urljoin

from laboratory.settings import IDGTL_KEY


class IDGTLApi:
    def __init__(self):
        self.url = 'https://direct.i-dgtl.ru/api/'
        self.headers = {'Authorization': f'Basic {IDGTL_KEY}', 'Content-Type': 'application/json'}

    @staticmethod
    def fix_phone(phone: str):
        phone = phone.replace('+', '')
        if len(phone) == 10:
            phone = '7' + phone
        elif len(phone) == 11:
            phone = '7' + phone[1:]
        elif len(phone) == 12:
            phone = '7' + phone[2:]
        return phone

    def join_url(self, path):
        return urljoin(self.url, path)

    def post(self, path, data=None):
        return requests.post(self.join_url(path), json=data, headers=self.headers)

    def send_code_cascade(self, phone: str, code: str):
        return self.post(
            'v1/message/cascade',
            data=[
                {
                    "destination": IDGTLApi.fix_phone(phone),
                    "cascade": [
                        {
                            "channelType": "VOICECODE",
                            "senderName": "voicecode",
                            "content": {
                                "contentType": "text",
                                "text": f"Код авторизации от организации: {code}",
                            },
                            "ttl": 100 * 60,
                        },
                        {
                            "channelType": "SMS",
                            "senderName": "sms_promo",
                            "content": {
                                "text": f"Код доступа: {code}",
                            },
                        },
                    ],
                }
            ],
        )

    def stop(self, ids: List[str]):
        return self.post(
            'v1/message/stop',
            data={
                "uuids": ids,
            },
        )
