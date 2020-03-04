"""
WSGI config for laboratory project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laboratory.settings")

application = get_wsgi_application()

# Нижнее до лучших времен: после разбирательств с gunicorn
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration

# from appconf.manager import SettingManager
# from laboratory.settings import SENTRY_DSN

# sentry_sdk.init(
#     dsn=SENTRY_DSN,
#     integrations=[DjangoIntegration()],
#     send_default_pii=True,
#     environment=SettingManager.get("org_title") or "Default L2"
# )
