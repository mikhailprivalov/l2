import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laboratory.settings")
import django  # noqa E402

django.setup()

from education.main import process_update_enrollees  # noqa E402

if __name__ == "__main__":
    process_update_enrollees()
