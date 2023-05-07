from django.apps import AppConfig
import logging


class ApiKeysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_keys'


logger = logging.getLogger('api_keys')
