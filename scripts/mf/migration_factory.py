#!/usr/bin/env python3

import json
import logging
import re

from . import ENV_VAR_MIGRATION_FACTORY_PASSWORD
from . import ENV_VAR_MIGRATION_FACTORY_USERNAME
from .utils import EnvironmentVariableFetcher
from .utils import Requester
import requests_cache


class CSVIntake:
    """ Data object to represent intake CSV """

    WAVE_NAME = 'wave_name'
    APP_NAME = 'app_name'
    CLOUDENDURE_PROJECT_NAME = 'cloudendure_projectname'
    AWS_ACCOUNT_ID = 'aws_accountid'
    SERVER_NAME = 'server_name'
    SERVER_OS = 'server_os'
    SERVER_OS_VERSION = 'server_os_version'
    SERVER_FQDN = 'server_fqdn'
    SERVER_TIER = 'server_tier'
    SERVER_ENVIRONMENT = 'server_environment'
    SUBNET_ID = 'subnet_id'
    SECURITY_GROUP_ID = 'securitygroup_ids'
    SUBNET_ID_TEST = 'subnet_id_test'
    SECURITY_GROUP_ID_TEST = 'securitygroup_ids_test'
    INSTANCE_TYPE = 'instance_type'
    TENANCY = 'tenancy'
    IAM_ROLE = 'iam_role'

    MF_WAVE_NAME = 'wave_id'
    MF_APP_NAME = 'app_name'
    MF_CLOUDENDURE_PROJECT_NAME = 'cloudendure_projectname'
    MF_AWS_ACCOUNT_ID = 'aws_accountid'
    MF_SERVER_NAME = 'server_name'
    MF_SERVER_OS = 'server_os'
    MF_SERVER_OS_VERSION = 'server_os_version'
    MF_SERVER_FQDN = 'server_fqdn'
    MF_SERVER_TIER = 'server_tier'
    MF_SERVER_ENVIRONMENT = 'server_environment'
    MF_SUBNET_ID = 'subnet_IDs'
    MF_SECURITY_GROUP_ID = 'securitygroup_IDs'
    MF_SUBNET_ID_TEST = 'subnet_IDs_test'
    MF_SECURITY_GROUP_ID_TEST = 'securitygroup_IDs_test'
    MF_INSTANCE_TYPE = 'instanceType'
    MF_TENANCY = 'tenancy'
    MF_IAM_ROLE = 'iamRole'

    ALL_FIELDS = {
        WAVE_NAME: MF_WAVE_NAME,
        APP_NAME: MF_APP_NAME,
        CLOUDENDURE_PROJECT_NAME: MF_CLOUDENDURE_PROJECT_NAME,
        AWS_ACCOUNT_ID: MF_AWS_ACCOUNT_ID,
        SERVER_NAME: MF_SERVER_NAME,
        SERVER_OS: MF_SERVER_OS,
        SERVER_OS_VERSION: MF_SERVER_OS_VERSION,
        SERVER_FQDN: MF_SERVER_FQDN,
        SERVER_TIER: MF_SERVER_TIER,
        SERVER_ENVIRONMENT: MF_SERVER_ENVIRONMENT,
        SUBNET_ID: MF_SUBNET_ID,
        SECURITY_GROUP_ID: MF_SECURITY_GROUP_ID,
        SUBNET_ID_TEST: MF_SUBNET_ID_TEST,
        SECURITY_GROUP_ID_TEST: MF_SECURITY_GROUP_ID_TEST,
        INSTANCE_TYPE: MF_INSTANCE_TYPE,
        TENANCY: MF_TENANCY,
        IAM_ROLE: MF_IAM_ROLE,
    }


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
        requests_cache.install_cache('migration_factory', backend='memory', expire_after=30)

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

    URI_ADMIN_SCHEMA = '/prod/admin/schema/app'

    URI_USER_SERVER_LIST = '/prod/user/servers'
    URI_USER_SERVER = '/prod/user/servers/{}'
    URI_USER_APP_LIST = '/prod/user/apps'
    URI_USER_APP = '/prod/user/apps/{}'
    URI_USER_WAVE = '/prod/user/waves/{}'
    URI_USER_WAVE_LIST = '/prod/user/waves'

    _migration_factory_authenticator = None
    _endpoints_loader = None

    def __init__(self, endpoints_loader):
        self._migration_factory_authenticator = MigrationFactoryAuthenticator(endpoints_loader.get_login_api_url())
        self._endpoints_loader = endpoints_loader

    def get(self, uri, url=None, headers=None, response_type=Requester.RESPONSE_TYPE_JSON):
        if url is None:
            print('URL IS NONE')
            url = self._guess_url(uri)

        print(url)

        return Requester.get(
            uri=uri,
            url=url,
            headers=self._migration_factory_authenticator.populate_headers_with_authorization(headers),
            response_type=response_type,
        )

    def put(self, uri, url=None, headers=None, data=None, response_type=Requester.RESPONSE_TYPE_JSON):
        if url is None:
            url = self._guess_url(uri)

        return Requester.put(
            uri=uri,
            url=url,
            headers=self._migration_factory_authenticator.populate_headers_with_authorization(headers),
            data=data,
            response_type=response_type,
        )

    def post(self, uri, url=None, headers=None, data=None, response_type=Requester.RESPONSE_TYPE_JSON):
        if url is None:
            url = self._guess_url(uri)

        return Requester.post(
            uri=uri,
            url=url,
            headers=self._migration_factory_authenticator.populate_headers_with_authorization(headers),
            data=data,
            response_type=response_type,
        )

    def delete(self, uri, url=None, headers=None, response_type=Requester.RESPONSE_TYPE_JSON):
        if url is None:
            url = self._guess_url(uri)

        return Requester.delete(
            uri=uri,
            url=url,
            headers=self._migration_factory_authenticator.populate_headers_with_authorization(headers),
            response_type=response_type,
        )

    def get_user_app_by_name(self, app_name=None):
        all_apps = self.get(uri=self.URI_USER_APP_LIST)

        for app in all_apps:
            if app['app_name'] == app_name:
                return app

        return None

    def get_user_server_ids(self, filter_app_id=None):
        _server_list = self.get(self.URI_USER_SERVER_LIST)

        _server_selected_list_id = []

        for server in _server_list:
            if filter_app_id:
                if "app_id" in server and server["app_id"] == filter_app_id:
                    _server_selected_list_id.append(server["server_id"])
                else:
                    logging.getLogger('root').debug('{}: server id “{}” filtered (not in app {})'.format(
                        self.__class__.__name__, server["server_id"], filter_app_id
                    ))
            else:
                _server_selected_list_id.append(server["server_id"])

        return _server_selected_list_id

    def get_user_app_ids(self, filter_wave_id=None):
        _app_list = self.get(self.URI_USER_APP_LIST)

        _app_selected_list_id = []

        for app in _app_list:
            if filter_wave_id:
                if "wave_id" in app and app["wave_id"] == filter_wave_id:
                    _app_selected_list_id.append(app["app_id"])
                else:
                    logging.getLogger('root').debug('{}: app id “{}” filtered (not in wave {})'.format(
                        self.__class__.__name__, app["app_id"], filter_wave_id
                    ))
            else:
                _app_selected_list_id.append(app["app_id"])

        return _app_selected_list_id

    def _guess_url(self, uri):
        if self._has_user_uri(uri):
            return self._endpoints_loader.get_user_api_url()
        if self._has_admin_uri(uri):
            return self._endpoints_loader.get_admin_api_url()
        if self._has_login_uri(uri):
            return self._endpoints_loader.get_login_api_url()

        return self._endpoints_loader.get_tools_api_url

    @classmethod
    def _has_user_uri(cls, uri):
        return re.match('/user/', uri)

    @classmethod
    def _has_admin_uri(cls, uri):
        return re.match('/admin/', uri)

    @classmethod
    def _has_login_uri(cls, uri):
        return re.match('/login', uri)


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
