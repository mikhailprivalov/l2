import os
import django  # noqa E402


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laboratory.settings")

django.setup()

from directions.utils import process_gistology_result_upload_start  # noqa E402


process_gistology_result_upload_start()
