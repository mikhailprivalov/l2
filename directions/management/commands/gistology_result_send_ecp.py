from directions.utils import gistology_result_send
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Отправить гистологические результаты в ЕЦП"

    def add_arguments(self, parser):
        """
        :param path - файл с картами пациентов + диагноз Д-учета
        """
        parser.add_argument('dirs', type=str)

    def handle(self, *args, **kwargs):
        if kwargs["dirs"]:
            dirs = kwargs["dirs"]
        else:
            dirs = ''
        gistology_result_send(dirs)
