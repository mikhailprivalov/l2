from django.core.management.base import BaseCommand

from directions.models import MonitoringResult
from calendar import monthrange
from datetime import date


class Command(BaseCommand):
    help = "Обновить period_date гдк пусто"

    def handle(self, *args, **kwargs):
        monitoring_result = MonitoringResult.objects.filter(period_date=None)
        for mr in monitoring_result:
            if mr.research.type_period == "PERIOD_HOUR" or mr.research.type_period == "PERIOD_DAY":
                if None in [mr.period_param_year, mr.period_param_month, mr.period_param_day]:
                    continue
                mr.period_date = date(mr.period_param_year, mr.period_param_month, mr.period_param_day)
                mr.save()
            if mr.research.type_period == "PERIOD_MONTH":
                last_day_month = monthrange(mr.period_param_year, mr.period_param_month)[1]
                mr.period_date = date(mr.period_param_year, mr.period_param_month, last_day_month)
                mr.save()

            if mr.research.type_period == "PERIOD_WEEK":
                mr.period_date = mr.period_param_week_date_start
                mr.save()
