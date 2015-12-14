#
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'sbib5ss_=z^qngyjqw1om5)4w5l@_ba@pin(7ee^k=#6q=0b)!'

DEBUG = True

ALLOWED_HOSTS = ['192.168.0.105', 'k105', 'k105-2', 'lis.fc-ismu.local', 'lis', '127.0.0.1', 'localhost']

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = 1
X_FRAME_OPTIONS = 'DENY'
DEBUG = False

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'debug_panel',
    'cachalot',
    'users',
    'dashboard',
    'podrazdeleniya',
    'clients',
    'results',
    'researches',
    'directions',
    'receivematerial',
    'construct',
    'slog',
    'directory',
    'statistic',
    'api',
    'ajax_select'
)

LOGIN_REDIRECT_URL = '/'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'debug_panel.middleware.DebugPanelMiddleware',
)

ROOT_URLCONF = 'laboratory.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'laboratory.wsgi.application'
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/dashboard/'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lis2',
        'USER': 'postgres',
        'PASSWORD': '123456',
        # 'HOST': '192.168.122.45',
        'HOST': '192.168.0.252',
        # 'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'lis2',  # TODO: lis
            'USER': 'postgres',
            'PASSWORD': '123456',
            # 'HOST': '192.168.122.45',
            'HOST': '192.168.0.105',
            # 'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '192.168.0.252:11211',  # TODO: 11211
        'KEY_PREFIX': 'lis_test'
    },
    'debug-panel': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/debug-panel-cache-2',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 200
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

DATE_FORMAT = 'd.m.Y'

TIME_FORMAT = 'd.m.Y'

USE_TZ = True

TIME_ZONE = 'Asia/Irkutsk'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/



STATIC_URL = '/static/'
# STATIC_ROOT = '/var/www/laboratory/static/'
# STATIC_ROOT = '/webapps/lis/static/'
STATIC_ROOT = '/home/lisuser/lis/static/'
DEBUG = False
if DEBUG:
    STATIC_ROOT = '/webapps/lis2/static/'  # TODO: lis
'''
if not DEBUG:
    STATIC_ROOT = '/home/dev/PycharmProjects/laboratory/static/'''

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

AUTH_PROFILE_MODULE = 'users.models.DoctorsProfile'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs') + '/log.txt',
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
    'cachalot.panels.CachalotPanel',
)

LDAP = {
    "enable": True,
    "server": {
        "host": "192.168.0.254",
        "port": 389,
        "user": "cn=Admin,dc=fc-ismu,dc=local",
        "password": "cnfkbybd"
    },
    "user_object": "(objectClass=*)",
    "base": "dc=fc-ismu,dc=local"

}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 15 * 60 * 60

DEBUG = True
