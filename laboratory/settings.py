import logging
import os
import sys
import warnings
from collections import OrderedDict


PROFILING = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = None
DEBUG = "DEBUG" in os.environ
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
    'appconf.apps.AppconfConfig',
    'manifest_loader',
    'dynamic_directory.apps.DynamicDirectoryConfig',
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
    'rmis_integration',
    'rest_framework',
    'integration_framework',
    'statistics_tickets',
    'reports',
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
    'command_utils',
    'doctor_schedule',
    'django_celery_results',
    'dashboards',
    'chats.apps.ChatsConfig',
    'employees.apps.EmployeesConfig',
    'results_feed.apps.ResultsFeedConfig',
    'document_management',
)

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
INSTALLED_APPS_PRE_ADD = ()
INSTALLED_APPS_ADD = ()
MIDDLEWARE_ADD = []

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'django.contrib.auth.backends.RemoteUserBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['integration_framework.authentication.TokenAuthentication'],
}

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
                'context_processors.utils.default_org',
                'context_processors.utils.menu',
                'context_processors.utils.profile',
                'context_processors.utils.local_settings',
            ],
        },
    },
]
WSGI_APPLICATION = 'laboratory.wsgi.application'
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/ui/menu'

CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_NAME = 'csrftoken'

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
    'default': {'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache', 'LOCATION': '127.0.0.1:11211', 'KEY_PREFIX': 'lis' + ("" if not DEBUG else "_DBG")},
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

RMIS_PROXY = None
FIAS_PROXY = None
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

AFTER_DATE_HOLTER = None

DICOM_SEARCH_TAGS = []
DICOM_ADDRESS = ''
DICOM_SERVER_DELETE = ''
DICOM_PORT = None
DICOM_SERVER = ''
DICOM_SERVERS = []

ACSN_MODE = None
REMOTE_DICOM_ADDRESS = ''
REMOTE_DICOM_PORT = None
REMOTE_DICOM_SERVER = ""
REMOTE_DICOM_PEER = ""

URL_RMIS_AUTH = ""
URL_ELN_MADE = ""
URL_SCHEDULE = ""
EXTRA_MASTER_RESEARCH_PK = None
EXTRA_SLAVE_RESEARCH_PK = None

PAP_ANALYSIS_ID = []
PAP_ANALYSIS_FRACTION_QUALITY_ID = []
PAP_ANALYSIS_FRACTION_CONTAIN_ID = []

DEF_LABORATORY_AUTH_PK = None
DEF_LABORATORY_LEGAL_AUTH_PK = None

DEF_CONSULT_AUTH = None
DEF_CONSULT_LEGALAUTH = None

DEATH_RESEARCH_PK = None
GISTOLOGY_RESEARCH_PK = None
PERINATAL_DEATH_RESEARCH_PK = None
COVID_RESEARCHES_PK = []
RESEARCHES_NOT_PRINT_FOOTERS = []

RESEARCH_SPECIAL_REPORT = {"driver_research": None, "weapon_research_pk": None}

CENTRE_GIGIEN_EPIDEMIOLOGY = ""
REGION = ""
EXCLUDE_HOSP_SEND_EPGU = []

SOME_LINKS = []
DISABLED_FORMS = []
DISABLED_AUTO_PRINT_DATE_IN_FORMS = []
DISABLED_RESULT_FORMS = []
DISABLED_STATISTIC_CATEGORIES = []
DISABLED_STATISTIC_REPORTS = []
COVID_QUESTION_ID = None

# Пример указания формы: [{'title': 'Согласие на обработку персональных данных', 'type': '101.02'}, {'title': 'Согласие на медицинское вмешательство', 'type': '101.03'}]
LK_FORMS = []
# Суррогатный юзер - подразделение "Личный кабинет" пользлватель "Личный кабинет"
LK_USER = -1
LK_FILE_SIZE_BYTES = -1
LK_FILE_COUNT = -1

LK_DAY_MONTH_START_SHOW_RESULT = "01.01."

SENTRY_DSN = "https://4a6968777ec240b190abd11cbf1c96e1@sentry.io/3083440"

QUERY_TIMEOUT = 120

