#!/usr/bin/env python3

from pathlib import Path
import logging
import sys
import yaml
import os
import re

PATH_HOME=os.path.join(str(Path.home()), 'migration')
PATH_TEMPLATE=os.path.join(PATH_HOME, 'templates')

FILE_CSV_WAVE_TEMPLATE=os.path.join(PATH_TEMPLATE, 'migration-intake-form.csv')
FILE_CSV_INIT_WAVE_TEMPLATE=os.path.join(PATH_TEMPLATE, 'migration-intake-form-init.csv')
FILE_DONE_MARKER='.mf_done'

DIRECTORY_POST_LAUNCH='post-launch'

class DefaultsLoader:
    """ Loads default configuration values for every wave and fetch available environments """

    _defaults = {}
    _available_environments = []

    def load(self, default_config_file, environment):
        with open(default_config_file, 'r') as stream:
            try:
                all_defaults = yaml.safe_load(stream)
                self._defaults = all_defaults[environment]
                logging.debug(self._defaults)

                for environment, defaults in all_defaults.items():
                    Utils().check_is_serializable_as_path(string_to_test=environment)
                    self._available_environments.append(environment)
            except yaml.YAMLError as exception:
                logging.error(exception)

    def get(self):
        return self._defaults

    def getAvailableEnvironments(self):
        return self._available_environments

class Utils:
    """ Primitive type utilities """

    def check_is_serializable_as_path(self, string_to_test):
        is_serializable_as_path = re.search("^[a-zA-Z0-9_-]+$", string_to_test)
        if not is_serializable_as_path:
            logging.warning('The string “'+string_to_test+'” will need to be serialized for a path or a filename. It might not be suitable because it contains special characters. Use at your own risk.')
        return bool(is_serializable_as_path)


def setup_logging(verbose=False):
    if verbose is True:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    logging.basicConfig(stream=sys.stderr, level=logging_level)


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
