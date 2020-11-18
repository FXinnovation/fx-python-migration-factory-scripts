#!/usr/bin/env python3

import getpass
import json
import logging
import os
import re
import sys
from pathlib import Path

import boto3
import requests
import yaml

PATH_HOME = os.path.join(str(Path.home()), 'migration')
PATH_TEMPLATE = '/usr/local/share/applications/migration_factory'
PATH_CONFIG = '/etc/migration_factory'

FILE_CSV_WAVE_TEMPLATE = 'migration-intake-form.csv'
FILE_CSV_INIT_WAVE_TEMPLATE = 'migration-intake-form-init.csv'
FILE_DONE_MARKER = '.mf_done'

DIRECTORY_POST_LAUNCH = 'post-launch'

ENV_VAR_AWS_ACCESS_KEY_NAMES = ['MF_AWS_ACCESS_KEY_ID', 'AWS_ACCESS_KEY_ID', 'AWS_ACCESS_KEY']
ENV_VAR_AWS_SECRET_KEY_NAMES = ['MF_AWS_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY', 'AWS_SECRET_KEY']
ENV_VAR_AWS_REGION_NAMES = ['MF_AWS_REGION', 'AWS_REGION']
ENV_VAR_ENDPOINT_CONFIG_FILE = ['MF_ENDPOINT_CONFIG_FILE']
ENV_VAR_DEFAULTS_CONFIG_FILE = ['MF_DEFAULTS_CONFIG_FILE']
ENV_VAR_MIGRATION_FACTORY_USERNAME = ['MF_USERNAME', 'MF_FACTORY_USERNAME', 'MF_MIGRATION_FACTORY_USERNAME']
ENV_VAR_MIGRATION_FACTORY_PASSWORD = ['MF_PASSWORD', 'MF_FACTORY_PASSWORD', 'MF_MIGRATION_FACTORY_PASSWORD']
ENV_VAR_CLOUDENDURE_API_TOKEN = ['MF_CE_API_TOKEN', 'MF_FACTORY_CE_API_TOKEN', 'MF_MIGRATION_FACTORY_CE_API_TOKEN']

DEFAULT_ENV_VAR_ENDPOINT_CONFIG_FILE = os.path.join(PATH_CONFIG, 'endpoints.yml')
DEFAULT_ENV_VAR_DEFAULTS_CONFIG_FILE = os.path.join(PATH_CONFIG, 'defaults.yml')


class DefaultsLoader:
    """ Loads default configuration values for every wave and fetch available environments """

    _defaults = {}
    _available_environments = []

    def load(self, default_config_file, environment):
        with open(default_config_file, 'r') as stream:
            try:
                all_defaults = yaml.safe_load(stream)

                if not environment in all_defaults:
                    raise Exception(
                        'Environment “' + environment + '” does not exists in “' + default_config_file + '”.'
                    )

                self._defaults = all_defaults[environment]

                logging.debug("Defaults:" + str(self._defaults))

                for environment, defaults in all_defaults.items():
                    Utils().check_is_serializable_as_path(string_to_test=environment)
                    self._available_environments.append(environment)

                return self.get()

            except yaml.YAMLError as exception:
                logging.error(exception)

    def get(self):
        return self._defaults

    def get_available_environments(self):
        return self._available_environments


class EndpointsLoader:
    """ Loads endpoints configuration """

    _endpoints = None
    _endpoint_config_file = None

    def __init__(self, endpoint_config_file):
        self._endpoint_config_file = endpoint_config_file

    def load(self):
        with open(self._endpoint_config_file, 'r') as stream:
            try:
                self._endpoints = yaml.safe_load(stream)
                return self._endpoints
            except yaml.YAMLError as exception:
                logging.error(exception)

    def get(self):
        if self._endpoints is None:
            self.load()

        return self._endpoints


class Utils:
    """ Primitive type utilities """

    @staticmethod
    def check_is_serializable_as_path(string_to_test):
        is_serializable_as_path = re.search("^[a-zA-Z0-9_ -]+$", string_to_test)
        if not is_serializable_as_path:
            logging.warning(
                'The string “' + string_to_test + '” will need to be serialized for a path or a filename. It might not be suitable because it contains special characters. Use at your own risk.'
            )
        return bool(is_serializable_as_path)


class EnvironmentVariableFetcher:
    """ Fetch environment variables """

    @staticmethod
    def fetch(self, env_var_names, env_var_description='Env variable', default=False, sensitive=False):
        for env_var_name in env_var_names:
            logging.debug(self.__class__.__name__ + ': Trying to fetch ' + env_var_name + ' environment variable.')

            if env_var_name in os.environ:
                return os.getenv(env_var_name)

        if sensitive is True and default is False:
            return getpass.getpass(env_var_description + ": ")

        if default is not False:
            return default

        return input(env_var_description + ": ")


class MigrationFactoryAuthenticator:
    """ Login to Migration Factory """

    _username = None
    _password = None
    _login_api_url = None
    _authorization_token = None

    def __init__(self, login_api_url):
        self._username = EnvironmentVariableFetcher.fetch(
            ENV_VAR_MIGRATION_FACTORY_USERNAME, env_var_description='Migration Factory username'
        )
        self._password = EnvironmentVariableFetcher.fetch(
            ENV_VAR_MIGRATION_FACTORY_PASSWORD, env_var_description='Migration Factory password', sensitive=True
        )
        self._login_api_url = login_api_url

    def login(self):
        response = requests.post(
            os.path.join(self._login_api_url, 'prod/login'),
            data=json.dumps({'username': self._username, 'password': self._password})
        )
        if response.status_code == 200:
            logging.debug(self.__class__.__name__ + ': Migration Factory Login successful')
            self._authorization_token = str(json.loads(response.text))
            return self._authorization_token
        else:
            logging.error(self.__class__.__name__ + ': Migration Factory Login failed.')
            logging.debug(self.__class__.__name__ + ':' + str(response))
            sys.exit(1)

    def get_authorization_token(self):
        if self._authorization_token is None:
            return self.login()

        return self._authorization_token


class AWSServiceAccessor:
    """ Allows access to AWS API endpoints """

    _environment_variable_fetcher = None
    _aws_access_key = ''
    _aws_secret_access_key = ''
    _aws_region = ''
    _ec2_client = None

    def __init__(self):
        self._aws_access_key = EnvironmentVariableFetcher.fetch(
            ENV_VAR_AWS_ACCESS_KEY_NAMES, 'AWS Access Key ID'
        )
        self._aws_secret_access_key = EnvironmentVariableFetcher.fetch(
            ENV_VAR_AWS_SECRET_KEY_NAMES, 'AWS Access Secret Key', sensitive=True
        )
        self._aws_region = EnvironmentVariableFetcher.fetch(ENV_VAR_AWS_REGION_NAMES, 'AWS Region')

    def get_ec2(self):
        if self._ec2_client is None:
            self._ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=self._aws_access_key,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self._aws_region
            )

        return self._ec2_client


def setup_logging(verbose=False):
    if verbose is True:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    logging.basicConfig(stream=sys.stderr, level=logging_level)


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
