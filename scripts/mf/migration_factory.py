#!/usr/bin/env python3

import json
import logging
import re

import requests_cache

from mf.aws import AWSValidator
from . import ENV_VAR_MIGRATION_FACTORY_PASSWORD
from . import ENV_VAR_MIGRATION_FACTORY_USERNAME
from .utils import EnvironmentVariableFetcher, MessageBag
from .utils import Requester


class MfField:
    """ Data object to represent Migration Factory Fields """

    WAVE_NAME = 'wave_name'
    WAVE_ID = 'wave_id'
    WAVE_DESCRIPTION = 'Description'
    APP_NAME = 'app_name'
    APP_ID = 'app_id'
    CLOUDENDURE_PROJECT_NAME = 'cloudendure_projectname'
    AWS_ACCOUNT_ID = 'aws_accountid'
    SERVER_NAME = 'server_name'
    SERVER_ID = 'server_id'
    SERVER_OS = 'server_os'
    SERVER_OS_VERSION = 'server_os_version'
    SERVER_FQDN = 'server_fqdn'
    SERVER_TIER = 'server_tier'
    SERVER_ENVIRONMENT = 'server_environment'
    SUBNET_ID = 'subnet_IDs'
    SECURITY_GROUP_ID = 'securitygroup_IDs'
    SUBNET_ID_TEST = 'subnet_IDs_test'
    SECURITY_GROUP_ID_TEST = 'securitygroup_IDs_test'
    INSTANCE_TYPE = 'instanceType'
    TENANCY = 'tenancy'
    IAM_ROLE = 'iamRole'


class MigrationFactoryData:
    """ Data object representing any data in Migration Factory (superclass) """

    FIELDS = {}
    PUT_FIELDS = {}

    _data = {}
    _id = None

    def __init__(self, data: dict, identifier: int = None):
        self.fill(data, identifier)

    def fill(self, data: dict, identifier: int = None):
        for key in self.FIELDS:
            if key not in data.keys():
                self._data[key] = ''
            else:
                self._data[key] = data[key]

        if identifier is not None:
            self.set_id(identifier)

    def to_dict(self, layer: dict = None):
        self.update_data()

        if layer is None:
            layer = self.FIELDS

        temp_data = {}
        for key in layer:
            temp_data[key] = str(self._data[key])

        return temp_data

    def to_post_payload(self):
        return json.dumps(self.to_dict())

    def to_put_payload(self):
        return json.dumps(self.to_dict(self.PUT_FIELDS))

    def get_id(self):
        return self._id

    def set_id(self, identifier: int):
        self._id = identifier

    def get(self, key: str):
        return self._data[key]

    def is_filled(self):
        return self.get_id() is not None

    def update_data(self):
        pass


class Wave(MigrationFactoryData):
    """ Data object representing a wave in Migration Factory """

    FIELDS = {
        MfField.WAVE_NAME,
        MfField.WAVE_DESCRIPTION,
    }

    _data = {}
    _id = None

    def __init__(self, data: dict = None, identifier: int = None):
        if data is None:
            data = {}

        super().__init__(data=data, identifier=identifier)

    def __str__(self):
        return self._data[MfField.WAVE_ID]


class App(MigrationFactoryData):
    """ Data object representing a app in Migration Factory """

    FIELDS = {
        MfField.WAVE_ID,
        MfField.APP_NAME,
        MfField.CLOUDENDURE_PROJECT_NAME,
        MfField.AWS_ACCOUNT_ID,
    }

    _wave = None
    _data = {}
    _id = None

    def __init__(self, data: dict = None, identifier: int = None, wave: Wave = Wave()):
        if data is None:
            data = {}

        super().__init__(data=data, identifier=identifier)
        self.set_wave(wave)

    def __str__(self):
        return self._data[MfField.APP_ID]

    def set_wave(self, wave: Wave):
        self._wave = wave
        self.update_data()

    def get_wave(self):
        return self._wave

    def is_filled(self):
        return super().is_filled() and self.get_wave().is_filled()

    def update_data(self):
        if self.get_wave() and self.get_wave().get_id():
            self._data[MfField.WAVE_ID] = self.get_wave().get_id()


