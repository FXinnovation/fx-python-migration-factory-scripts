#!/usr/bin/env python3

import logging
import os
from binascii import hexlify

import paramiko
from paramiko import AuthenticationException, BadHostKeyException, SSHException, PasswordRequiredException, \
    MissingHostKeyPolicy

import mf
from mf.utils import EnvironmentVariableFetcher, UserManualConfirmation


class SSHClient(paramiko.SSHClient):
    """
        Decorate paramiko.SSHClient
        Adds an execute method to perform SSH commands
        Adds an sftp_put method to copy files remotely
    """

    _hostname = ''

    _sftp_client = None

    def __init__(self, hostname: str):
        self._hostname = hostname
        super(SSHClient, self).__init__()

    def execute(self, command: str):
        stdin, stdout, stderr = self.exec_command(command)

        stdout.channel.recv_exit_status()
        lines = stdout.readlines()
        stderr.channel.recv_exit_status()
        err_lines = stderr.readlines()

        if len(err_lines) != 0:
            logging.getLogger('root').error(
                '{}: Command on host “{}” failed with this error: “{}”.'.format(
                    self.__class__.__name__, self._hostname, "\n".join(err_lines)
                )
            )
            quit(1)

        return lines

    def sftp_put(self, filename: str, destination: str):
        if self._sftp_client is None:
            self._sftp_client = self.open_sftp()

        try:
            self._sftp_client.put(filename, destination)

            logging.getLogger('root').info(
                '{}: Sent {} to {}:{}.'.format(
                    self.__class__.__name__, filename, self._hostname, destination
                )
            )
        except Exception as exception:
            logging.getLogger('root').error(
                "Copy file “{}” to “{}” on host “{}” failed du to: \n {}".format(
                    filename, destination, self._hostname, str(exception)
                )
            )

    def close(self):
        if self._sftp_client is not None:
            self._sftp_client.close()

        super(SSHClient, self).close()


class SSHConnector:
    """ Connects to a distant server using SSH """

    _user = ''
    _hostname = ''
    _port = 22

    def __init__(self, user, hostname, port):
        self._user = user
        self._hostname = hostname
        self._port = port

    def connect(
        self, key_file_path: str = None, key_passphrase: str = None, password: str = None, retry_count: int = 0
    ) -> SSHClient:
        ssh_client = None
        try:
            logging.getLogger('root').debug(
                "{}: SSH connection attempt on {}:\nUser: {}\nPort: {}\nKey: {}\nPassword: {}\nPassphrase: {}\n".format(
                    self.__class__.__name__,
                    self._hostname,
                    self._user,
                    self._port,
                    "not set" if key_file_path is None else key_file_path,
                    "not set" if password is None else "*** (set)",
                    "not set" if key_passphrase is None else "*** (set)",
                )
            )

            ssh_client = SSHClient(self._hostname)
            ssh_client.set_missing_host_key_policy(AskingPolicy())
            ssh_client.load_system_host_keys()
            ssh_client.connect(
                port=self._port,
                hostname=self._hostname,
                username=self._user,
                password=password,
                key_filename=key_file_path,
                passphrase=key_passphrase,
            )
        except PasswordRequiredException:
            if key_passphrase is None and retry_count < 2:
                key_passphrase = EnvironmentVariableFetcher.fetch(
                    env_var_names=mf.ENV_VAR_LINUX_PRIVATE_KEY_PASSPHRASE,
                    env_var_description='Linux key passphrase (for hostname “{}”): '.format(self._hostname),
                    sensitive=True
                )
                ssh_client.close()
                return self.connect(
                    key_file_path=key_file_path, key_passphrase=key_passphrase, retry_count=retry_count + 1
                )
            else:
                logging.getLogger('root').error('{}: Cannot prepare SSH key file “{}”. Passphrase is wrong.'.format(
                    self.__class__.__name__, self._hostname
                ))
                quit(1)
        except IOError as exception:
            logging.getLogger('root').error('{}: Cannot prepare SSH key file “{}”. Got this error “{}”.'.format(
                self.__class__.__name__, key_file_path, exception
            ))
            logging.getLogger('root').error('{}: Cannot join hostname “{}”. Got this error “{}”.'.format(
                self.__class__.__name__, self._hostname, exception
            ))
            quit(1)
        except AuthenticationException as exception:
            if password is not None and retry_count < 2:
                print('Wrong password. Try again.')
                password = EnvironmentVariableFetcher.fetch(
                    env_var_names=mf.ENV_VAR_LINUX_PASSWORD,
                    env_var_description='Linux user “{}” password for hostname “{}”: '.format(self._user,
                                                                                              self._hostname),
                    sensitive=True
                )
                ssh_client.close()
                return self.connect(password=password, retry_count=retry_count + 1)
            else:
                logging.getLogger('root').error('{}: Connection to host “{}” failed with error “{}”.'.format(
                    self.__class__.__name__, self._hostname, exception
                ))
                quit(1)
        except BadHostKeyException:
            logging.getLogger('root').error(
                '{}: Connection to host “{}” failed. This host has a different key that the one saved locally!'.format(
                    self.__class__.__name__, self._hostname
                ))
            quit(1)
        except SSHException as exception:
            logging.getLogger('root').error(
                '{}: Connection to host “{}” with user "{}" on port “{}” failed with this error: “{}”.'.format(
                    self.__class__.__name__, self._hostname, self._user, self._port, exception
                )
            )
            if key_file_path is not None:
                logging.getLogger('root').error(
                    '{}: Make sure your key file {} is indeed a SSH private key.'.format(
                        self.__class__.__name__, key_file_path
                    )
                )
            if key_passphrase is not None:
                logging.getLogger('root').error(
                    '{}: Make sure your key passphrase is correct.'.format(
                        self.__class__.__name__
                    )
                )
            quit(1)

        return ssh_client

    def set_hostname(self, hostname: str):
        self._hostname = hostname

    def get_hostname(self):
        return self._hostname


class AskingPolicy(MissingHostKeyPolicy):
    """
        Policy for asking to add the hostname key to the system known hosts.
        Either add the missing host key or terminate the script.
    """

    def missing_host_key(self, client, hostname, key):
        if (not UserManualConfirmation.ask(
                'Key {} {} (MD5) is MISSING from local known hosts. MITM MAY BE HAPPENING! Save & proceed? [Y]'.format(
                    key.get_name(),
                    hexlify(key.get_fingerprint()).decode('utf-8')
                ),
        )):
            logging.getLogger('root').error(
                "{}: Server key fingerprint {} {} (MD5) rejected. Aborting.".format(
                    self.__class__.__name__,
                    key.get_name(),
                    hexlify(key.get_fingerprint()).decode('utf-8')
                ),
            )
            quit(1)

        client.get_host_keys().add(hostname, key.get_name(), key)
        client.save_host_keys(os.path.expanduser("~/.ssh/known_hosts"))

        logging.getLogger('root').info(
            "{}: Adding {} host key for {}: {}".format(
                self.__class__.__name__, key.get_name(), hostname, hexlify(key.get_fingerprint()).decode('utf-8')
            ),
        )


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
