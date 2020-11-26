#!/usr/bin/env python3

import json
import logging
import os
import sys

import requests

from . import ENV_VAR_MIGRATION_FACTORY_PASSWORD
from . import ENV_VAR_MIGRATION_FACTORY_USERNAME
from .utils import EnvironmentVariableFetcher
from .utils import Requester


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
            logging.getLogger('root').info(self.__class__.__name__ + ': Migration Factory Login successful')
            self._authorization_token = str(json.loads(response.text))
            return self._authorization_token
        else:
            logging.getLogger('root').error(self.__class__.__name__ + ': Migration Factory Login failed.')
            logging.getLogger('root').debug(self.__class__.__name__ + ':' + str(response))
            sys.exit(1)

    def get_authorization_token(self):
        if self._authorization_token is None:
            return self.login()

        return self._authorization_token

    def populate_headers_with_authorization(self, headers):
        return {**headers, **{"Authorization": self.get_authorization_token()}}


class MigrationFactoryRequester:
    """ Allow to make requests against the Migration Factory """

    KEY_LOGIN_API_URL = 'LoginApiUrl'
    KEY_USER_API_URL = 'UserApiUrl'
    KEY_ADMIN_API_URL = 'AdminApiUrl'

    _migration_factory_authenticator = None

    def __init__(self, login_api_url):
        self._migration_factory_authenticator = MigrationFactoryAuthenticator(login_api_url)

    def get(self, url, uri, headers=None):
        return Requester.get(
            url, uri, self._migration_factory_authenticator.populate_headers_with_authorization(headers)
        )

    def put(self, url, uri, headers=None, data=None):
        return Requester.put(
            url, uri, self._migration_factory_authenticator.populate_headers_with_authorization(headers), data
        )

    def post(self, url, uri, headers=None, data=None):
        return Requester.post(
            url, uri, self._migration_factory_authenticator.populate_headers_with_authorization(headers), data
        )


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
