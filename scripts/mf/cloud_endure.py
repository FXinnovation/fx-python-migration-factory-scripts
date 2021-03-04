#!/usr/bin/env python3

import json
import logging
import sys

import requests

from . import ENV_VAR_CLOUDENDURE_TOKEN
from .utils import EnvironmentVariableFetcher
from .utils import Requester


class CloudEndureSession:
    """ Login to CloudEndure """

    CLOUDENDURE_ENDPOINT_HOST = 'https://console.cloudendure.com'
    CLOUDENDURE_ENDPOINT_URI = '/api/latest/{}'

    _api_token = None
    _api_endpoint_uri = None
    _session_token = None
    _session = None

    def __init__(self):
        self._api_token = EnvironmentVariableFetcher.fetch(
            env_var_names=ENV_VAR_CLOUDENDURE_TOKEN, env_var_description='CloudEndure API token'
        )

    def __call__(self):
        return self.get_session()

    def login(self):
        self._session = requests.Session()
        self._session.headers.update({'Content-type': 'application/json', 'Accept': 'text/plain'})
        self._api_endpoint_uri = self.CLOUDENDURE_ENDPOINT_URI
        response = self._login_request()

        if response.status_code != 200:
            logging.getLogger('root').error(self.__class__.__name__ + ': CloudEndure Login failed.')
            sys.exit(2)

        self._session_token = self._session.cookies.get('XSRF-TOKEN')
        self._session.headers['X-XSRF-TOKEN'] = self._session_token

        return self._session

    def _login_request(self):
        response = self._session.post(
            url=self.CLOUDENDURE_ENDPOINT_HOST + self._api_endpoint_uri.format('login'),
            data=json.dumps({'userApiToken': self._api_token})
        )
        logging.getLogger('root').debug(self.__class__.__name__ + ':' + str(response))

        return response

    def get_api_endpoint(self):
        if self._api_endpoint_uri is None:
            self.login()

        return self.CLOUDENDURE_ENDPOINT_HOST + self._api_endpoint_uri

    def get_session_token(self):
        if self._session_token is None:
            self.login()

        return self._session_token

    def get_session(self):
        if self._session is None:
            self.login()

        return self._session


class CloudEndureRequester:
    """ Allow to make requests against the CloudEndure* """

    REGIONS = {
        "gov-east-2": "AWS GovCloud (US)",
        "eu-west-1": "AWS EU (Ireland)",
        "ap-east-1": "AWS Asia Pacific (Hong Kong)",
        "ap-southeast-1": "AWS Asia Pacific (Singapore)",
        "ap-southeast-2": "AWS Asia Pacific (Sydney)",
        "us-west-2": "AWS US West (Oregon)",
        "sa-east-1": "AWS South America (Sao Paulo)",
        "us-east-2": "AWS US East (Ohio)",
        "ca-central-1": "AWS Canada (Central)",
        "us-west-1": "AWS US West (Northern California)",
        "eu-west-3": "AWS EU (Paris)",
        "ap-northeast-1": "AWS Asia Pacific (Tokyo)",
        "me-south-1": "AWS Middle East (Bahrain)",
        "eu-central-1": "AWS EU (Frankfurt)",
        "ap-south-1": "AWS Asia Pacific (Mumbai)",
        "eu-west-2": "AWS EU (London)",
        "gov-east-1": "AWS GovCloud (US-East)",
        "ap-northeast-2": "AWS Asia Pacific (Seoul)",
        "eu-north-1": "AWS EU (Stockholm)",
        "us-east-1": "AWS US East (Northern Virginia)",
    }

    URI_PROJECTS = 'projects'
    URI_PROJECT = URI_PROJECTS + '/{}'

    URI_MACHINES = URI_PROJECT + '/machines'
    URI_MACHINE = URI_PROJECT + '/machine/{}'

    URI_REPLICA = URI_PROJECT + '/replicas/{}'

    _cloud_endure_session = None

    def __init__(self):
        self._cloud_endure_session = CloudEndureSession()

    def get_aws_cloud_id(self):
        response = self.get('clouds')

        for clouds_item in response['items']:
            if clouds_item['name'] == 'AWS':
                return clouds_item['id']

    def get_migration_license(self):
        response = self.get('licenses')

        for license_item in response['items']:
            if license_item['type'] == 'MIGRATION':
                return license_item['id']

    def get_on_prem_region_id(self):
        response = self.get('cloudCredentials/00000000-0000-0000-0000-000000000000/regions')

        for region_items in response['items']:
            return region_items['id']

    def get_aws_region_id(self, cloud_credentials_id, aws_region):
        response = self.get('cloudCredentials/{}/regions'.format(cloud_credentials_id))
        for region in response['items']:
            if region['name'] == self.REGIONS[aws_region]:
                return region['id']

    def get_project_by_name(self, project_name):
        response = self.get(self.URI_PROJECTS)
        for project in response['items']:
            if project['name'] == project_name:
                logging.getLogger('root').debug(self.__class__.__name__ + ': ' + str(project))
                return project

        logging.getLogger('root').debug(self.__class__.__name__ + ': ' +
                                        str("project") + project_name + str(" not found"))

        return False

    def get_project_id(self, project_name):
        project = self.get_project_by_name(project_name)

        if not project:
            return False

        return project['id']

    def get_machines(self, project_name):
        _project_id = self.get_project_id(project_name)

        if not _project_id:
            return False

        machines = self.get(self.URI_MACHINES.format(_project_id))

        if not machines:
            logging.getLogger('root').debug(self.__class__.__name__ + ': ' +
                                            str("project") + project_name + str(" is empty"))

        return machines

    def get_machine(self, project_name: str, machine_name: str):
        machines = self.get_machines(project_name)

        if not machines:
            logging.getLogger('root').debug(self.__class__.__name__ + ': ' +
                                            str("project ") + project_name + str(" has no machine"))
            return None

        for machine in machines['items']:
            if machine_name.lower() == machine['sourceProperties']['name'].lower():
                logging.getLogger('root').debug(self.__class__.__name__ + ': ' + str("project ") +
                                                project_name + str(" has a machine ") + machine['sourceProperties']['name'])
                return machine

        return None

    def get_machine_replica(self, replica_id, project_name):
        _project_id = self.get_project_id(project_name)

        if not _project_id:
            return False

        return self.get(self.URI_REPLICA.format(_project_id, replica_id))

    def get_all_project_names(self):
        response = self.get(self.URI_PROJECTS)

        return list(map(lambda project: project['name'], response['items']))

    def get_api_token(self, project_name: str):
        project = self.get_project_by_name(project_name)

        if not project:
            return False

        if 'agentInstallationToken' not in project:
            logging.getLogger('root').error("{}: {} didn't have installation token".format(
                self.__class__.__name__, project_name
            ))

        return project['agentInstallationToken']

    def get(self, uri):
        return Requester.get(
            uri=self._cloud_endure_session.get_api_endpoint().format(uri),
            request_instance=self._cloud_endure_session.get_session()
        )

    def post(self, uri, data=None):
        return Requester.post(
            uri=self._cloud_endure_session.get_api_endpoint().format(uri),
            data=json.dumps(data),
            request_instance=self._cloud_endure_session.get_session()
        )

    def patch(self, uri, data=None):
        return Requester.patch(
            uri=self._cloud_endure_session.get_api_endpoint().format(uri),
            data=json.dumps(data),
            request_instance=self._cloud_endure_session.get_session()
        )

    def delete(self, uri):
        return Requester.delete(
            uri=self._cloud_endure_session.get_api_endpoint().format(uri),
            request_instance=self._cloud_endure_session.get_session(),
        )


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
