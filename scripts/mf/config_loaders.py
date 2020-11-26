#!/usr/bin/env python3

import logging
import os
from collections.abc import MutableMapping

import yaml

from . import PATH_CONFIG
from .utils import Utils

DEFAULT_ENV_VAR_ENDPOINT_CONFIG_FILE = os.path.join(PATH_CONFIG, 'endpoints.yml')
DEFAULT_ENV_VAR_DEFAULTS_CONFIG_FILE = os.path.join(PATH_CONFIG, 'defaults.yml')


class DefaultValues(MutableMapping):
    """ Stores default values in memory """

    def __init__(self, *args, **kwargs):
        self._store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self._store[key] = value

    def __delitem__(self, key):
        del self._store[key]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __str__(self):
        return str(self._store)

    def get(self, key, default=None):
        if default is None:
            default = ''

        if key not in self._store.keys() or self._store[key] is None:
            logging.debug(self.__class__.__name__ + ':Key “' + key + '” not found. Return default:“' + default + '”')
            return default

        return self._store[key]


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

                self._defaults = DefaultValues(all_defaults[environment])

                logging.debug(self.__class__.__name__ + ':Defaults:' + str(self._defaults))

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
