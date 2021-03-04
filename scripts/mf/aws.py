#!/usr/bin/env python3

import logging
import re

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
            env_var_names=ENV_VAR_AWS_ACCESS_KEY_NAMES, env_var_description='AWS Access Key ID')
        self._aws_secret_access_key = EnvironmentVariableFetcher.fetch(
            env_var_names=ENV_VAR_AWS_SECRET_KEY_NAMES, env_var_description='AWS Access Secret Key', sensitive=True)
        self._aws_region = EnvironmentVariableFetcher.fetch(
            env_var_names=ENV_VAR_AWS_REGION_NAMES, env_var_description='AWS Region')

    def get_ec2(self):
        if self._ec2_client is None:
            self._ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=self._aws_access_key,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self._aws_region
            )

        return self._ec2_client

    def describe_ec2_instance(self, instance_id: str = None):
        return self.get_ec2().describe_instances(InstanceIds=[instance_id])

    def get_ec2_instance_ips(self, instance_id: str = None):
        ec2_instance = self.describe_ec2_instance(instance_id=instance_id)

        logging.getLogger('root').debug('{}: instance “{}”: {}'.format(
            self.__class__.__name__, instance_id, ec2_instance
        ))

        instance_ip = []
        for reservation in ec2_instance['Reservations']:
            for instance in reservation['Instances']:
                for nic in instance['NetworkInterfaces']:
                    for ips in nic['PrivateIpAddresses']:
                        instance_ip.append(ips['PrivateIpAddress'])

        return instance_ip


class AWSValidator:
    """ Check values to be compliant with AWS """

    REGEXP_ACCOUNT_ID = '^[0-9]{12}$'
    REGEXP_CLOUDENDURE_PROJECT_NAME = '^[0-9A-Za-z _-]{2,64}$'
    REGEXP_INSTANCE_TYPE = '^(u-)?[a-z0-9]{2,4}\\.(nano|micro|small|medium|metal|(2|4|8|16|24)?x?large)$'
    REGEXP_SECURITY_GROUP_ID = '^sg-([a-z0-9]{8}|[a-z0-9]{17})$'
    REGEXP_SUBNET_ID = '^subnet-([a-z0-9]{8}|[a-z0-9]{17})$'
    REGEXP_WAVE_NAME = '^[0-9A-Za-z _-]{2,64}$'

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
