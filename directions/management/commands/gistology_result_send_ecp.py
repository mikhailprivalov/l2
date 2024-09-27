from dateutil.relativedelta import relativedelta
import simplejson as json

from directions.sql_func import get_directions_for_send_ecp_by_researches
from laboratory.settings import REMD_ONLY_RESEARCH
from laboratory.utils import current_time
from django.core.management.base import BaseCommand

from api.dicom import check_server_port
from appconf.manager import SettingManager
from directions.models import Napravleniya, DirectionParamsResult
from l2vi.integration import send_gistology_direction_to_ecp


class Command(BaseCommand):
    help = "Отправить гистологические результаты в ЕЦП"

    def handle(self, *args, **kwargs):
        base = SettingManager.get_api_ecp_base_url()
        if base != 'empty':
            available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
            if not available:
                self.stdout.write({"error": True, "message": "Cервер отправки в ЕЦП не доступен"})
        date_start = current_time(only_date=True) + relativedelta(minutes=-120)
        print(date_start)

        current_time_ecp_upload = SettingManager.rmis_upload_hours_interval()
        date_end = current_time(only_date=True)
        d_qs = get_directions_for_send_ecp_by_researches(tuple(REMD_ONLY_RESEARCH), '20240927 20:00:00', '20240927 23:00:00')
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
            {"directionId": i.napravleniye_id, "issId": i.iss_id, "dateRmis": i.rmis_direction_date, "rmis_number": i.rmis_number, "markBiopsy": result_params.get(i.napravleniye_id)}
            for i in d_qs if result_params.get(i.napravleniye_id)
        ]
        res = send_gistology_direction_to_ecp(directions_iss)
        self.stdout.write(f"{res}\n")
        count = 0
        for n in Napravleniya.objects.filter(pk__in=directions):
            n.rmis_resend_services = True
            # n.save()
            count += 1
        self.stdout.write(f"{count}\n")
