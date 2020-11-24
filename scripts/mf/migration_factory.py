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

    URI_LOGIN = 'prod/login'

    def __init__(self, login_api_url):
        self._username = EnvironmentVariableFetcher.fetch(
            ENV_VAR_MIGRATION_FACTORY_USERNAME, env_var_description='Migration Factory username'
        )
        self._password = EnvironmentVariableFetcher.fetch(
            ENV_VAR_MIGRATION_FACTORY_PASSWORD, env_var_description='Migration Factory password', sensitive=True
        )
        self._login_api_url = login_api_url

    def login(self):
        self._authorization_token = Requester.post(
            url=self._login_api_url,
            uri=self.URI_LOGIN,
            data=json.dumps({'username': self._username, 'password': self._password})
        ).strip('"')

        return self._authorization_token

    def get_authorization_token(self):
        if self._authorization_token is None:
            return self.login()

        return self._authorization_token

    def populate_headers_with_authorization(self, headers):
        if headers is None:
            headers = {}

        return {**headers, **{"Authorization": self.get_authorization_token()}}


class MigrationFactoryRequester:
    """ Allow to make requests against the Migration Factory """

    KEY_LOGIN_API_URL = 'LoginApiUrl'
    KEY_USER_API_URL = 'UserApiUrl'
    KEY_ADMIN_API_URL = 'AdminApiUrl'

    URI_ADMIN_SCHEMA = '/prod/admin/schema/app'

    URI_USER_SERVER_LIST = '/prod/user/servers'
    URI_USER_APP_LIST = '/prod/user/apps'
    URI_USER_WAVE = '/prod/user/waves/{}'
    URI_USER_SERVER = '/prod/user/servers/{}'
    URI_USER_APP = '/prod/user/apps/{}'

    _migration_factory_authenticator = None

    def __init__(self, login_api_url):
        self._migration_factory_authenticator = MigrationFactoryAuthenticator(login_api_url)

    def get(self, url, uri, headers=None):
        return Requester.get(
            uri=uri,
            url=url,
            headers=self._migration_factory_authenticator.populate_headers_with_authorization(headers)
        )

    def put(self, url, uri, headers=None, data=None):
        return Requester.put(
            uri=uri,
            url=url,
            headers=self._migration_factory_authenticator.populate_headers_with_authorization(headers),
            data=data
        )

    def post(self, url, uri, headers=None, data=None):
        return Requester.post(
            uri=uri,
            url=url,
            headers=self._migration_factory_authenticator.populate_headers_with_authorization(headers),
            data=data
        )

    def delete(self, url, uri, headers=None, data=None):
        return Requester.delete(
            uri=uri,
            url=url,
            headers=self._migration_factory_authenticator.populate_headers_with_authorization(headers),
            data=data
        )

    def get_user_server_ids(self, user_api_url, app_id=""):
        server_list = self.get(user_api_url, self.URI_USER_SERVER_LIST)

        _server_selected_list_id = []

        for server in server_list:
            if not app_id:
                if server["app_id"] == app_id:
                    _server_selected_list_id.append(server["server_id"])
            else:
                _server_selected_list_id.append(server["server_id"])

        return _server_selected_list_id
    
    def get_user_app_ids(self, user_api_url, wave_id=""):
        app_list = self.get(user_api_url, self.URI_USER_SERVER_LIST)

        _app_selected_list_id = []

        for app in app_list:
            if not wave_id:
                if server["wave_id"] == wave_id:
                    _app_selected_list_id.append(server["app_id"])
            else:
                _app_selected_list_id.append(server["app_id"])

        return _app_selected_list_id


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
