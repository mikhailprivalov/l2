import os
import sys
import django  # noqa E402
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laboratory.settings")
django.setup()

from ftp_orders.json_import import process_pull_json_results_start  # noqa E402

if __name__ == "__main__":
    process_pull_json_results_start()
