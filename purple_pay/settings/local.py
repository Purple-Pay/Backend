from purple_pay.settings.base import *
import os
import datetime
from purple_pay.logger_config import LOGGING_SETTING


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ej@$x2f*r@0@22p*qp=c@v((j@luis=(3b1c6&jt_&=2y2ys%)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['*']
CORS_ORIGIN_ALLOW_ALL = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'purplepaydb',
        'USER': 'legittdotme',
        'PASSWORD': 'Leg!ttdotm3',
        'HOST': 'localhost',
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

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587    # GMAIL
EMAIL_HOST_USER = 'letstalk@purplepay.app'
EMAIL_HOST_PASSWORD = 'crwgagtuondtjnrq'
DEFAULT_FROM_EMAIL = 'letstalk@purplepay.app'
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True

DATA_UPLOAD_MAX_MEMORY_SIZE = 15728640  # 15 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 15728640  # 15 MB

LOGGING = LOGGING_SETTING

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'