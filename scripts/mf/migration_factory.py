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
    TAGS = 'tags'


class MigrationFactoryData:
    """ Data object representing any data in Migration Factory (superclass) """

    FIELDS = {}
    PUT_FIELDS = {}

    _data = {}
    _id = None

    def __init__(self, data: dict, identifier: int = None):
        self._data = {}
        self._id = None
        self.fill(data, identifier)

    def fill(self, data: dict, identifier: int = None):
        for key, destination_value_type in self.FIELDS.items():
            if key not in data.keys():
                self._data[key] = self._get_empty_default(destination_value_type)
                continue

            if destination_value_type is str:
                self._data[key] = data[key].strip()
            elif destination_value_type is list:
                self._data[key] = data[key].split(';')
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
            temp_data[key] = self._data[key]

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

    @classmethod
    def _get_empty_default(cls, value_type):
        if value_type is str:
            return ''
        if value_type is list:
            return []
        if value_type is dict:
            return {}
        if value_type is int:
            return None


class Wave(MigrationFactoryData):
    """ Data object representing a wave in Migration Factory """

    FIELDS = {
        MfField.WAVE_NAME: str,
        MfField.WAVE_DESCRIPTION: str,
    }

    _data = {}
    _id = None

    def __init__(self, data: dict = None, identifier: int = None):
        if data is None:
            data = {}

        super().__init__(data=data, identifier=identifier)

    def __str__(self):
        if MfField.WAVE_ID not in self._data:
            return ''

        return self._data[MfField.WAVE_ID]


