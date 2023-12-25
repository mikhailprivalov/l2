import datetime

from django.core.management.base import BaseCommand
from openpyxl import load_workbook

from clients.models import Card, Individual
from ecp_integration.integration import search_patient_ecp_by_fio, attach_patient_ecp
from utils.dates import normalize_dots_date
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    # def add_arguments(self, parser):
    #     """
    #     :param path - файл с пациентами - участок ecp
    #     """
    #     parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        # fp = kwargs["path"]
        # self.stdout.write("Path: " + fp)
        current_date = datetime.datetime.now()
        children_individual = Individual.objects.filter(birthday__range=[(current_date - current_date.year - 14), ])