class Server(MigrationFactoryData):
    """ Data object representing a server in Migration Factory """

    FIELDS = {
        MfField.APP_ID,
        MfField.SERVER_NAME,
        MfField.SERVER_OS,
        MfField.SERVER_OS_VERSION,
        MfField.SERVER_FQDN,
        MfField.SERVER_TIER,
        MfField.SERVER_ENVIRONMENT,
        MfField.SUBNET_ID,
        MfField.SECURITY_GROUP_ID,
        MfField.SUBNET_ID_TEST,
        MfField.SECURITY_GROUP_ID_TEST,
        MfField.INSTANCE_TYPE,
        MfField.TENANCY,
        MfField.IAM_ROLE,
    }

    PUT_FIELDS = {
        MfField.SERVER_OS,
        MfField.SERVER_OS_VERSION,
        MfField.SERVER_FQDN,
        MfField.SERVER_TIER,
        MfField.SERVER_ENVIRONMENT,
        MfField.SUBNET_ID,
        MfField.SECURITY_GROUP_ID,
        MfField.SUBNET_ID_TEST,
        MfField.SECURITY_GROUP_ID_TEST,
        MfField.INSTANCE_TYPE,
        MfField.TENANCY,
        MfField.IAM_ROLE,
    }

    _app = None
    _data = {}
    _id = None

    def __init__(self, data: dict = None, identifier: int = None, app: App = App()):
        if data is None:
            data = {}

        super().__init__(data=data, identifier=identifier)
        self.set_app(app)

    def __str__(self):
        return self._data[MfField.SERVER_ID]

    def set_app(self, app: App):
        self._app = app
        self.update_data()

    def get_app(self):
        return self._app

    def is_filled(self):
        return super().is_filled() and self.get_app().is_filled()

    def update_data(self):
        if self.get_app() and self.get_app().get_id():
            self._data[MfField.APP_ID] = self.get_app().get_id()


class MigrationFactoryDataValidator:
    """ Allow to validate Migration Factory data objects """

    ALLOWED_SERVER_OS = ['windows', 'linux']
    ALLOWED_SERVER_TIER = ['app', 'db', 'wav']
    ALLOWED_TENANCY = ['Shared', 'Dedicated', 'Dedicated Host']

    _validation_error_bag = MessageBag(type_of_bag='error')

    @classmethod
    def validate_servers_data(cls, servers: [Server], exit_on_error: bool = True):
        apps = list(map(lambda x: x.get_app(), servers))
        waves = list(map(lambda x: x.get_wave(), apps))

        cls._check_dict_value_duplication(servers, MfField.SERVER_NAME)
        cls._check_dict_value_duplication(servers, MfField.SERVER_FQDN)
        cls._check_dict_value_consistency(apps, MfField.CLOUDENDURE_PROJECT_NAME)
        cls._check_dict_value_consistency(apps, MfField.AWS_ACCOUNT_ID)
        cls._check_dict_value_consistency(waves, MfField.WAVE_NAME)

        for server_data in servers:
            cls._validate_with_regexp(
                server_data.get_app().get(MfField.AWS_ACCOUNT_ID),
                AWSValidator.REGEXP_ACCOUNT_ID,
                'an account ID name'
            )
            cls._validate_with_regexp(
                server_data.get_app().get_wave().get(MfField.WAVE_NAME),
                AWSValidator.REGEXP_CLOUDENDURE_PROJECT_NAME,
                'a wave name'
            )
            cls._validate_with_regexp(
                server_data.get_app().get(MfField.CLOUDENDURE_PROJECT_NAME),
                AWSValidator.REGEXP_CLOUDENDURE_PROJECT_NAME,
                'a project name'
            )
            cls._validate_with_regexp(
                server_data.get(MfField.INSTANCE_TYPE), AWSValidator.REGEXP_INSTANCE_TYPE, 'an instance type'
            )

            cls._validate_with_regexp(
                server_data.get(MfField.SUBNET_ID), AWSValidator.REGEXP_SUBNET_ID, 'an AWS subnet ID'
            )
            cls._validate_with_regexp(
                server_data.get(MfField.SUBNET_ID_TEST), AWSValidator.REGEXP_SUBNET_ID, 'an AWS subnet ID'
            )

            cls._validate_with_enum(server_data.get(MfField.SERVER_OS), cls.ALLOWED_SERVER_OS, 'a server OS')
            cls._validate_with_enum(server_data.get(MfField.SERVER_TIER), cls.ALLOWED_SERVER_TIER, 'a server tier')
            cls._validate_with_enum(server_data.get(MfField.TENANCY), cls.ALLOWED_TENANCY, 'a tenancy')

            for security_group in server_data.get(MfField.SECURITY_GROUP_ID).split(';'):
                cls._validate_with_regexp(security_group, AWSValidator.REGEXP_SECURITY_GROUP_ID, 'a security group ID')

            for security_group in server_data.get(MfField.SECURITY_GROUP_ID_TEST).split(';'):
                cls._validate_with_regexp(
                    security_group, AWSValidator.REGEXP_SECURITY_GROUP_ID, 'a security group ID (for test)'
                )

        cls._validation_error_bag.unload()

        if not cls._validation_error_bag.is_empty() and exit_on_error:
            exit(1)

    @classmethod
    def _check_dict_value_consistency(cls, objects_to_check: [MigrationFactoryData], key: str):
        if len(list(dict.fromkeys(map(lambda x: x.get(key).strip(), objects_to_check)))) != 1:
            cls._validation_error_bag.add('{}: “{}” key is not consistent among all servers.'.format(
                cls.__class__.__name__, key
            ))

    @classmethod
    def _check_dict_value_duplication(cls, objects_to_check: [MigrationFactoryData], key: str):
        if list(map(lambda x: x.get(key).strip(), objects_to_check)).count(key) > 1:
            cls._validation_error_bag.add('{}: “{}” key is duplicated among all servers.'.format(
                cls.__class__.__name__, key
            ))

    @classmethod
    def _validate_with_regexp(cls, value: str, regexp: str, description: str):
        cls._debug_validate(value)
        if not re.match(regexp, value):
            cls._validation_error_bag.add('{}: Given “{}” as {} is invalid (failed regex: “{}”).'.format(
                cls.__class__.__name__, value, description, regexp
            ))

    @classmethod
    def _validate_with_enum(cls, value, enum, description):
        cls._debug_validate(value)
        if value not in enum and value.lower() not in enum:
            cls._validation_error_bag.add('{}: Given “{}” as {} is invalid (allowed values: {}).'.format(
                cls.__class__.__name__, value, description, str(enum)
            ))

    @classmethod
    def _debug_validate(cls, value):
        logging.getLogger('root').debug('{}: Validating user input: “{}”)'.format(
            cls.__class__.__name__, value
        ))


