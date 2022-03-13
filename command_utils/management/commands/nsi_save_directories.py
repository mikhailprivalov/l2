import os
from django.core.management import BaseCommand
from appconf.manager import SettingManager
import requests
from requests import Session
from zeep import Client
from zeep.transports import Transport
from laboratory.settings import BASE_DIR
from utils.nsi_directories import NSI


NSI_DIRECTORIES_TO_SAVE = {
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


class Command(BaseCommand):
    help = "Справочники НСИ"

    def handle(self, *args, **options):
        nsi_key = SettingManager.get("nsi_key", default='', default_type='s')

        session = Session()
        transport = Transport(session=session)
        client = Client('https://nsi.rosminzdrav.ru/wsdl/SOAP-server.v2.php?wsdl', transport=transport)
        directories_project_file_path = os.path.join('utils', 'nsi_directories.py')
        directories_file_path = os.path.join(BASE_DIR, directories_project_file_path)
        STATIC_DIRECTORIES = {x: NSI[x] for x in NSI if x not in NSI_DIRECTORIES_TO_SAVE}
        with open(directories_file_path, 'w') as f:
            f.write("NSI = {\n")
            for oid in NSI_DIRECTORIES_TO_SAVE:
                print('Получение данных', oid)  # noqa: T001
                version_data = client.service.getVersionList(userKey5=nsi_key, refbookCode4=oid)
                version_data = version_data['item'][-1]['children']['item']
                version = None
                for i in version_data:
                    if i['key'] == 'S_VERSION':
                        version = i['value']
                        break
                if not version:
                    print('Не найдена версия для справочника')  # noqa: T001
                    continue

                directory_parts = client.service.getRefbookParts(userKey3=nsi_key, refbookCode2=oid, version2=version)
                data_parts = None
                for i in directory_parts['item']:
                    if i['key'] == "partsAmount":
                        data_parts = int(i['value']) + 1
                if not version:
                    print('Не найдено количество частей для справочника')  # noqa: T001
                    continue

                f.write(f"    '{oid}': {{\n")
                f.write(f"        'title': '{NSI_DIRECTORIES_TO_SAVE[oid]}',\n")
                f.write("        'values': {\n")
                for i in range(1, data_parts):
                    response = requests.get(f'https://nsi.rosminzdrav.ru:443/port/rest/data?userKey={nsi_key}&identifier={oid}&page={i}&size=500')
                    for data in response.json()['list']:
                        code, title = None, None
                        for p in data:
                            if p['column'] == 'ID':
                                code = p['value']
                            if str(p['column']).lower() == 'name':
                                title = p['value'].replace('\xa0', ' ')
                        if code and title:
                            f.write(f"            '{code}': '{title}',\n")
                f.write("        },\n")
                f.write("    },\n")
            for oid in STATIC_DIRECTORIES:
                f.write(f"    '{oid}': {{\n")
                f.write(f"        'title': '{STATIC_DIRECTORIES[oid]['title']}',\n")
                f.write("        'values': {\n")
                for code in STATIC_DIRECTORIES[oid]['values']:
                    f.write(f"            '{code}': '{STATIC_DIRECTORIES[oid]['values'][code]}',\n")
                f.write("        },\n")
                f.write("    },\n")
            f.write("}\n")
        print('Сохранено в:', directories_project_file_path)  # noqa: T001
