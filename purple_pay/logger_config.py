from datetime import datetime
import os

BASE_DIR_LOGGER = "/var/log/purple_pay/"
#BASE_DIR_LOGGER = "/Users/alexratna/Desktop/test/purplepay_logger/"
LOGGER_WHEN = 'H'
LOGGER_INTERVAL = 24
LOGGER_BACKUPCOUNT = 15
APP_ADD_LOGGER = ['django', 'api_keys', 'authentication', 'commons', 'kyc', 'payments',
                  'user_profile']


def get_dir(app_name):
    base_dir = BASE_DIR_LOGGER
    log_dir = base_dir + app_name + '/'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    return log_dir + app_name + '_logs.log'


def create_logger(prev_log_setting, app_name):
    app_handler = app_name + '_handler'
    if app_handler not in prev_log_setting['handlers']:
        prev_log_setting['handlers'][app_handler] = {'level': 'INFO',
                                                     'class': 'logging.handlers.TimedRotatingFileHandler',
                                                     'filename': get_dir(app_name),
                                                     'when': LOGGER_WHEN,  # this specifies the interval
                                                     'interval': LOGGER_INTERVAL,
                                                     # defaults to 24, only necessary for other values
                                                     'backupCount': LOGGER_BACKUPCOUNT,
                                                     # how many backup file to keep, 15 days
                                                     'formatter': 'verbose'}
    if app_name not in prev_log_setting['loggers']:
        prev_log_setting['loggers'][app_name] = {
            'handlers': [app_handler, 'console'],
            'level': 'INFO',
        }
    return prev_log_setting


LOGGING_SETTING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        }},
    'loggers': {},
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message} {pathname}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message} {pathname}',
            'style': '{',
        },
    },
}

for app in APP_ADD_LOGGER:
    LOGGING_SETTING = create_logger(LOGGING_SETTING, app)
