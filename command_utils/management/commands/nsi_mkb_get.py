from concurrent.futures import ThreadPoolExecutor

from django.core.management import BaseCommand
from appconf.manager import SettingManager
from directions.models import Diagnoses
import requests
from requests import Session
from zeep import Client
from zeep.transports import Transport
from django.db import transaction


NSI_MKB10_DIRECTORIES = {
    "mkb10.4": {
        "oid": "1.2.643.5.1.13.13.11.1005",
        "title": "Международная статистическая классификация болезней и проблем, связанных со здоровьем (10-й пересмотр)",
    },
    "mkb10.5": {
        "oid": "1.2.643.5.1.13.13.11.1489",
        "title": "Алфавитный указатель к Международной статистической классификации болезней и проблем, связанных со здоровьем (10-й пересмотр, том 3)",
    },
    "mkb10.6": {
        "oid": "1.2.643.5.1.13.13.99.2.692",
        "title": "Алфавитный указатель к Международной статистической классификации болезней и проблем, связанных со здоровьем (10-й пересмотр, том 3, "
        "внешние причины заболеваемости и смертности)",
    },
}


def fetch(url):
    page = requests.get(url)
    return page.json()['list']


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
        for diag_key in NSI_MKB10_DIRECTORIES:
            k = NSI_MKB10_DIRECTORIES[diag_key]['oid']
            v = NSI_MKB10_DIRECTORIES[diag_key]['title']
            if fp and fp != diag_key:
                print('Пропуск справочника', diag_key)  # noqa: T001
                print(v)  # noqa: T001
                continue
            with transaction.atomic():
                print('Получение справочника', diag_key)  # noqa: T001
                print(v)  # noqa: T001
                is_empty = not Diagnoses.objects.filter(d_type=diag_key).exists()
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

                bulk_create = []
                pool = ThreadPoolExecutor(max_workers=20)
                urls = [f'https://nsi.rosminzdrav.ru:443/port/rest/data?userKey={nsi_key}&identifier={k}&page={i}&size=500' for i in range(1, data_parts)]
                i = -1
                for diagnoses in pool.map(fetch, urls):
                    i += 1
                    n = 0
                    for data in diagnoses:
                        n += 1
                        nsi_code, title, mkb_code = "", "", ""
                        for p in data:
                            if p['column'] == 'ID':
                                nsi_code = p['value']
                            if p['column'] == 'S_NAME' and not title:
                                title = p['value']
                            if p['column'] == 'MKB_NAME' and not title:
                                title = p['value']
                            if p['column'] == 'ICD-10' and not mkb_code:
                                mkb_code = p['value']
                            if p['column'] == 'MKB_CODE' and not mkb_code:
                                mkb_code = p['value']
                        n_str = f"({i + 1}/{data_parts}) ({n}/{len(diagnoses)}): {diag_key}-{mkb_code}-{title}-{nsi_code}"

                        if is_empty:
                            bulk_create.append(Diagnoses(code=mkb_code, d_type=diag_key, title=title, nsi_id=nsi_code, hide=False, m_type=2))
                            print(f"добавлено в очередь создания {n_str}")  # noqa: T001
                        else:
                            _, created = Diagnoses.objects.update_or_create(code=mkb_code, d_type=diag_key, title=title, defaults={'nsi_id': nsi_code, 'hide': False, 'm_type': 2})
                            if not created:
                                print(f"обновлено {n_str}")  # noqa: T001
                            else:
                                print(f"создано {n_str}")  # noqa: T001
                    if len(bulk_create) >= 19500:
                        print(f"пакетное создание записей {len(bulk_create)} шт")  # noqa: T001
                        Diagnoses.objects.bulk_create(bulk_create, 8000)
                        bulk_create = []

                if bulk_create:
                    print(f"пакетное создание записей {len(bulk_create)} шт")  # noqa: T001
                    Diagnoses.objects.bulk_create(bulk_create)
            print(f'Скрытых значений {diag_key}:', Diagnoses.objects.filter(d_type=diag_key, hide=True).count())  # noqa: T001
