#!/usr/bin/env python3
import logging

import paramiko
from paramiko import AuthenticationException, BadHostKeyException, SSHException, PasswordRequiredException

import mf
from mf.utils import EnvironmentVariableFetcher


class SSHConnector:
    """ Connects to a distant server using SSH """

    _user = ''
    _hostname = ''
    _port = 22

    def __init__(self, user, hostname, port):
        self._user = user
        self._hostname = hostname
        self._port = port

    def connect_with_password(self, password: str = None, retry_count: int = 0):
        if password is None:
            password = EnvironmentVariableFetcher.fetch(
                env_var_names=mf.ENV_VAR_LINUX_PASSWORD,
                env_var_description='Linux user “{}” password for hostname “{}”: '.format(self._user, self._hostname),
                sensitive=True
            )

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(port=self._port, hostname=self._hostname, username=self._user, password=password)
        except AuthenticationException as exception:
            if retry_count < 3:
                print('Wrong password. Try again.')
                self.connect_with_password(password=None, retry_count=retry_count+1)
            else:
                logging.error('{}: Connection to host “{}” failed with error “{}”.'.format(
                    self.__class__.__name__, self._hostname, exception
                ))
                quit(1)
        except BadHostKeyException:
            logging.error('{}: Connection to host “{}” failed. Host is not in the known hosts.'.format(
                self.__class__.__name__, self._hostname
            ))
            quit(1)
        except SSHException as exception:
            logging.error('{}: Connection to host “{}” failed with this error: “{}”.'.format(
                self.__class__.__name__, self._hostname, exception
            ))
            quit(1)

    def connect_with_private_key(self, key_file_path: str, key_passphrase: str = None):
        try:
            private_key = paramiko.PKey.from_private_key_file(key_file_path, key_passphrase)
        except (IOError, SSHException) as exception:
            logging.error('{}: Cannot prepare SSH key file “{}”. Got this error “{}”.'.format(
                self.__class__.__name__, key_file_path, exception
            ))
            quit(1)
        except PasswordRequiredException:
            if key_passphrase is None:
                key_passphrase = EnvironmentVariableFetcher.fetch(
                    env_var_names=mf.ENV_VAR_LINUX_PRIVATE_KEY_PASSPHRASE,
                    env_var_description='Linux key passphrase (for hostname “{}”): '.format(self._hostname),
                    sensitive=True
                )
                self.connect_with_private_key(key_file_path, key_passphrase)
            else:
                logging.error('{}: Cannot prepare SSH key file “{}”. Passphrase is wrong.'.format(
                    self.__class__.__name__, self._hostname
                ))
                quit(1)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        try:
            ssh.connect(port=self._port, hostname=self._hostname, username=self._user, pkey=private_key)
        except AuthenticationException as exception:
            logging.error('{}: Connection to host “{}” failed with error “{}”.'.format(
                self.__class__.__name__, self._hostname, exception
            ))
            quit(1)
        except BadHostKeyException:
            logging.error('{}: Connection to host “{}” failed. Host is not in the known hosts.'.format(
                self.__class__.__name__, self._hostname
            ))
            quit(1)
        except SSHException as exception:
            logging.error('{}: Connection to host “{}” failed with this error: “{}”.'.format(
                self.__class__.__name__, self._hostname, exception
            ))
            quit(1)


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
