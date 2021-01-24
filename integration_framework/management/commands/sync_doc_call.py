from django.core.management import BaseCommand

import datetime
import time

from doctor_call.models import DoctorCall
from hospitals.models import Hospitals
from laboratory.settings import DOC_CALL_SYNC_WAIT_LONG_TIME_SECS, DOC_CALL_SYNC_WAIT_TIME_SECS
from tfoms.l2 import update_doc_call_status


class Command(BaseCommand):
    help = "Синхронизация заявок на вызов врача"

    def handle(self, *args, **options):
        while True:
            default_h = Hospitals.get_default_hospital()
            self.stdout.write("Start sync at {:%Y-%m-%d %H:%M}".format(datetime.datetime.now()))
            count = 0
            for call in DoctorCall.objects.filter(need_send_status=True):
                count += 1
                hospital: Hospitals = call.hospital or default_h
                self.stdout.write(f"Sync {call.num}:{call.external_num} -> {call.status}")
                resp = update_doc_call_status(call.external_num, call.status, hospital.oid, hospital.code_tfoms)
                self.stdout.write(f"Result: {resp}")
            if count == 0:
                self.stdout.write("Waiting {}\n".format(DOC_CALL_SYNC_WAIT_LONG_TIME_SECS))
                time.sleep(DOC_CALL_SYNC_WAIT_LONG_TIME_SECS)
            else:
                self.stdout.write("Waiting {}\n".format(DOC_CALL_SYNC_WAIT_TIME_SECS))
                time.sleep(DOC_CALL_SYNC_WAIT_TIME_SECS)
