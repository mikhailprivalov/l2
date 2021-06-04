import os
from django.core.management import BaseCommand

import utils.permanent_directories2
from appconf.manager import SettingManager
import pickle
import requests
from requests import Session
from zeep import Client
from zeep.transports import Transport
from laboratory.settings import BASE_DIR
import simplejson as json


class Command(BaseCommand):
    help = "Справочники НСИ"

    def handle(self, *args, **options):
        nsi_key = SettingManager.get("nsi_key", default='', default_type='s')
        nsi_directories = {
            "1.2.643.5.1.13.13.99.2.19": "Вид медицинского свидетельства о смерти",
            "1.2.643.5.1.13.13.11.1042": "Вид места жительства",
            "1.2.643.5.1.13.13.99.2.20": "Типы мест наступления смерти",
            "1.2.643.5.1.13.13.99.2.18": "Доношенность новорожденного",
            "1.2.643.5.1.13.13.99.2.15": "Семейное положение",
            "1.2.643.5.1.13.13.99.2.16": "Классификатор образования для медицинских свидетельств",
            "1.2.643.5.1.13.13.11.1038": "Социальные группы населения в учетной медицинской документации",
            "1.2.643.5.1.13.13.99.2.21": "Род причины смерти",
            "1.2.643.5.1.13.13.99.2.22": "Тип медицинского работника, установившего причины смерти",
            "1.2.643.5.1.13.13.99.2.23": "Основания для определения причины смерти",
            "1.2.643.5.1.13.13.99.2.24": "Связь смерти с ДТП",
            "1.2.643.5.1.13.13.99.2.25": "Связь смерти с беременностью",
        }

        result = {}
        session = Session()
        transport = Transport(session=session)
        client = Client('https://nsi.rosminzdrav.ru/wsdl/SOAP-server.v2.php?wsdl', transport=transport)
        version_data, mkb_code, data_parts, nsi_code, title = '', '', '', '', ''
        for k, v in nsi_directories.items():
            data = client.service.getVersionList(userKey5=nsi_key, refbookCode4=k)
            version_data = data['item'][-1]['children']['item']
            for i in version_data:
                if i['key'] == 'S_VERSION':
                    version_data = i['value']

            data = client.service.getRefbookParts(userKey3=nsi_key, refbookCode2=k, version2=version_data)
            for i in data['item']:
                if i['key'] == "partsAmount":
                    data_parts = int(i['value']) + 1
            temp_data = {}
            for i in range(1, data_parts):
                response = requests.get(
                    f'https://nsi.rosminzdrav.ru:443/port/rest/data?userKey={nsi_key}&identifier={k}&page={i}&size=500')
                for data in response.json()['list']:
                    code, title = "", ""
                    for p in data:
                        if p['column'] == 'ID':
                            code = int(p['value'])
                        if p['column'] == 'NAME':
                            title = p['value'].replace('\xa0', ' ')
                        if p['column'] == 'Name':
                            title = p['value'].replace('\xa0', ' ')
                    temp_data[code] = title
            result[v] = [f"{key} - {temp_data[key]}" for key in sorted(temp_data.keys())]

        directories_file = os.path.join(BASE_DIR, 'utils', 'permanent_directories.json')
        with open(directories_file, 'w') as f:
            json.dump(result, f)
