from dateutil.relativedelta import relativedelta
from brokers_queue.rmq.publisher import broker_publish_msg
from laboratory.settings import RMQ_AUTH_PARAM
from laboratory.utils import current_time
from django.core.management.base import BaseCommand
from directions.models import Napravleniya


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
            date = current_time() + relativedelta(days=-5)
            d_qs = Napravleniya.objects.filter(total_confirmed=True, ecp_direction_number=None, rmis_resend_services=False, last_confirmed_at__gte=date, received_by_rmq=False)
        use_exchange_name = RMQ_AUTH_PARAM.get("lab_exchange_name")
        use_routing_key = RMQ_AUTH_PARAM.get("lab_routing_key")
        for i in d_qs:
            broker_publish_msg(i.pk, use_exchange_name=use_exchange_name, use_routing_key=use_routing_key)
            i.need_resend_ecp = True
            i.save()
