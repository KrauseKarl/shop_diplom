import os
import logging.config
from pathlib import Path
from os import environ


BASE_DIR = Path(__file__).resolve().parent.parent
# DATABASE_DIR = BASE_DIR / "pg_data"
# DATABASE_DIR.mkdir(exist_ok=True)

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-hgtz)@6%!&a)!vn^wi#i-3$uxchie4%f#fz+2lnor*5r$2(q2d"
)

DEBUG = os.getenv("DEBUG", "0") == "1"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "0.0.0.0"
] + os.getenv("ALLOWED_HOSTS", "127.0.0.1").split(",")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 'easy_thumbnails',

    # my app
    'app_item.apps.AppItemConfig',
    'app_user.apps.AppUserConfig',
    'app_store.apps.AppStoreConfig',
    'app_order.apps.AppOrderConfig',
    'app_cart.apps.AppCartConfig',
    'app_invoice.apps.AppInvoiceConfig',
    'app_settings.apps.AppSettingsConfig',
    'app_favorite.apps.AppFavoriteConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'shop.middleware.userMiddleware.simple_middleware',
]

ROOT_URLCONF = 'shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # app_item
                'app_item.context_processors.categories',
                'app_item.context_processors.tags',

                # app_cart
                'app_cart.context_processors.get_cart',
                'app_cart.context_processors.in_cart',

                # app_order
                'app_order.context_processors.customer_order_list',
                'app_order.context_processors.seller_order_list',

                # app_settings
                'app_settings.context_processors.load_settings',
            ],
            'libraries': {

            }
        },
    },
]
# THUMBNAIL_ALIASES = {
#     'app_user.Profile.avatar': {
#         'avatar': {'size': (50, 50), 'crop': True},
#     },
# }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

WSGI_APPLICATION = 'shop.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'HOST': 'database',
#         'NAME': 'postgres',
#         'USER': 'postgresUSER',
#         'PASSWORD': 'postgresPASS',
#         'PORT': 5432,
#     }
# }

# DATABASES = {
#     'default': {
#         'ENGINE':os.getenv('POSTGRES_ENGINE', 'django.db.backends.sqlite3'),
#         'NAME': os.getenv('POSTGRES_DB', os.path.join(BASE_DIR, 'db.sqlite3')),
#         'USER': os.getenv('POSTGRES_USER', 'user'),
#         'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'password'),
#         'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
#         'PORT':os.getenv('POSTGRES_PORT', '5432'),
#
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = '/assets/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'assets'), ]
# STATIC_ROOT = BASE_DIR / "assets"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

FIXTURE_ROOT = os.path.join(BASE_DIR, 'fixtures')
# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGLEVEL = os.getenv("DJANGO_LOGLEVEL", "info").upper()
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(module)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "": {
            "level": LOGLEVEL,
            "handlers": [
                "console",
            ],
        },
    },
})

if DEBUG:
    MIDDLEWARE += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
INSTALLED_APPS += (
    'debug_toolbar',
)
INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

USE_CACHE = True

#
# SESSION_EXPIRE_AT_BROWSER_CLOSE = False
# SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
# SESSION_COOKIE_HTTPONLY = True
# SESSION_COOKIE_AGE = 31536000


# Celery settings
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/1'
# CELERY_BROKER_URL = 'redis://redis:6379/0'
# CELERY_RESULT_BACKEND = 'redis://redis:6379/1'
CELERY_TIMEZONE = 'Europe/Moscow'
# CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
# CELERY_ACCEPT_CONTENT = ['application/json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TASK_TRACK_STARTED = True
# CELERY_TASK_TIME_LIMIT = 30 * 60
