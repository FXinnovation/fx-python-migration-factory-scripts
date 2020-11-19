#!/usr/bin/env python3

import argparse
import logging
import os

from botocore.exceptions import ClientError

import mf
from mf.aws import AWSServiceAccessor
from mf.config_loaders import DefaultsLoader
from mf.utils import EnvironmentVariableFetcher
from mf.utils import Utils


class TemplateSecurityGroupCreator:
    """ Create copies of template security groups """

    _arguments = []
    _defaults = {}
    _environments = []
    _path_wave = ''
    _aws_service_accessor = None

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', action='store_true', help='Enable debug outputs')
        parser.add_argument('--wave-name', required=True, help='Name of the wave to prepare')
        parser.add_argument(
            '--wave-sg-prefix',
            default='rehost',
            help='Prefix of the Security Group duplicates from the template Security Group'
        )
        parser.add_argument(
            '--config-file-defaults',
            default=EnvironmentVariableFetcher.fetch(
                mf.ENV_VAR_DEFAULTS_CONFIG_FILE,
                default=mf.DEFAULT_ENV_VAR_DEFAULTS_CONFIG_FILE
            ),
            help='Configuration file containing default IDs'
        )
        environment_arg = parser.add_argument('--environment', default='prod', help='Environment of the wave')

        self._arguments = parser.parse_args()

        mf.utils.setup_logging(self._arguments.v)
        defaults_loader = DefaultsLoader()
        self._defaults = defaults_loader.load(
            default_config_file=self._arguments.config_file_defaults,
            environment=self._arguments.environment
        )

        environment_arg.choices = defaults_loader.get_available_environments()

        self._arguments = parser.parse_args()

        Utils.check_is_serializable_as_path(self._arguments.wave_name)
        self._path_wave = os.path.join(mf.PATH_HOME, self._arguments.wave_name)

        self._aws_service_accessor = AWSServiceAccessor()

    def template_security_group_id_default_exists(self):
        return 'template_security_group_id' in self._defaults.keys() and \
               self._defaults['template_security_group_id'] is not ''

    def create(self):
        return self._create()

    def create_for_testing(self):
        return self._create(for_testing=True)

    def _create(self, for_testing=False):
        if not self.template_security_group_id_default_exists():
            logging.debug('No security group template. Skipping security group copy.')
            return None

        template_security_group = self._aws_service_accessor.get_ec2().describe_security_groups(GroupIds=[
            self._defaults['template_security_group_id']
        ])['SecurityGroups'][0]

        print('### Create template Security Group copy' + (' (testing)' if for_testing else '') + '…', end=' ')

        try:
            sg_create_response = self._aws_service_accessor.get_ec2().create_security_group(
                Description='For the ' + self._arguments.wave_name + ' wave ' + (
                    '(testing)' if for_testing else '') + ' .',
                GroupName=self._arguments.wave_sg_prefix + (
                    '-testing-' if for_testing else '-') + self._arguments.wave_name,
                VpcId=template_security_group['VpcId'],
                DryRun=False
            )
            print('✔ Done')

            logging.debug(self.__class__.__name__ + ':' + str(sg_create_response))
        except ClientError as error:
            if error.response['Error']['Code'] == 'InvalidGroup.Duplicate':
                print('✔ Already Done')

                sg_create_response = self._aws_service_accessor.get_ec2().describe_security_groups(Filters=[
                    dict(Name='group-name', Values=[
                        self._arguments.wave_sg_prefix + (
                            '-testing-' if for_testing else '-') + self._arguments.wave_name
                    ])
                ])['SecurityGroups'][0]
            else:
                print('')
                raise

        print('### Populate Security Group copy ' + ('(testing) ' if for_testing else '') + 'rules…', end=' ')

        try:
            sg_authorize_response = self._aws_service_accessor.get_ec2().authorize_security_group_ingress(
                GroupId=sg_create_response['GroupId'],
                IpPermissions=template_security_group['IpPermissions'],
            )

            print('✔ Done')
            logging.debug(self.__class__.__name__ + ':' + str(sg_authorize_response))
        except ClientError as error:
            if error.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                print('✔ Already Done')
            else:
                print('')
                raise

        return sg_create_response['GroupId']


if __name__ == '__main__':
    template_sg_creator = TemplateSecurityGroupCreator()
    template_sg_creator.create()
