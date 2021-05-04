import logging
import os
import sys
import warnings
from collections import OrderedDict

PROFILING = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'sbib5ss_=z^qngyjqw1om5)4w5l@_ba@pin(7ee^k=#6q=0b)!'
DEBUG = "DLIS" in os.environ
INTERNAL_IPS = ['127.0.0.1', '192.168.0.200', '192.168.0.101', '192.168.102.4', '192.168.0.128']
ALLOWED_HOSTS = ['lis', '127.0.0.1', 'localhost', 'testserver']
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = 1
X_FRAME_OPTIONS = 'ALLOWALL'
CORS_ALLOW_ALL_ORIGINS = True
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'ajax_select',
    'health',
    'appconf.apps.AppconfConfig',
    'manifest_loader',
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
    'api.apps.ApiConfig',
    'discharge',
    'rmis_integration',
    'rest_framework',
    'integration_framework',
    'django_logtail',
    'statistics_tickets',
    'reports',
    'mq.apps.MqConfig',
    'cases.apps.CasesConfig',
    'forms',
    'contracts',
    'lq',
    'treatment',
    'external_system',
    'plans',
    'medical_certificates',
    'list_wait',
    'doctor_call',
    'hospitals.apps.HospitalsConfig',
    'pharmacotherapy',
)

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]
INSTALLED_APPS_PRE_ADD = ()
INSTALLED_APPS_ADD = ()
MIDDLEWARE_ADD = []

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django.contrib.auth.backends.RemoteUserBackend',
]

REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ['integration_framework.authentication.TokenAuthentication']}

ROOT_URLCONF = 'laboratory.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
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
    'default': {'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache', 'LOCATION': '127.0.0.1:11211', 'KEY_PREFIX': 'lis' + ("" if not DEBUG else "_DBG")},
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

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'assets'),)

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

FONTS_FOLDER = os.path.join(BASE_DIR, 'assets', 'fonts')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
FIXTURE_DIRS = [os.path.join(BASE_DIR, 'fixtures')]
AUTH_PROFILE_MODULE = 'users.models.DoctorsProfile'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'base': {'format': '\n[%(asctime)s] [%(levelname)s] %(module)s\n' 'Request: %(path)s [%(method)s] %(user)s %(data)s\n' 'Body: %(body)s\n' '%(stack_info)s\n'},
    },
    'filters': {
        'requestdata': {
            '()': 'utils.filters.RequestDataFilter',
        },
    },
    'handlers': {
        'file': {'level': 'DEBUG', 'class': 'logging.FileHandler', 'filters': ['requestdata'], 'filename': os.path.join(BASE_DIR, 'logs', 'log.txt'), 'formatter': 'base'},
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
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
)
LDAP = {
    "enable": False,
    "server": {"host": "192.168.0.254", "port": 389, "user": "cn=Admin,dc=fc-ismu,dc=local", "password": ""},
    "user_object": "(objectClass=*)",
    "base": "dc=fc-ismu,dc=local",
}
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 15 * 60 * 60

MAX_RMIS_THREADS = 10

RMIS_UPLOAD_WAIT_TIME_SECS = 8
RMIS_UPLOAD_WAIT_LONG_TIME_SECS = 300
RMIS_UPLOAD_COUNT_TO_REFRESH_CLIENT = 40
RMIS_UPLOAD_COUNT = 20

DOC_CALL_SYNC_WAIT_TIME_SECS = 8
DOC_CALL_SYNC_WAIT_LONG_TIME_SECS = 300

RATELIMIT_VIEW = 'mainmenu.views.ratelimited'

RMIS_PROXY = None
AFTER_DATE = None
AFTER_DATE_HOLTER = None

MAX_DOC_CALL_EXTERNAL_REQUESTS_PER_DAY = 3

PREFETCH_DEBUG = False
PREFETCH_ENABLED = False
PREFETCH_MAX_THREADS = 15

LOG_SQL = False


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"


TESTS_IN_PROGRESS = False
if 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]:
    logging.disable(logging.CRITICAL)
    PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)
    DEBUG = False
    TEMPLATE_DEBUG = False
    TESTS_IN_PROGRESS = True
    MIGRATION_MODULES = DisableMigrations()

warnings.filterwarnings('ignore', message='DateTimeField*', category=RuntimeWarning)
MAX_UPLOAD_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600

DEBUG = False

LOGOUT_REDIRECT_URL = '/'

LOGTAIL_FILES = {'L2': os.path.join(BASE_DIR, 'logs', 'log.txt')}

RMQ_URL = "amqp://t:t@localhost:5672/"
RMQ_ENABLED = False

WS_BASE = "localhost"
WS_PORT = 8822
WS_ENABLED = False


def SILKY_INTERCEPT_FUNC(request):
    return request.path not in ['/mainmenu/']


AFTER_DATE_HOLTER = None

DICOM_SEARCH_TAGS = []
DICOM_ADDRESS = ''
DICOM_PORT = None
DICOM_SERVER = ""
URL_RMIS_AUTH = ""
URL_ELN_MADE = ""
URL_SCHEDULE = ""

SENTRY_DSN = "https://4a6968777ec240b190abd11cbf1c96e1@sentry.io/3083440"

QUERY_TIMEOUT = 120

FORM_100_08_A4_FORMAT = False
FORCE_CACHALOT = False

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

try:
    from laboratory.local_settings import *  # noqa: F403,F401
except ImportError:
    pass

if PROFILING:
    INSTALLED_APPS += ('silk',)
    MIDDLEWARE += ('silk.middleware.SilkyMiddleware',)

MIDDLEWARE += MIDDLEWARE_ADD
MIDDLEWARE = list(OrderedDict.fromkeys(MIDDLEWARE))
INSTALLED_APPS += INSTALLED_APPS_ADD
if not FORCE_CACHALOT:
    INSTALLED_APPS = [x for x in OrderedDict.fromkeys(INSTALLED_APPS_PRE_ADD + INSTALLED_APPS) if x not in ['cachalot']]

WS_URL = "ws://{}:{}/".format(WS_BASE, WS_PORT)

if LOG_SQL:
    LOGGING['loggers']['django.db.backends'] = {
        'level': 'DEBUG',
        'handlers': ['console'],
    }

MANIFEST_LOADER = {
    'cache': False,
    'output_dir': 'webpack_bundles/',
    'manifest_file': os.path.join(BASE_DIR, 'assets/webpack_bundles/manifest.json'),
    'ignore_missing_assets': DEBUG,
}

# db = DATABASES.get('default', {})
# db['OPTIONS'] = db.get('OPTIONS', {})
# db['OPTIONS']['options'] = f'-c statement_timeout={QUERY_TIMEOUT * 1000}'
