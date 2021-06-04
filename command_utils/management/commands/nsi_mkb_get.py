from django.core.management import BaseCommand
from appconf.manager import SettingManager
from directions.models import Diagnoses
import requests
from requests import Session
from zeep import Client
from zeep.transports import Transport


class Command(BaseCommand):
    help = "Получение справочника МКБ"

    def handle(self, *args, **options):
        nsi_key = SettingManager.get("nsi_key", default='', default_type='s')
        mkb10_directories = {
            "1.2.643.5.1.13.13.11.1489": "Алфавитный указатель к Международной статистической классификации болезней и проблем, связанных со здоровьем (10-й пересмотр, том 3)",
            "1.2.643.5.1.13.13.99.2.692": "Алфавитный указатель к Международной статистической классификации болезней и проблем, связанных со здоровьем (10-й пересмотр, том 3, внешние причины заболеваемости и смертности)",
        }
        session = Session()
        transport = Transport(session=session)
        client = Client('https://nsi.rosminzdrav.ru/wsdl/SOAP-server.v2.php?wsdl', transport=transport)
        version_data, mkb_code, data_parts, nsi_code, title = '', '', '', '', ''
        for k, v in mkb10_directories.items():
            data = client.service.getVersionList(userKey5=nsi_key, refbookCode4=k)
            version_data = data['item'][-1]['children']['item']
            for i in version_data:
                if i['key'] == 'S_VERSION':
                    version_data = i['value']

            data = client.service.getRefbookParts(userKey3=nsi_key, refbookCode2=k, version2=version_data)
            for i in data['item']:
                if i['key'] == "partsAmount":
                    data_parts = int(i['value']) + 1
            for i in range(1, data_parts):
                diag = None
                response = requests.get(f'https://nsi.rosminzdrav.ru:443/port/rest/data?userKey={nsi_key}&identifier={k}&page={i}&size=500')
                for data in response.json()['list']:
                    print(data)
                    nsi_code, title, mkb_code = "", "", ""
                    for p in data:
                        if p['column'] == 'ID':
                            nsi_code = p['value']
                        if p['column'] == 'S_NAME':
                            title = p['value']
                        if p['column'] == 'ICD-10':
                            mkb_code = p['value']
                    diag = Diagnoses.objects.filter(code=mkb_code).first()
                    if diag:
                        if diag.title != title:
                            diag.title = title
                        diag.nsi_id = nsi_code
                        diag.save()
                        print(f"обновлено: {mkb_code}-{title}-{nsi_code}")  # noqa: T001
                if diag is None:
                    Diagnoses(code=mkb_code, title=title, m_type=2, d_type='mkb10.4', nsi_id=nsi_code).save()
                    print(f"создано: {mkb_code}-{title}-{nsi_code}")  # noqa: T001
