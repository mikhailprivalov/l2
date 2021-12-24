from django.core.management import BaseCommand
from laboratory.settings import PERINATAL_DEATH_RESEARCH_PK
from statistic.sql_func import sql_get_date_death
from datetime import datetime
from clients.models import Card


class Command(BaseCommand):
    help = "Проверка и заполнение дат смерти: формат даты: 1970-01-01"

    def add_arguments(self, parser):
        parser.add_argument('date_range', type=str)

    def handle(self, *args, **kwargs):
        data = kwargs["date_range"].split(":")
        start_date = f"{data[0]} 00:00:01"
        end_date = f"{data[1]} 23:59:59"
        if PERINATAL_DEATH_RESEARCH_PK:
            results_death = sql_get_date_death(PERINATAL_DEATH_RESEARCH_PK, start_date, end_date)
            for i in results_death:
                date_death = datetime.strptime(i.value, "%Y-%m-%d").date()
                if date_death:
                    client_obj = Card.objects.get(pk=i.client_id)
                    client_obj.death_date = date_death
                    client_obj.save()