class App(MigrationFactoryData):
    """ Data object representing a app in Migration Factory """

    FIELDS = {
        MfField.WAVE_ID: int,
        MfField.APP_NAME: str,
        MfField.CLOUDENDURE_PROJECT_NAME: str,
        MfField.AWS_ACCOUNT_ID: str,
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
        if MfField.APP_ID not in self._data:
            return ''

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
        MfField.APP_ID: int,
        MfField.SERVER_NAME: str,
        MfField.SERVER_OS: str,
        MfField.SERVER_OS_VERSION: str,
        MfField.SERVER_FQDN: str,
        MfField.SERVER_TIER: str,
        MfField.SERVER_ENVIRONMENT: str,
        MfField.SUBNET_ID: list,
        MfField.SECURITY_GROUP_ID: list,
        MfField.SUBNET_ID_TEST: list,
        MfField.SECURITY_GROUP_ID_TEST: list,
        MfField.INSTANCE_TYPE: str,
        MfField.TENANCY: str,
        MfField.IAM_ROLE: str,
        MfField.TAGS: dict,
    }

    PUT_FIELDS = {
        MfField.SERVER_OS: str,
        MfField.SERVER_OS_VERSION: str,
        MfField.SERVER_FQDN: str,
        MfField.SERVER_TIER: str,
        MfField.SERVER_ENVIRONMENT: str,
        MfField.SUBNET_ID: list,
        MfField.SECURITY_GROUP_ID: list,
        MfField.SUBNET_ID_TEST: list,
        MfField.SECURITY_GROUP_ID_TEST: list,
        MfField.INSTANCE_TYPE: str,
        MfField.TENANCY: str,
        MfField.IAM_ROLE: str,
        MfField.TAGS: dict,
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
        if MfField.SERVER_ID not in self._data:
            return ''

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

        for server in servers:
            cls._validate_with_regexp(
                server.get_app().get(MfField.AWS_ACCOUNT_ID),
                AWSValidator.REGEXP_ACCOUNT_ID,
                'an account ID name'
            )
            cls._validate_with_regexp(
                server.get_app().get_wave().get(MfField.WAVE_NAME),
                AWSValidator.REGEXP_CLOUDENDURE_PROJECT_NAME,
                'a wave name'
            )
            cls._validate_with_regexp(
                server.get_app().get(MfField.CLOUDENDURE_PROJECT_NAME),
                AWSValidator.REGEXP_CLOUDENDURE_PROJECT_NAME,
                'a project name'
            )
            cls._validate_with_regexp(
                server.get(MfField.INSTANCE_TYPE), AWSValidator.REGEXP_INSTANCE_TYPE, 'an instance type'
            )

            for subnet_id in server.get(MfField.SUBNET_ID):
                cls._validate_with_regexp(
                    subnet_id, AWSValidator.REGEXP_SUBNET_ID, 'an AWS subnet ID'
                )
            for subnet_id in server.get(MfField.SUBNET_ID_TEST):
                cls._validate_with_regexp(
                    subnet_id, AWSValidator.REGEXP_SUBNET_ID, 'an AWS subnet ID (for test)'
                )

            cls._validate_with_enum(server.get(MfField.SERVER_OS), cls.ALLOWED_SERVER_OS, 'a server OS')
            cls._validate_with_enum(server.get(MfField.SERVER_TIER), cls.ALLOWED_SERVER_TIER, 'a server tier')
            cls._validate_with_enum(server.get(MfField.TENANCY), cls.ALLOWED_TENANCY, 'a tenancy')

            for security_group in server.get(MfField.SECURITY_GROUP_ID):
                cls._validate_with_regexp(security_group, AWSValidator.REGEXP_SECURITY_GROUP_ID, 'a security group ID')

            for security_group in server.get(MfField.SECURITY_GROUP_ID_TEST):
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
    URI_TOOL_CLOUDENDURE = '/prod/cloudendure'

    _migration_factory_authenticator = None
    _endpoints_loader = None

    def __init__(self, endpoints_loader):
        self._migration_factory_authenticator = MigrationFactoryAuthenticator(endpoints_loader.get_login_api_url())
        self._endpoints_loader = endpoints_loader
        requests_cache.install_cache('migration_factory', backend='memory', expire_after=30)

    @classmethod
    def clear_cache(cls):
        requests_cache.clear()

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

        self.clear_cache()

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

        self.clear_cache()

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

        self.clear_cache()

        return Requester.delete(
            uri=uri,
            url=url,
            headers=self._migration_factory_authenticator.populate_headers_with_authorization(headers),
            response_type=response_type,
        )

    def get_user_apps_by_wave_name(self, wave_name: str):
        wave = self.get_user_wave_by_name(wave_name)
        if wave is None:
            return None

        return self.get_user_apps_by_wave_id(wave[MfField.WAVE_ID])

    def get_user_apps_by_wave_id(self, wave_id: str):
        all_apps = self.get(uri=self.URI_USER_APP_LIST)

        apps = []
        for app in all_apps:
            if MfField.WAVE_ID in app and app[MfField.WAVE_ID] == wave_id:
                apps.append(app)

        return apps

    def get_user_app_by_name(self, app_name):
        all_apps = self.get(uri=self.URI_USER_APP_LIST)

        for app in all_apps:
            if MfField.WAVE_ID in app and app[MfField.APP_NAME] == app_name:
                return app

        return None

    def get_user_wave_by_name(self, wave_name):
        all_waves = self.get(uri=self.URI_USER_WAVE_LIST)

        for wave in all_waves:
            if wave[MfField.WAVE_NAME] == wave_name:
                return wave

        logging.getLogger('root').error('{}: wave “{}” not found'.format(
            self.__class__.__name__, wave_name
        ))

        return None

    def get_user_server_by_name(self, server_name):
        all_servers = self.get(uri=self.URI_USER_SERVER_LIST)

        for server in all_servers:
            if server[MfField.SERVER_NAME] == server_name:
                return server

        return None

    def get_user_servers_by_wave_name(self, wave_name):
        wave = self.get_user_wave_by_name(wave_name)
        all_apps = self.get_user_apps_by_wave_id(wave[MfField.WAVE_ID])
        all_servers = self.get(uri=self.URI_USER_SERVER_LIST)

        filtered_servers = []
        for app in all_apps:
            for server in all_servers:
                if server[MfField.APP_ID] == app[MfField.APP_ID]:
                    filtered_servers.append(server)

        if not filtered_servers:
            return None

        return filtered_servers

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

    def get_user_servers_by_wave(self, filter_wave_name: str):
        _server_list = self.get(self.URI_USER_SERVER_LIST)

        _server_selected_list_id = []

        for server in _server_list:
            app = self.get(self.URI_USER_APP.format(server[MfField.APP_ID]))
            if app is None:
                logging.getLogger('root').debug('{}: server id “{}” filtered (not in wave {})'.format(
                    self.__class__.__name__, server[MfField.SERVER_ID], filter_wave_name
                ))
                continue

            wave = self.get(self.URI_USER_WAVE.format(app[MfField.APP_ID]))
            if wave is None:
                logging.getLogger('root').debug('{}: server id “{}” filtered (not in wave {})'.format(
                    self.__class__.__name__, server[MfField.SERVER_ID], filter_wave_name
                ))
                continue

            if MfField.WAVE_NAME in wave and wave[MfField.WAVE_NAME] == filter_wave_name:
                _server_selected_list_id.append(server)
            else:
                logging.getLogger('root').debug('{}: server id “{}” filtered (not in wave {})'.format(
                    self.__class__.__name__, server[MfField.SERVER_ID], filter_wave_name
                ))

        return _server_selected_list_id

    def get_user_servers_by_wave_and_os(self, filter_wave_name, filter_os):
        _server_list = self.get_user_servers_by_wave(filter_wave_name=filter_wave_name)

        _server_selected_list_id = []
        if _server_list:
            for server in _server_list:
                if server[MfField.SERVER_OS].lower().strip() == filter_os.lower().strip():
                    _server_selected_list_id.append(server)

        return _server_selected_list_id

    def launch_target(self, wave_name: str, cloudendure_api_token: str, dry_run: bool = True, for_testing: bool = False, relaunch: bool = False):
        wave = self.get_user_wave_by_name(wave_name)

        apps = self.get_user_apps_by_wave_id(wave[MfField.WAVE_ID])

        if apps == []:
            logging.getLogger('root').error('{}: There is no apps in wave “{}”'.format(
                self.__class__.__name__, wave_name
            ))

        request_data = {
            "userapitoken": cloudendure_api_token,
            "launchtype": "cutover" if not for_testing else "test",
            "waveid": wave[MfField.WAVE_ID]
        }

        if dry_run:
            request_data["dryrun"] = "Yes"

        if relaunch and not dry_run:
            request_data["relaunch"] = True

        for app in apps:
            request_data["projectname"] = app[MfField.CLOUDENDURE_PROJECT_NAME]

            return self.post(self.URI_TOOL_CLOUDENDURE, data=json.dumps(request_data), response_type=Requester.RESPONSE_TYPE_TEXT)

        return

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
