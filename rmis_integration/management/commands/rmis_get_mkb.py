from django.core.management import BaseCommand
from rmis_integration.client import Client as RC
from directions.models import Diagnoses


class Command(BaseCommand):
    help = "Получение справочника МКБ"

    def handle(self, *args, **options):
        c = RC()

        request_data = {
            "refbookCode": "1.2.643.5.1.13.3.1058506043530.1.1.5",
            "version": "CURRENT",
        }
        count_parts = c.get_client("path_directory").service.getRefbookParts(**request_data)
        for i in range(count_parts):
            request_data['partNumber'] = i + 1
            mkb_part = c.get_client("path_directory").service.getRefbookPartial(**request_data)
            for m in mkb_part:
                data = m['column']
                code, name, rmis_id = '', '', ''
                m_type = 1
                for j in data:
                    print(j)
                    if j['name'] == 'CODE':
                        code = j['data']
                    if j['name'] == 'NAME':
                        name = j['data']
                    if j['name'] == 'ID':
                        rmis_id = j['data']
                    if j['name'] == 'HAS_CHILD':
                        if j['data'] == 'true':
                            m_type = 1
                        else:
                            m_type = 2

                if "-" in code:
                    continue
                diag = Diagnoses.objects.filter(code=code).first()
                if diag:
                    if diag.title != name:
                        diag.title = name
                    if rmis_id and diag.rmis_id != rmis_id:
                        diag.rmis_id = rmis_id
                    diag.m_type = m_type
                    diag.save()
                    print(f"обновлено: {code}-{name}-{m_type}")
                if diag is None:
                    Diagnoses(code=code, title=name, m_type=m_type, d_type='mkb10.4', rmis_id=rmis_id).save()
                    print(f"создано: {code}-{name}-{m_type}")
