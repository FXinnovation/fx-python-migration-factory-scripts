#!/usr/bin/env python3

import getpass
import json
import logging
import os
import re
import sys

import requests


class Utils:
    """ Primitive type utilities """

    @staticmethod
    def check_is_serializable_as_path(string_to_test):
        is_serializable_as_path = re.search("^[a-zA-Z0-9_ -]+$", string_to_test)
        if not is_serializable_as_path:
            logging.getLogger('root').warning(
                'The string “' + string_to_test +
                '” will need to be serialized for a path or a filename.'
                ' It might not be suitable because it contains special characters.'
                ' Use at your own risk.'
            )
        return bool(is_serializable_as_path)


class Requester:
    """ Decorator around requests for enhanced logging """

    @classmethod
    def get(cls, uri, url=None, headers=None, data=None, request_instance=requests, exit_on_error=True):
        return Requester._do_request(request_instance, 'get', url, uri, headers, data, [200], exit_on_error)

    @classmethod
    def post(cls, uri, url=None, headers=None, data=None, request_instance=requests, exit_on_error=True):
        return Requester._do_request(request_instance, 'post', url, uri, headers, data, [201], exit_on_error)

    @classmethod
    def put(cls, uri, url=None, headers=None, data=None, request_instance=requests, exit_on_error=True):
        return Requester._do_request(request_instance, 'put', url, uri, headers, data, [200, 201], exit_on_error)

    @classmethod
    def patch(cls, uri, url=None, headers=None, data=None, request_instance=requests, exit_on_error=True):
        return Requester._do_request(request_instance, 'put', url, uri, headers, data, [200], exit_on_error)

    @classmethod
    def _do_request(cls, request_instance, verb, url, uri, headers, data, expected_codes, exit_on_error):
        if headers is None:
            headers = {}
        if data is None:
            headers = {}
        if url is None:
            url = ''

        logging.getLogger('root').debug("{}: Using “{}” as requests instance for {} “{}”".format(
            cls.__class__.__name__, verb.upper(), type(request_instance), url, uri
        ))

        response = getattr(request_instance, verb.lower())(
            url=url + uri,
            headers=headers,
            data=data
        )

        logging.getLogger('root').info('{}: {} “{}” “{}” (code: “{}”)'.format(
            cls.__class__.__name__, verb.upper(), url, uri, str(response.status_code)
        ))
        logging.getLogger('root').debug("{}: {} “{}” “{}” (code: “{}”). Content:\n{}\n".format(
            cls.__class__.__name__, verb.upper(), url, uri, str(response.status_code), str(response.content)
        ))

        if response.status_code not in expected_codes:
            logging.getLogger('root').error("{}: {} “{}” “{}” (code: “{}”). Content:\n{}\n".format(
                cls.__class__.__name__, verb.upper(), url, uri, str(response.status_code), str(response.content)
            ))
            if exit_on_error:
                sys.exit(50)

        return json.loads(response.content)


class EnvironmentVariableFetcher:
    """ Fetch environment variables """

    @staticmethod
    def fetch(env_var_names, env_var_description='Env variable', default=None, sensitive=False):
        for env_var_name in env_var_names:
            logging.getLogger('root').debug(
                'EnvironmentVariableFetcher: Trying to fetch ' + env_var_name + ' environment variable.'
            )

            if env_var_name in os.environ:
                return os.getenv(env_var_name)

        if default is not None:
            return default

        if sensitive is True:
            return getpass.getpass(env_var_description + ": ")

        return input(env_var_description + ": ")


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
