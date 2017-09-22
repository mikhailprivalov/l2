import datetime

import requests
from django.core.management import BaseCommand
from django.db.models import Q
from django.utils.timezone import now
from requests import Session
from requests.auth import HTTPBasicAuth
from requests_toolbelt import MultipartEncoder
from zeep.transports import Transport
from zeep import Client
from time import strftime, gmtime, localtime
from appconf.manager import SettingManager
from directions.models import Issledovaniya, Result
from django.test import Client as TC
from rmis_integration.client import Client as RC

import simplejson as json


class Command(BaseCommand):
    help = "Выгрузка результатов и направлений в РМИС"

    def handle(self, *args, **options):
        self.stdout.write("{:%Y-%m-%d %H:%M}".format(datetime.datetime.now()) + " - TRIGGER")
        c = RC()
        self.stdout.write(json.dumps(c.directions.check_and_send_all(self.stdout)))

