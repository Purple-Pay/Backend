from purple_pay.settings.base import *
import os
import datetime
from purple_pay.logger_config import LOGGING_SETTING


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = ['*']
CORS_ORIGIN_ALLOW_ALL = True

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DJANGO_DB_ENGINE'),
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': '5432',
    }
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(days=120),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=240),
}

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND')
# EMAIL_HOST = 'smtp.gmail.com'    # GMAIL
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = 587    # GMAIL
# EMAIL_PORT = 465    # SSL Port
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True

DATA_UPLOAD_MAX_MEMORY_SIZE = 15728640  # 15 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 15728640  # 15 MB

LOGGING = LOGGING_SETTING

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'