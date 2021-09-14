from django.core.management import BaseCommand
from appconf.manager import SettingManager
from directions.models import Diagnoses
import requests
from requests import Session
from zeep import Client
from zeep.transports import Transport
from django.db import transaction


NSI_MKB10_DIRECTORIES = {
    "1.2.643.5.1.13.13.11.1489": "Алфавитный указатель к Международной статистической классификации болезней и проблем, связанных со здоровьем (10-й пересмотр, том 3)",
    "1.2.643.5.1.13.13.99.2.692": "Алфавитный указатель к Международной статистической классификации болезней и проблем, связанных со здоровьем (10-й пересмотр, том 3, "
                                  "внешние причины заболеваемости и смертности)",
}


class Command(BaseCommand):
    help = "Получение справочника МКБ"

    def add_arguments(self, parser):
        parser.add_argument('mode', nargs='?', type=str, default=None)

    def handle(self, *args, **kwargs):
        fp = kwargs.get("mode")
        nsi_key = SettingManager.get("nsi_key", default='', default_type='s')
        session = Session()
        transport = Transport(session=session)
        client = Client('https://nsi.rosminzdrav.ru/wsdl/SOAP-server.v2.php?wsdl', transport=transport)
        version_data, mkb_code, nsi_code, title = '', '', '', ''
        data_parts = 0
        for k, v in NSI_MKB10_DIRECTORIES.items():
            with transaction.atomic():
                diag_key = 'mkb10-death' if k == '1.2.643.5.1.13.13.99.2.692' else 'mkb10.4'
                if fp and fp != diag_key:
                    print('Пропуск справочника', diag_key)  # noqa: T001
                    print(v)  # noqa: T001
                    continue
                print('Получение справочника', diag_key)  # noqa: T001
                print(v)  # noqa: T001
                Diagnoses.objects.filter(d_type=diag_key).update(hide=True)
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
                    diagnoses = response.json()['list']
                    n = 0
                    for data in diagnoses:
                        n += 1
                        nsi_code, title, mkb_code = "", "", ""
                        for p in data:
                            if p['column'] == 'ID':
                                nsi_code = p['value']
                            if p['column'] == 'S_NAME':
                                title = p['value']
                            if p['column'] == 'ICD-10':
                                mkb_code = p['value']
                        diag = Diagnoses.objects.filter(code=mkb_code, d_type=diag_key, title=title).first()
                        n_str = f"({i + 1}/{data_parts}) ({n}/{len(diagnoses)}): {diag_key}-{mkb_code}-{title}-{nsi_code}"
                        if diag:
                            updates = ['hide']
                            diag.hide = False
                            if diag.nsi_id != nsi_code:
                                diag.nsi_id = nsi_code
                                updates.append('nsi_id')
                            diag.save(update_fields=updates)
                            if updates:
                                print(f"обновлено {n_str}")  # noqa: T001
                            else:
                                print(f"корректно {n_str}")  # noqa: T001
                        else:
                            Diagnoses(code=mkb_code, title=title, m_type=2, d_type=diag_key, nsi_id=nsi_code).save()
                            print(f"создано {n_str}")  # noqa: T001
            print(f'Скрытых значений {diag_key}:', Diagnoses.objects.filter(d_type=diag_key, hide=True).count())  # noqa: T001
