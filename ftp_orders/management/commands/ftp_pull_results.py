from django.core.management.base import BaseCommand

from ftp_orders.main import process_pull_orders


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        process_pull_orders()
