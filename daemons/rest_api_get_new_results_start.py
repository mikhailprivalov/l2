import os
import sys
import django  # noqa E402
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laboratory.settings")
django.setup()

from external_rest_integration.utils import process_rest_api_get_new_results_start  # noqa E402

if __name__ == "__main__":
    process_rest_api_get_new_results_start()
