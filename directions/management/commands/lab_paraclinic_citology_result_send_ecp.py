from dateutil.relativedelta import relativedelta

from brokers_queue.rmq.publisher import broker_publish_msg
from laboratory.settings import RMQ_AUTH_PARAM
from laboratory.utils import current_time
from django.core.management.base import BaseCommand

from api.dicom import check_server_port
from appconf.manager import SettingManager
from directions.models import Napravleniya
from l2vi.integration import send_lab_direction_to_ecp
from django.db import connection
from utils.db import namedtuplefetchall


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
            d_qs = sql_01(date)
        if SettingManager.use_rmq_for_sendlabresultecp():
            use_exchange_name = RMQ_AUTH_PARAM.get("lab_exchange_name")
            use_routing_key = RMQ_AUTH_PARAM.get("lab_routing_key")
            for i in d_qs:
                broker_publish_msg(i.pk, use_exchange_name=use_exchange_name, use_routing_key=use_routing_key)
                i.need_resend_ecp = True
                i.save()
        else:
            base = SettingManager.get_api_ecp_base_url()
            if base != 'empty':
                available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
                if not available:
                    self.stdout.write({"error": True, "message": "Cервер отправки в ЕЦП не доступен"})
            directions = [i.pk for i in d_qs]
            res = send_lab_direction_to_ecp(directions)
            self.stdout.write(f"{res}\n")
            count = 0
            for n in d_qs:
                n.rmis_resend_services = True
                n.save()
                count += 1
            self.stdout.write(f"{count}\n")


def sql_01(d_s):
    """
    Для журнала новородок первичные
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    directions_napravleniya.id as pk
                    
                    FROM directions_napravleniya
                    LEFT JOIN directions_issledovaniya di on directions_napravleniya.id = di.napravleniye_id
                    LEFT JOIN directory_researches dr on di.research_id = dr.id
                    WHERE 
                      directions_napravleniya.total_confirmed = true
                      AND
                      directions_napravleniya.ecp_direction_number is NULL 
                      AND
                      directions_napravleniya.rmis_resend_services=False
                      AND
                      directions_napravleniya.last_confirmed_at > %(d_start)s
                      AND dr.is_paraclinic = true 
                      AND dr.is_lab = true
                    order by directions_napravleniya.id
                """,
            params={'d_start': d_s},
        )

        rows = namedtuplefetchall(cursor)
    return rows
