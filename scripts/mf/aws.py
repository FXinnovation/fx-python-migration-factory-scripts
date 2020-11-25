#!/usr/bin/env python3

import boto3

from . import ENV_VAR_AWS_ACCESS_KEY_NAMES
from . import ENV_VAR_AWS_REGION_NAMES
from . import ENV_VAR_AWS_SECRET_KEY_NAMES
from .utils import EnvironmentVariableFetcher

import re

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


class AWSValidator:
    """ Check values to be compliant with AWS """

    REGEXP_CLOUDENDURE_PROJECT_NAME = '^[0-9A-Za-z _-]{2,64}$'
    REGEXP_ACCOUNT_ID = '^[0-9]{12}$'
    REGEXP_SUBNET_ID = '^subnet-([a-z0-9]{8}|[a-z0-9]{17})$'
    REGEXP_SECURITY_GROUP_ID = '^sg-([a-z0-9]{8}|[a-z0-9]{17})$'
    REGEXP_INSTANCE_TYPE = '^(u-)?[a-z0-9]{2,4}\\.(nano|micro|small|medium|metal|(2|4|8|16|24)?x?large)$'

    @classmethod
    def is_account_id(cls, value):
        return re.match(cls.REGEXP_ACCOUNT_ID, value)

    @classmethod
    def is_cloud_endure_project_name(cls, value):
        return re.match(cls.REGEXP_WAVE_NAME, value)

    @classmethod
    def is_subnet_id(cls, value):
        return re.match(cls.REGEXP_SUBNET_ID, value)

    @classmethod
    def is_security_group_id(cls, value):
        return re.match(cls.REGEXP_SECURITY_GROUP_ID, value)

    @classmethod
    def is_instance_type(cls, value):
        return re.match(cls.REGEXP_INSTANCE_TYPE, value)


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
