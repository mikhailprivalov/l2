from django.core.management.base import BaseCommand
from openpyxl.workbook import Workbook

from api.parse_file.forms103 import form_01 as parse_employee
from appconf.manager import SettingManager


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
        result_upload = parse_employee(request_data={"file": file_path, "entity_id": organization_id})
        if result_upload["ok"]:
            result_wb = Workbook()
            result_ws = result_wb[result_wb.sheetnames[0]]
            col_data = [column["title"] for column in result_upload["result"]["colData"]]
            result_ws.append(col_data)
            for row in result_upload["result"]["data"]:
                result_ws.append([row["fio"], row["reason"]])
            dir_tmp = SettingManager.get("dir_param")
            result_wb.save(f"{dir_tmp}/result_import_employees.xlsx")
            self.stdout.write(f"Успешная загрузка сотрудников, результаты доступны в {dir_tmp}")
        else:
            self.stdout.write(f"Ошибка загрузки сотрудников: {result_upload['message']}")
