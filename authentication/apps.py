from django.apps import AppConfig
import logging


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'


logger = logging.getLogger('authentication')
