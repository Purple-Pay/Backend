from django.apps import AppConfig
import logging


class PaymentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'


logger = logging.getLogger('payments')