from dateutil.relativedelta import relativedelta
import simplejson as json

from directions.sql_func import get_directions_for_send_ecp_by_researches, get_directions_for_send_ecp_by_dirs
from laboratory.settings import REMD_ONLY_RESEARCH
from laboratory.utils import current_time
from django.core.management.base import BaseCommand

from api.dicom import check_server_port
from appconf.manager import SettingManager
from directions.models import Napravleniya, DirectionParamsResult
from l2vi.integration import send_gistology_direction_to_ecp


class Command(BaseCommand):
    help = "Отправить гистологические результаты в ЕЦП"

    def add_arguments(self, parser):
        """
        :param path - файл с картами пациентов + диагноз Д-учета
        """
        parser.add_argument('dirs', type=str)

    def handle(self, *args, **kwargs):
        base = SettingManager.get_api_ecp_base_url()
        if base != 'empty':
            available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
            if not available:
                self.stdout.write({"error": True, "message": "Cервер отправки в ЕЦП не доступен"})
        current_time_ecp_upload = SettingManager.rmis_upload_hours_interval()
        date_start = current_time(only_date=False) + relativedelta(hours=-48)
        date_start = date_start.strftime('%Y%m%d %H:%M:%S')

        date_end = current_time(only_date=False) + relativedelta(hours=-current_time_ecp_upload)
        date_end = date_end.strftime('%Y%m%d %H:%M:%S')

        dirs = kwargs["dirs"]
        dirs = dirs.split(",")
        if len(dirs) > 0:
            dirs = [int(i) for i in dirs]
            print(dirs)
            d_qs = get_directions_for_send_ecp_by_dirs(tuple(REMD_ONLY_RESEARCH), tuple(dirs))
        else:
            d_qs = get_directions_for_send_ecp_by_researches(tuple(REMD_ONLY_RESEARCH), date_start, date_end)
        directions = [i.napravleniye_id for i in d_qs]
        dir_params = DirectionParamsResult.objects.filter(napravleniye_id__in=directions)
        result_params = {}
        for i in dir_params:
            if i.title == "Маркировка материала":
                marking_biopsy = json.loads(i.value)
                marking_biopsy_local_id = marking_biopsy['rows'][0][1]
                marking_biopsy_local_id = marking_biopsy_local_id.split("/")
                if len(marking_biopsy_local_id) < 2:
                    continue
                result_params[i.napravleniye_id] = marking_biopsy_local_id[1]
        directions_iss = [
            {
                "directionId": d.napravleniye_id,
                "issId": d.iss_id,
                "dateRmis": d.rmis_direction_date,
                "rmis_number": d.rmis_number,
                "markBiopsy": result_params.get(d.napravleniye_id),
                "rmis_login": d.rmis_login,
                "rmis_password": d.rmis_password,
            }
            for d in d_qs
            if result_params.get(d.napravleniye_id)
        ]
        res = send_gistology_direction_to_ecp(directions_iss)
        self.stdout.write(f"{res}\n")
        count = 0
        for n in Napravleniya.objects.filter(pk__in=directions):
            n.result_rmis_send = True
            n.save()
            count += 1
        self.stdout.write(f"{count}\n")
