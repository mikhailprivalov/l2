import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laboratory.settings")
import django  # noqa E402

django.setup()

from external_rest_integration.utils import process_rest_api_pull_result_star  # noqa E402

if __name__ == "__main__":
    process_rest_api_pull_result_star()
