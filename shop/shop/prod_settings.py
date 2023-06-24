import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-hgtz)@6%!&a)!vn^wi#i-3$uxchie4%f#fz+2lnor*5r$2(q2d"
)

DEBUG = os.getenv("DEBUG", "0") == "1"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "0.0.0.0"
] + os.getenv("ALLOWED_HOSTS", "127.0.0.1").split(",")


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'database',
        'NAME': 'postgres',
        'USER': 'postgresUSER',
        'PASSWORD': 'postgresPASS',
        'PORT': 5432,
    }
}

STATIC_URL = '/assets/'
STATIC_ROOT = BASE_DIR / "assets"