FORM_100_08_A4_FORMAT = False
FORCE_CACHALOT = False

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

N3_ODII_BASE_URL = ""
N3_ODII_TOKEN = ""
N3_ODII_SYSTEM_ID = ""

DEFAULT_N3_DOCTOR = {
    "pk": "",
    "snils": "",
    "speciality": "27",
    "position": "73",
    "family": "",
    "name": "",
    "patronymic": "",
}

SYSTEM_AS_VI = False

EMAIL_HOST = None
EMAIL_PORT = 465
EMAIL_HOST_USER = "your@yandex.ru"
EMAIL_HOST_PASSWORD = "password"
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

CELERY_TIMEZONE = 'Asia/Irkutsk'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = 'redis://localhost:6379/4'
CELERY_RESULT_BACKEND = 'django-db'

USE_DEPRECATED_PYTZ = True

FORWARD_DAYS_SCHEDULE = -1

SCHEDULE_AGE_LIMIT_LTE = None
QRCODE_OFFSET_SIZE = {}
LEFT_QRCODE_OFFSET_SIZE = {}
PROTOCOL_PLAIN_TEXT = True
SPLIT_PRINT_RESULT = False
REQUIRED_STATTALON_FIELDS = {}  # {"purpose": "Данные статталона - Цель не указана"}
RESEARCHES_PK_REQUIRED_STATTALON_FIELDS = {}  # {358: {"purpose": "Данные статталона - Цель не указана"}}
DISPANSERIZATION_STATTALON_FIELDS_RESULTS_PK = []
DISPANSERIZATION_STATTALON_FIELDS_PURPOSE_PK = []
HIDE_TITLE_BUTTONS_MAIN_MENU = {}

DASHBOARD_CHARTS_CACHE_TIME_SEC = 60 * 5
OFFSET_HOURS_PLAN_OPERATIONS = 0

TITLE_REPORT_FILTER_STATTALON_FIELDS = []
TITLE_REPORT_FILTER_HAS_ALL_FIN_SOURCE = []

DISPANSERIZATION_SERVICE_PK = {}  # {"pkServiceStart": [12, 13], "pkServiceEnd": [15])}
EXCLUDE_DOCTOR_PROFILE_PKS_ANKETA_NEED = []
DASH_REPORT_LIMIT_DURATION_DAYS = {"years": 2, "months": 13, "weeks": 50, "days": 90, "max_delta_days": 740}
BARCODE_SIZE = "43x25"
SEARCH_PAGE_STATISTIC_PARAMS = {}
MEDEXAM_FIN_SOURCE_TITLE = ""
RESEARCHES_EXCLUDE_AUTO_MEDICAL_EXAMINATION = []
SHOW_EXAMINATION_DATE_IN_PARACLINIC_RESULT_PAGE = {}

