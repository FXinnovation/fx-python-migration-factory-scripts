import os
from pathlib import Path

PATH_HOME = os.path.join(str(Path.home()), 'migration')
PATH_TEMPLATE = '/usr/local/share/applications/migration_factory'
PATH_CONFIG = '/etc/migration_factory'

ENV_VAR_AWS_ACCESS_KEY_NAMES = ['MF_AWS_ACCESS_KEY_ID', 'AWS_ACCESS_KEY_ID', 'AWS_ACCESS_KEY']
ENV_VAR_AWS_SECRET_KEY_NAMES = ['MF_AWS_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY', 'AWS_SECRET_KEY']
ENV_VAR_AWS_REGION_NAMES = ['MF_AWS_REGION', 'AWS_REGION']
ENV_VAR_ENDPOINT_CONFIG_FILE = ['MF_ENDPOINT_CONFIG_FILE']
ENV_VAR_DEFAULTS_CONFIG_FILE = ['MF_DEFAULTS_CONFIG_FILE']
ENV_VAR_MIGRATION_FACTORY_USERNAME = ['MF_USERNAME', 'MF_FACTORY_USERNAME', 'MF_MIGRATION_FACTORY_USERNAME']
ENV_VAR_MIGRATION_FACTORY_PASSWORD = ['MF_PASSWORD', 'MF_FACTORY_PASSWORD', 'MF_MIGRATION_FACTORY_PASSWORD']
ENV_VAR_CLOUDENDURE_TOKEN = [
    'MF_CE_API_TOKEN', 'MF_CE_TOKEN', 'MF_CLOUDENDURE_TOKEN', 'MF_CLOUDENDURE_API_TOKEN', 'CE_API_TOKEN'
]

FILE_CSV_WAVE_TEMPLATE = 'migration-intake-form.csv'
FILE_CSV_TAG = 'migration-tags.csv'
FILE_MARKER_PREPARE_DONE = '.mf_prepare_done'

DIRECTORY_POST_LAUNCH = 'post-launch'

DEFAULT_ENV_VAR_ENDPOINT_CONFIG_FILE = os.path.join(PATH_CONFIG, 'endpoints.yml')
DEFAULT_ENV_VAR_DEFAULTS_CONFIG_FILE = os.path.join(PATH_CONFIG, 'defaults.yml')


def setup_logging(logging, info=False, debug=False):
    if debug is True:
        logging_level = logging.DEBUG
    elif info is True:
        logging_level = logging.INFO
    else:
        logging_level = logging.WARNING

    logger = logging.getLogger('root')
    logger.setLevel(logging_level)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging_level)
    formatter = logging.Formatter("## [%(levelname)s]: %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
