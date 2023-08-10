import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laboratory.settings")
import django  # noqa E402

django.setup()

from ftp_orders.main import process_pull_start_orders  # noqa E402

if __name__ == "__main__":
    process_pull_start_orders()
