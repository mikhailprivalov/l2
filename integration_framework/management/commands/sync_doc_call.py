from django.core.management import BaseCommand

import datetime
import time

from appconf.manager import SettingManager
from doctor_call.models import DoctorCall
from hospitals.models import Hospitals
from laboratory.settings import DOC_CALL_SYNC_WAIT_LONG_TIME_SECS, DOC_CALL_SYNC_WAIT_TIME_SECS
from tfoms.l2 import update_doc_call_status, send_doc_call


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
                self.stdout.write(f"Sync status {call.num}:{call.external_num} -> {call.status}")
                resp = update_doc_call_status(call.external_num, call.status, hospital.oid, hospital.code_tfoms)
                self.stdout.write(f"Result: {resp}")
            if SettingManager.l2('send_doc_calls'):
                call: DoctorCall
                for call in DoctorCall.objects.filter(need_send_to_external=True, hospital__isnull=False).exclude(hospital__remote_url='').exclude(hospital__remote_token=''):
                    try:
                        base = call.hospital.remote_url
                        token = call.hospital.remote_token
                        data = call.json()
                        send_doc_call(base, token, {
                            "patientData": {
                                'enp':  call.client.individual.get_enp(),
                            },
                            "form": data,
                        })
                    except Exception as e:
                        self.stdout.write(str(e))
                    call.need_send_to_external = False
                    call.save(update_fields=['need_send_to_external'])
            if count == 0:
                self.stdout.write("Waiting {}\n".format(DOC_CALL_SYNC_WAIT_LONG_TIME_SECS))
                time.sleep(DOC_CALL_SYNC_WAIT_LONG_TIME_SECS)
            else:
                self.stdout.write("Waiting {}\n".format(DOC_CALL_SYNC_WAIT_TIME_SECS))
                time.sleep(DOC_CALL_SYNC_WAIT_TIME_SECS)
