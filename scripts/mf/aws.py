#!/usr/bin/env python3

import boto3

from . import ENV_VAR_AWS_ACCESS_KEY_NAMES
from . import ENV_VAR_AWS_REGION_NAMES
from . import ENV_VAR_AWS_SECRET_KEY_NAMES
from .utils import EnvironmentVariableFetcher


class AWSServiceAccessor:
    """ Allows access to AWS API endpoints """

    _environment_variable_fetcher = None
    _aws_access_key = ''
    _aws_secret_access_key = ''
    _aws_region = ''
    _ec2_client = None

    def __init__(self):
        self._aws_access_key = EnvironmentVariableFetcher.fetch(
            ENV_VAR_AWS_ACCESS_KEY_NAMES, 'AWS Access Key ID'
        )
        self._aws_secret_access_key = EnvironmentVariableFetcher.fetch(
            ENV_VAR_AWS_SECRET_KEY_NAMES, 'AWS Access Secret Key', sensitive=True
        )
        self._aws_region = EnvironmentVariableFetcher.fetch(ENV_VAR_AWS_REGION_NAMES, 'AWS Region')

    def get_ec2(self):
        if self._ec2_client is None:
            self._ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=self._aws_access_key,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self._aws_region
            )

        return self._ec2_client


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
