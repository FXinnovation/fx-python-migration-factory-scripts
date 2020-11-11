#!/usr/bin/env python3

from pathlib import Path
import logging
import sys
import yaml
import os
import re
import getpass
import boto3

PATH_HOME=os.path.join(str(Path.home()), 'migration')
PATH_TEMPLATE=os.path.join(PATH_HOME, 'templates')

FILE_CSV_WAVE_TEMPLATE=os.path.join(PATH_TEMPLATE, 'migration-intake-form.csv')
FILE_CSV_INIT_WAVE_TEMPLATE=os.path.join(PATH_TEMPLATE, 'migration-intake-form-init.csv')
FILE_DONE_MARKER='.mf_done'

DIRECTORY_POST_LAUNCH='post-launch'

ENV_VAR_AWS_ACCESS_KEY_NAMES=['MF_AWS_ACCESS_KEY_ID', 'AWS_ACCESS_KEY_ID', 'AWS_ACCESS_KEY']
ENV_VAR_AWS_SECRET_KEY_NAMES=['MF_AWS_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY', 'AWS_SECRET_KEY']
ENV_VAR_AWS_REGION_NAMES=['MF_AWS_REGION', 'AWS_REGION']

class DefaultsLoader:
    """ Loads default configuration values for every wave and fetch available environments """

    _defaults = {}
    _available_environments = []

    def load(self, default_config_file, environment):
        with open(default_config_file, 'r') as stream:
            try:
                all_defaults = yaml.safe_load(stream)

                if not environment in all_defaults:
                    raise Exception('Environment “'+ environment +'” does not exists in “'+ default_config_file +'”.')

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

    def getAvailableEnvironments(self):
        return self._available_environments

class Utils:
    """ Primitive type utilities """

    def check_is_serializable_as_path(self, string_to_test):
        is_serializable_as_path = re.search("^[a-zA-Z0-9_ -]+$", string_to_test)
        if not is_serializable_as_path:
            logging.warning('The string “'+string_to_test+'” will need to be serialized for a path or a filename. It might not be suitable because it contains special characters. Use at your own risk.')
        return bool(is_serializable_as_path)


class EnvironmentVariableFetcher():
    """ Fetch environment variables """

    def fetch(self, env_var_names, env_var_description, sensitive=False):
        for env_var_name in env_var_names:
            logging.debug('EnvironmentVariableFetcher: Trying to fetch '+ env_var_name +' environment variable.')

            if env_var_name in os.environ:
                return os.getenv(env_var_name)

        if sensitive is True:
            return getpass.getpass(env_var_description + ": ")

        return input(env_var_description + ": ")

class AWSServiceAccessor():
    """ Login to AWS """

    _environment_variable_fetcher = None
    _aws_access_key = ''
    _aws_secret_access_key = ''
    _aws_region = ''
    _ec2_client = None

    def __init__(self):
        self._environment_variable_fetcher = EnvironmentVariableFetcher()
        self._aws_access_key = self._environment_variable_fetcher.fetch(ENV_VAR_AWS_ACCESS_KEY_NAMES, 'AWS Access Key ID')
        self._aws_secret_access_key = self._environment_variable_fetcher.fetch(ENV_VAR_AWS_SECRET_KEY_NAMES, 'AWS Access Secret Key', sensitive=True)
        self._aws_region = self._environment_variable_fetcher.fetch(ENV_VAR_AWS_REGION_NAMES, 'AWS Region')


    def get_ec2(self):
        if self._ec2_client is None:
            self._ec2_client = boto3.client('ec2', aws_access_key_id=self._aws_access_key, aws_secret_access_key=self._aws_secret_access_key, region_name=self._aws_region)

        return self._ec2_client


def setup_logging(verbose=False):
    if verbose is True:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    logging.basicConfig(stream=sys.stderr, level=logging_level)


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
