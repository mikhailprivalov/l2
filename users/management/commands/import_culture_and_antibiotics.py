from django.core.management.base import BaseCommand
from directory.models import Researches, ParaclinicInputGroups, ParaclinicInputField
import json
from laboratory import utils


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - файл
        """
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        self.stdout.write("Path: " + fp)
        with open(fp) as json_file:
            data = json.load(json_file)
            print(data)
