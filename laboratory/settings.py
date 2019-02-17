import logging
import os
import sys
from collections import OrderedDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'sbib5ss_=z^qngyjqw1om5)4w5l@_ba@pin(7ee^k=#6q=0b)!'
DEBUG = "DLIS" in os.environ
INTERNAL_IPS = ['127.0.0.1', '192.168.0.200', '192.168.0.101', '192.168.102.4', '192.168.0.128']
ALLOWED_HOSTS = ['192.168.0.76', 'lis', '127.0.0.1', 'localhost', 'testserver']
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = 1
X_FRAME_OPTIONS = 'ALLOWALL'
CORS_ORIGIN_ALLOW_ALL = True
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',
    'ajax_select',
    'health',
    'appconf',
    'clients',
    'users',
    'mainmenu',
    'podrazdeleniya',
    'results',
    'researches',
    'directions',
    'receivematerial',
    'construct',
    'slog',
    'directory',
    'statistic',
    'api',
    'discharge',
    'rmis_integration',
    'rest_framework',
    'django_logtail',
    'corsheaders',
    'statistics_tickets',
    'webpack_loader',
    'reports',
    'mq.apps.MqConfig',
    'cases.apps.CasesConfig',
    'forms',
)
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.common.CommonMiddleware',
]
INSTALLED_APPS_PRE_ADD = ()
INSTALLED_APPS_ADD = ()
MIDDLEWARE_ADD = []

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django.contrib.auth.backends.RemoteUserBackend',
]

ROOT_URLCONF = 'laboratory.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'context_processors.utils.card_bases',
                'context_processors.utils.ws',
                'context_processors.utils.menu',
                'context_processors.utils.profile',
            ],
        },
    },
]
WSGI_APPLICATION = 'laboratory.wsgi.application'
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/mainmenu/'
# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'l2',
        'USER': 'postgres',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'lis' + ("" if not DEBUG else "_DBG")
    },
}
LANGUAGE_CODE = 'ru-ru'
DATE_FORMAT = 'd.m.Y'
DATE_FORMAT_SHORT = 'd.m.y'
TIME_FORMAT = 'd.m.Y'
USE_TZ = True
TIME_ZONE = 'Asia/Irkutsk'
USE_I18N = True
USE_L10N = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'assets'),
)

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

FONTS_FOLDER = os.path.join(BASE_DIR, 'assets', 'fonts')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
FIXTURE_DIRS = (os.path.join(BASE_DIR, 'fixtures'),)
AUTH_PROFILE_MODULE = 'users.models.DoctorsProfile'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'base': {
            'format': '\n[%(asctime)s] [%(levelname)s] %(module)s\n'
                      'Request: %(path)s [%(method)s] %(user)s %(data)s\n'
                      'Body: %(body)s\n'
                      '%(stack_info)s\n'
        }
    },
    'filters': {
        'requestdata': {
            '()': 'utils.filters.RequestDataFilter',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filters': ['requestdata'],
            'filename': os.path.join(BASE_DIR, 'logs') + '/log.txt',
            'formatter': 'base'
        },
        'pika': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs') + '/log-pika.txt',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'pika': {
            'handlers': ['pika'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'cachalot.panels.CachalotPanel',
)
LDAP = {
    "enable": False,
    "server": {
        "host": "192.168.0.254",
        "port": 389,
        "user": "cn=Admin,dc=fc-ismu,dc=local",
        "password": ""
    },
    "user_object": "(objectClass=*)",
    "base": "dc=fc-ismu,dc=local"
}
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 15 * 60 * 60

RATELIMIT_VIEW = 'mainmenu.views.ratelimited'

class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"


TESTS_IN_PROGRESS = False
if 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]:
    logging.disable(logging.CRITICAL)
    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )
    DEBUG = False
    TEMPLATE_DEBUG = False
    TESTS_IN_PROGRESS = True
    MIGRATION_MODULES = DisableMigrations()
CACHALOT_ENABLED = True

import warnings

warnings.filterwarnings('ignore', message='DateTimeField*', category=RuntimeWarning)
MAX_UPLOAD_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600

DEBUG = True

LOGOUT_REDIRECT_URL = '/'

LOGTAIL_FILES = {
    'L2': os.path.join(BASE_DIR, 'logs', 'log.txt')
}

RMQ_URL = "amqp://t:t@localhost:5672/"
RMQ_ENABLED = False

WS_BASE = "localhost"
WS_PORT = 8822
WS_ENABLED = False

try:
    from laboratory.local_settings import *
except ImportError:
    pass

MIDDLEWARE += MIDDLEWARE_ADD
MIDDLEWARE = list(OrderedDict.fromkeys(MIDDLEWARE))
INSTALLED_APPS += INSTALLED_APPS_ADD
INSTALLED_APPS = list(OrderedDict.fromkeys(INSTALLED_APPS_PRE_ADD + INSTALLED_APPS))

WS_URL = "ws://{}:{}/".format(WS_BASE, WS_PORT)


WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'webpack_bundles/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats.json'),
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': ['.+\.hot-update.js', '.+\.map']
    }
}
