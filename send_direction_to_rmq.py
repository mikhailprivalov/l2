import os
import django  # noqa E402


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laboratory.settings")
django.setup()

from directions.utils import process_direction_send_rmq_start  # noqa E402

if __name__ == "__main__":
    process_direction_send_rmq_start()
