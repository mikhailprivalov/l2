"""
WSGI config for laboratory project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)))

os.environ["DJANGO_SETTINGS_MODULE"] = "laboratory.settings"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