class MigrationFactoryAuthenticator:
    """ Allow to login to the migration Migration Factory and store authorization token """

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
            url = self._guess_url(uri)

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

    def get_user_apps_by_wave_name(self, wave_name: str):
        wave_id = self.get_user_wave_by_name(wave_name)[MfField.WAVE_ID]

        return self.get_user_apps_by_wave_id(wave_id)

    def get_user_apps_by_wave_id(self, wave_id: str):
        all_apps = self.get(uri=self.URI_USER_APP_LIST)

        return sorted(app for app in all_apps if app[MfField.WAVE_ID] == wave_id)

    def get_user_app_by_name(self, app_name):
        all_apps = self.get(uri=self.URI_USER_APP_LIST)

        for app in all_apps:
            if app[MfField.APP_NAME] == app_name:
                return app

        return None

    def get_user_wave_by_name(self, wave_name):
        all_waves = self.get(uri=self.URI_USER_WAVE_LIST)

        for wave in all_waves:
            if wave[MfField.WAVE_NAME] == wave_name:
                return wave

        return None

    def get_user_server_by_name(self, server_name):
        all_servers = self.get(uri=self.URI_USER_SERVER_LIST)

        for server in all_servers:
            if server[MfField.SERVER_NAME] == server_name:
                return server

        return None

    def get_user_server_ids(self, filter_app_id=None):
        _server_list = self.get(self.URI_USER_SERVER_LIST)

        _server_selected_list_id = []

        for server in _server_list:
            if filter_app_id:
                if MfField.APP_ID in server and server[MfField.APP_ID] == filter_app_id:
                    _server_selected_list_id.append(server[MfField.SERVER_ID])
                else:
                    logging.getLogger('root').debug('{}: server id “{}” filtered (not in app {})'.format(
                        self.__class__.__name__, server[MfField.SERVER_ID], filter_app_id
                    ))
            else:
                _server_selected_list_id.append(server[MfField.SERVER_ID])

        return _server_selected_list_id

    def _guess_url(self, uri):
        if self._has_user_uri(uri):
            return self._endpoints_loader.get_user_api_url()
        if self._has_admin_uri(uri):
            return self._endpoints_loader.get_admin_api_url()
        if self._has_login_uri(uri):
            return self._endpoints_loader.get_login_api_url()

        return self._endpoints_loader.get_tools_api_url()

    @classmethod
    def _has_user_uri(cls, uri):
        return re.match('.*/user/.*', uri)

    @classmethod
    def _has_admin_uri(cls, uri):
        return re.match('.*/admin/.*', uri)

    @classmethod
    def _has_login_uri(cls, uri):
        return re.match('.*/login.*', uri)


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
