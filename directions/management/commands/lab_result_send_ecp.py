from dateutil.relativedelta import relativedelta

from brokers_queue.rmq.publisher import broker_publish_msg
from laboratory.settings import RMQ_AUTH_PARAM
from laboratory.utils import current_time
from django.core.management.base import BaseCommand

from api.dicom import check_server_port
from appconf.manager import SettingManager
from directions.models import Napravleniya
from l2vi.integration import send_lab_direction_to_ecp


class Command(BaseCommand):
    help = "Отправить лабораторные результаты в ЕЦП"

    def add_arguments(self, parser):
        parser.add_argument('dirs', type=str)

    def handle(self, *args, **kwargs):
        if kwargs["dirs"]:
            dirs = kwargs["dirs"]
        else:
            dirs = ''
        if len(dirs) > 0:
            dirs = [int(i) for i in dirs.split(",")]
            d_qs = Napravleniya.objects.filter(pk__in=dirs)
        else:
            date = current_time() + relativedelta(days=-2)
            d_qs = Napravleniya.objects.filter(total_confirmed=True, ecp_direction_number=None, rmis_resend_services=False, last_confirmed_at__gte=date)
        directions = [i.pk for i in d_qs]
        if SettingManager.use_rmq_for_sendlabresultecp():
            use_exchange_name = RMQ_AUTH_PARAM.get("lab_exchange_name")
            use_routing_key = RMQ_AUTH_PARAM.get("lab_routing_key")
            for i in directions:
                broker_publish_msg(i.pk, use_exchange_name=use_exchange_name, use_routing_key=use_routing_key)
                i.need_resend_ecp = True
                i.save()
        else:
            base = SettingManager.get_api_ecp_base_url()
            if base != 'empty':
                available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
                if not available:
                    self.stdout.write({"error": True, "message": "Cервер отправки в ЕЦП не доступен"})
            res = send_lab_direction_to_ecp(directions)
            self.stdout.write(f"{res}\n")
            count = 0
            for n in d_qs:
                n.rmis_resend_services = True
                n.save()
                count += 1
            self.stdout.write(f"{count}\n")
