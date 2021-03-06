#!/usr/bin/env python3
import csv
import getpass
import json
import logging
import os
import re
import subprocess
import sys
from typing import List

import requests


class MessageBag:
    """ Bag of messages """

    ALLOWED_TYPES = ['error', 'warning', 'info', 'debug']

    _bag: List[str] = []
    _type: str = None

    def __init__(self, type_of_bag: str):
        if type_of_bag not in self.ALLOWED_TYPES:
            logging.error('{}: “{}” is not a valid MessageBag type (allowed: “{}”)'.format(
                self.__class__.__name__, type, self.ALLOWED_TYPES
            ))
            sys.exit(1)

        self._type = type_of_bag

    def add(self, element: str):
        self._bag.append(element)

    def unload(self, logger=logging):
        if not self.is_empty():
            print('')

        for element in self._bag:
            getattr(logger, self._type)(element)

    def is_empty(self):
        return len(self._bag) == 0


class Utils:
    """ Primitive type utilities """

    @staticmethod
    def check_is_serializable_as_path(string_to_test: str):
        is_serializable_as_path = re.search("^[a-zA-Z0-9_ -]+$", string_to_test)
        if not is_serializable_as_path:
            logging.getLogger('root').warning(
                'The string “' + string_to_test +
                '” will need to be serialized for a path or a filename.'
                ' It might not be suitable because it contains special characters.'
                ' Use at your own risk.'
            )
        return bool(is_serializable_as_path)

    @classmethod
    def csv_to_dicts(cls, csv_path: str):
        content = []
        with open(csv_path, newline='\n') as csv_content:
            reader = csv.DictReader(csv_content)
            for row in reader:
                content.append(row)

            logging.getLogger('root').debug("{}: CSV content\n{}".format(
                cls.__class__.__name__, csv_content
            ))

        return content

    @classmethod
    def write_csv_with_headers(cls, csv_path: str, csv_content: dict):
        with open(csv_path, 'a') as csv_file:
            if not csv_content:
                logging.getLogger('root').error("{}: CSV content argument can't be empty \n{}".format(
                    cls.__class__.__name__, csv_content
                ))
            writer = csv.DictWriter(csv_file, fieldnames=csv_content[0].keys())
            writer.writeheader()
            for row in csv_content:
                writer.writerow(row)
        logging.getLogger('root').debug("{}: CSV content\n{}".format(
            cls.__class__.__name__, csv_content
        ))


class Requester:
    """ Decorator around requests for enhanced logging """

    RESPONSE_TYPE_TEXT = 'text'
    RESPONSE_TYPE_RAW = 'raw'
    RESPONSE_TYPE_JSON = 'json'

    @classmethod
    def get(cls, uri, url=None, headers=None, data=None, request_instance=requests, exit_on_error=True,
            response_type=RESPONSE_TYPE_JSON):
        return Requester._do_request(request_instance, 'get', url, uri, headers, data, [200], exit_on_error,
                                     response_type)

    @classmethod
    def post(cls, uri, url=None, headers=None, data=None, request_instance=requests, exit_on_error=True,
             response_type=RESPONSE_TYPE_JSON):
        return Requester._do_request(request_instance, 'post', url, uri, headers, data, [200, 201], exit_on_error,
                                     response_type)

    @classmethod
    def put(cls, uri, url=None, headers=None, data=None, request_instance=requests, exit_on_error=True,
            response_type=RESPONSE_TYPE_JSON):
        return Requester._do_request(request_instance, 'put', url, uri, headers, data, [200, 201], exit_on_error,
                                     response_type)

    @classmethod
    def patch(cls, uri, url=None, headers=None, data=None, request_instance=requests, exit_on_error=True,
              response_type=RESPONSE_TYPE_JSON):
        return Requester._do_request(request_instance, 'patch', url, uri, headers, data, [200], exit_on_error,
                                     response_type)

    @classmethod
    def delete(cls, uri, url=None, headers=None, data=None, request_instance=requests, exit_on_error=True,
               response_type=RESPONSE_TYPE_JSON):
        return Requester._do_request(request_instance, 'delete', url, uri, headers, data, [200, 204], exit_on_error,
                                     response_type)

    @classmethod
    def _do_request(cls, request_instance, verb, url, uri, headers, data, expected_codes, exit_on_error, response_type):
        if headers is None:
            headers = {}
        if data is None:
            data = {}
        if url is None:
            url = ''
        else:
            url = url.rstrip('/') + '/'

        uri = uri.lstrip('/')

        logging.getLogger('root').debug("{}: Using “{}” as requests instance for {} “{}”".format(
            cls.__class__.__name__, type(request_instance), url, uri
        ))

        response = getattr(request_instance, verb.lower())(
            url=url + uri,
            headers=headers,
            data=data
        )

        logging.getLogger('root').info('{}: {} “{}” “{}” (code: “{}”)'.format(
            cls.__class__.__name__, verb.upper(), url, uri, str(response.status_code)
        ))
        logging.getLogger('root').debug(
            "{}: {} “{}” “{}” (code: “{}”). Cached: {}\nSent data:\n{}\nSent headers:\n{}\nResponse:\n{}\n".format(
                cls.__class__.__name__,
                verb.upper(),
                url,
                uri,
                str(response.status_code),
                str(response.from_cache),
                str(data),
                str(headers),
                str(response.content)
            )
        )

        if response.status_code not in expected_codes:
            logging.getLogger('root').error(
                "{}: {} “{}” “{}” (code: “{}”). Sent data:\n{}\nResponse:\n{}\n".format(
                    cls.__class__.__name__,
                    verb.upper(),
                    url,
                    uri,
                    str(response.status_code),
                    str(data),
                    str(response.content)
                )
            )
            if exit_on_error:
                sys.exit(50)

        if response_type == cls.RESPONSE_TYPE_RAW:
            return response.content

        if response_type == cls.RESPONSE_TYPE_TEXT:
            return response.text

        return json.loads(response.content or 'null')


class EnvironmentVariableFetcher:
    """ Fetch environment variables """

    @staticmethod
    def fetch(env_var_names, env_var_description='Env variable', default=None, sensitive=False, default_is_none=False):
        for env_var_name in env_var_names:
            logging.getLogger('root').debug(
                'EnvironmentVariableFetcher: Trying to fetch ' + env_var_name + ' environment variable.'
            )

            if env_var_name in os.environ:
                return os.getenv(env_var_name)

        if default is not None:
            return default

        if default_is_none:
            return None

        if sensitive is True:
            return getpass.getpass(env_var_description + ": ")

        return input(env_var_description + ": ")


class UserManualConfirmation:
    """ Prompt user to confirm an action"""

    @staticmethod
    def ask(message: str, confirmation_text: str = 'Y') -> bool:
        return input(message + " (type “" + confirmation_text + "” to confirm)\n") == confirmation_text


class PowershellRunner:
    """ Runs powershell commands with pwsh """

    @classmethod
    def run(cls, command: str):
        process = subprocess.Popen(["pwsh", "-Command", command], stdout=sys.stdout)
        return process.communicate()

    @classmethod
    def authenticate_command(cls, command: str, user: str, password: str) -> str:
        return cls.insert_authenthication_arguments(command + ' %s', user, password)

    @classmethod
    def insert_authenthication_arguments(cls, command_with_percentage: str, user: str, password: str) -> str:
        _credential_string = "-Credential (New-Object System.Management.Automation.PSCredential('{}'," \
                             " (ConvertTo-SecureString '{}' -AsPlainText -Force))) -Authentication Negotiate".format(
                                 user, password
                             )

        return command_with_percentage % _credential_string


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
