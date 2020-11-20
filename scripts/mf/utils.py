#!/usr/bin/env python3

import getpass
import logging
import os
import re
import sys


class Utils:
    """ Primitive type utilities """

    @staticmethod
    def check_is_serializable_as_path(string_to_test):
        is_serializable_as_path = re.search("^[a-zA-Z0-9_ -]+$", string_to_test)
        if not is_serializable_as_path:
            logging.warning(
                'The string “' + string_to_test +
                '” will need to be serialized for a path or a filename.'
                ' It might not be suitable because it contains special characters.'
                ' Use at your own risk.'
            )
        return bool(is_serializable_as_path)


class EnvironmentVariableFetcher:
    """ Fetch environment variables """

    @staticmethod
    def fetch(env_var_names, env_var_description='Env variable', default=False, sensitive=False):
        for env_var_name in env_var_names:
            logging.debug('EnvironmentVariableFetcher: Trying to fetch ' + env_var_name + ' environment variable.')

            if env_var_name in os.environ:
                return os.getenv(env_var_name)

        if sensitive is True and default is False:
            return getpass.getpass(env_var_description + ": ")

        if default is not False:
            return default

        return input(env_var_description + ": ")


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
