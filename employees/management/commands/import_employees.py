from django.core.management.base import BaseCommand
from api.parse_file.forms103 import form_01


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - путь до файла с работниками
        :param organization_id = id организации в бд (hospital_id)
        """
        parser.add_argument('path', type=str)
        parser.add_argument('organization_id', type=int)

    def handle(self, *args, **kwargs):
        file_path = kwargs["path"]
        organization_id = kwargs["organization_id"]
        result_upload = form_01(request_data={"file": file_path, "entity_id": organization_id})
        if result_upload["ok"]:
            self.stdout.write("Успешная загрузка сотрудников")
        else:
            self.stdout.write("Ошибка загрузки сотрудников")


