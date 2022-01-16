import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laboratory.settings')

app = Celery('l2')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
