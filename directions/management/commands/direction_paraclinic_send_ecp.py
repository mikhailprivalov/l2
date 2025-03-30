from dateutil.relativedelta import relativedelta

from directions.sql_func import get_paraclini_directions_for_send_ecp_queue
from laboratory.settings import ID_RESERACH_FLG
from laboratory.utils import current_time
from django.core.management.base import BaseCommand

from api.dicom import check_server_port
from appconf.manager import SettingManager
from l2vi.integration import send_paraclinic_direction_to_ecp


class Command(BaseCommand):
    help = "Отправить лабораторные результаты в ЕЦП"

    def handle(self, *args, **kwargs):
        base = SettingManager.get_api_ecp_base_url()
        if base != 'empty':
            available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
            if not available:
                self.stdout.write({"error": True, "message": "Cервер отправки в ЕЦП не доступен"})
            if not ID_RESERACH_FLG:
                self.stdout.write({"error": True, "message": "ID_RESERACH_FLG не доступен"})

        date_start = current_time(only_date=False) + relativedelta(hours=-36)
        date_start = date_start.strftime('%Y%m%d %H:%M:%S')
        date_end = current_time(only_date=False)
        date_end = date_end.strftime('%Y%m%d %H:%M:%S')
        result = get_paraclini_directions_for_send_ecp_queue(ID_RESERACH_FLG, date_start, date_end)
        today_date_d = current_time(only_date=False)
        today_date = today_date_d.strftime('%d.%m.%Y')
        data = [
            {
                "family": i.patient_family,
                "name": i.patient_name,
                "patronymic": i.patient_patronymic,
                "birthday": i.patient_birthday,
                "direction": i.napravleniye_id,
                "todayDate": today_date
             }
            for i in result
        ]

        res = send_paraclinic_direction_to_ecp(data)
        self.stdout.write(f"{res}\n")
