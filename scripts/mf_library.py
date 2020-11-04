#!/usr/bin/env python3

from pathlib import Path
import logging
import sys
import yaml
import os

PATH_HOME=os.path.join(str(Path.home()), 'migration')
PATH_TEMPLATE=os.path.join(PATH_HOME, 'templates')

FILE_CSV_WAVE_TEMPLATE=os.path.join(PATH_TEMPLATE, 'migration-intake-form.csv')
FILE_CSV_INIT_WAVE_TEMPLATE=os.path.join(PATH_TEMPLATE, 'migration-intake-form-init.csv')
FILE_DONE_MARKER='.mf_done'

DIRECTORY_POST_LAUNCH='post-launch'

class DefaultsLoader:
    _defaults = {}
    _logger = None

    def __init__(self, logger):
        self._logger = logger

    def load(self, default_config_file, environment):
        with open(default_config_file, 'r') as stream:
            try:
                all_defaults = yaml.safe_load(stream)
                self._defaults = all_defaults[environment]
                self._logger.error(self._defaults)

                for environment, defaults in all_defaults.items():
                    self._check_is_serializable_as_path(environment)
                    self._environments.append(environment)
            except yaml.YAMLError as exception:
                self._logger.error(exception)

    def get(self):
        return self._defaults

class Logger(logging.getLoggerClass()):
    def __init__(self, verbose=False):
        if verbose is True:
            logging_level = logging.DEBUG
        else:
            logging_level = logging.INFO

        super().__init__()
        super().basicConfig(stream=sys.stderr, level=logging_level)


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
