#!/usr/bin/env python3

import logging
import os

import yaml

from . import PATH_CONFIG
from .utils import Utils

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

                if environment not in all_defaults:
                    raise Exception(
                        'Environment “' + environment + '” does not exists in “' + default_config_file + '”.'
                    )

                self._defaults = all_defaults[environment]

                logging.debug("Defaults:" + str(self._defaults))

                for environment, defaults in all_defaults.items():
                    Utils.check_is_serializable_as_path(string_to_test=environment)
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


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