REFERENCE_ODLI = False
ODII_METHODS = {}
ODII_METHODS_IEMK = {}
ID_MED_DOCUMENT_TYPE_IEMK_N3 = {}
REMD_ONLY_RESEARCH = []
REMD_EXCLUDE_RESEARCH = []
REMD_RESEARCH_USE_GLOBAL_LEGAL_AUTH = []
LEGAL_AUTH_CODE_POSITION = [334, 336, 6, 4, 335]
REMD_FIELDS_BY_TYPE_DOCUMENT = {"ConsultationProtocol_max": []}
JSON_LOADS_FIELDS_CDA = []
UNLIMIT_PERIOD_STATISTIC_GROUP = []
UNLIMIT_PERIOD_STATISTIC_RESEARCH = []
PRINT_ADDITIONAL_PAGE_DIRECTION_FIN_SOURCE = {}
PRINT_APPENDIX_PAGE_DIRECTION = {}
HOSPITAL_PKS_NOT_CONTROL_DOCUMENT_EXTERNAL_CREATE_DIRECTION = []
STATISTIC_TYPE_DEPARTMENT = [3]
CONTROL_AGE_MEDEXAM = {}  # {"male": {40: 30, 39: 31}, "femail": {40: 32, 39: 33}}
AUTO_PRINT_RESEARCH_DIRECTION = {}  # {perid_month_ago: "10", "researches": [research_pk, research_pk, research_pk]}
ECP_SEARCH_PATIENT = {}
DAYS_AGO_SEARCH_RESULT = {}  # {"isLab: 90", "isInstrument: 365"}
NEED_ORDER_DIRECTION_FOR_DEFAULT_HOSPITAL = False
USE_TFOMS_DISTRICT = False
NEED_RECIEVE_TUBE_TO_PUSH_ORDER = False
TITLE_RESULT_FORM_USE_HOSPITAL_STAMP = False
QR_CODE_ANKETA = ""
RESULT_LABORATORY_FORM = ""
SELF_WATERMARKS = ""
TYPE_COMPANY_SET_DIRECTION_PDF = ""
CPP_SEND_PROTOCOL_ID = -1
CPP_TEMPLATE_XML_DIRECTORY = ""
CDA_TEMPLATE_XML_DIRECTORY = ""
IDGTL_KEY = ""
ROUTE_LIST_ROW_HEIGHTS = 25
OWN_SETUP_TO_SEND_FTP_EXECUTOR = False
FORMS_LABORATORY_DIRECTION_DEFAULT = ""
TUBE_MAX_RESEARCH_WITH_SHARE = False
TUBE_BARCODE_OFFSET_X = 1
TUBE_BARCODE_WIDTH_MINDEX = 0.0125
RELATED_AGREES_FORMS_TOGETHER = {}
FTP_PATH_TO_SAVE = ""

FCM_CERT_PATH = ""
PROMETHEUS_ENABLED = False

TYPE_NUMBER_SYSTEM = []
FTP_SETUP_TO_SEND_HL7_BY_RESEARCHES = {
    "msh": {"app_sender": "", "organization_sender": "", "app_receiver": "", "organization_receiver": ""},
    "obr": {"executer_code": ""},
    "ftp_settings": {"address": "", "user": "", "password": "", "path": ""},
    "id_researches": [],
}

ALLOWED_FORMS_FILE = {
    "100.01": True,
}

try:
    from laboratory.local_settings import *  # noqa: F403,F401
except ImportError:
    pass

MIDDLEWARE += MIDDLEWARE_ADD
MIDDLEWARE = list(OrderedDict.fromkeys(MIDDLEWARE))
INSTALLED_APPS += INSTALLED_APPS_ADD
if not FORCE_CACHALOT:
    INSTALLED_APPS = [x for x in OrderedDict.fromkeys(INSTALLED_APPS_PRE_ADD + INSTALLED_APPS) if x not in ['cachalot']]

if PROMETHEUS_ENABLED:
    INSTALLED_APPS += ['django_prometheus']
    MIDDLEWARE = ['django_prometheus.middleware.PrometheusBeforeMiddleware'] + MIDDLEWARE + ['django_prometheus.middleware.PrometheusAfterMiddleware']

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


def get_env_value(env_variable):
    return os.environ.get(env_variable)


DB_USER = get_env_value('DB_USER')
DB_PASSWORD = get_env_value('DB_PASSWORD')
DB_NAME = get_env_value('DB_NAME')
DB_HOST = get_env_value('DB_HOST')
DB_PORT = get_env_value('DB_PORT')
ENV_SECRET_KEY = get_env_value('SECRET_KEY')

if DB_USER:
    DATABASES['default']['USER'] = DB_USER

if DB_PASSWORD:
    DATABASES['default']['PASSWORD'] = DB_PASSWORD

if DB_NAME:
    DATABASES['default']['NAME'] = DB_NAME

if DB_HOST:
    DATABASES['default']['HOST'] = DB_HOST

if DB_PORT:
    DATABASES['default']['PORT'] = DB_PORT

if ENV_SECRET_KEY:
    SECRET_KEY = ENV_SECRET_KEY

if CACHES.get('default', {}).get('BACKEND') == 'django_redis.cache.RedisCache':
    CACHES['default']['BACKEND'] = 'django.core.cache.backends.redis.RedisCache'


# db = DATABASES.get('default', {})
# db['OPTIONS'] = db.get('OPTIONS', {})
# db['OPTIONS']['options'] = f'-c statement_timeout={QUERY_TIMEOUT * 1000}'
