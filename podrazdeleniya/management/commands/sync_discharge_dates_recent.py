from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db.models import Q
from datetime import datetime, time as dtime

from api.stationar.sql_func import get_extract_by_main_directions
from appconf.manager import SettingManager
from laboratory import utils
from laboratory.settings import CDA_ID_FOR_DATE_IS_EXTRACT
from podrazdeleniya.models import PatientToBed


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('dirs', type=str)

    def handle(self, *args, **kwargs):
        dirs = []
        if kwargs["dirs"]:
            dirs = kwargs["dirs"]
        date_end = utils.current_time()
        days_ago = SettingManager.get("days_before_hosp", default='35', default_type='i')
        date_start = date_end + relativedelta(days=-days_ago)
        date_start = datetime.combine(date_start, dtime.min)
        dirs_data = dirs.split(",")
        if len(dirs_data) > 0:
            patient_bed = PatientToBed.objects.filter(direction_id__in=[dirs_data])
        else:
            patient_bed = PatientToBed.objects.filter((Q(date_in__gte=date_start) | Q(plan_date_in__gte=date_start) & Q(is_extract=False)))
        direction_pk = [i.direction_id for i in patient_bed if i.direction]
        result = get_extract_by_main_directions(tuple(direction_pk), CDA_ID_FOR_DATE_IS_EXTRACT)
        for i in result:
            self.stdout.write(f"{i.main_direction_id}, {i.field_value}, {i.title}")
            ptb = PatientToBed.objects.filter(direction_id=i.main_direction_id).first()
            ptb.date_out = i.field_value
            ptb.plan_date_out = i.field_value
            ptb.is_extract = True
            ptb.save()
            self.stdout.write(f"{ptb}")
