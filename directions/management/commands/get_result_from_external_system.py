from external_rest_integration.utils import rest_api_pull_result
from django.core.management.base import BaseCommand



class Command(BaseCommand):
    help = "Получить ре-таты извне"

    def handle(self, *args, **kwargs):
        rest_api_pull_result()
