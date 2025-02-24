from django.core.management.base import BaseCommand
from openpyxl import load_workbook

from hospitals.models import Hospitals


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - путь до файла с работниками
        :param organization_id = id организации в бд (hospital_id)
        """
        parser.add_argument('path', type=str)
        parser.add_argument('organization_id', type=int)

    def handle(self, *args, **kwargs):
        file_path = kwargs["path"]
        organization_id = kwargs["organization_id"]

