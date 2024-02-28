import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laboratory.settings")
import django  # noqa E402

django.setup()

from ftp_orders.main import process_push_results_start  # noqa E402

if __name__ == "__main__":
    process_push_results_start()
