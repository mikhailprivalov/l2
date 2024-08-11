from django.core.management.base import BaseCommand

from api.dicom import check_server_port
from appconf.manager import SettingManager
from directions.models import Napravleniya
from l2vi.integration import send_lab_direction_to_ecp


class Command(BaseCommand):
    help = "Отправить лабораторные результаты в ЕЦП"

    def handle(self, *args, **kwargs):
        base = SettingManager.get_api_ecp_base_url()
        if base != 'empty':
            available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
            if not available:
                self.stdout.write({"error": True, "message": "Cервер отправки в ЕЦП не доступен"})
        d_qs = Napravleniya.objects.filter(total_confirmed=True, ecp_direction_number=None, rmis_resend_services=False)
        directions = [i.pk for i in d_qs]
        res = send_lab_direction_to_ecp(directions)
        self.stdout.write(f"{res}\n")
        for n in d_qs:
            n.rmis_resend_services = True
            n.save()
