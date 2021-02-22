#!/usr/bin/env python3
import logging

import subprocess
import paramiko
from paramiko import AuthenticationException, BadHostKeyException, SSHException, PasswordRequiredException

import mf
from mf.utils import EnvironmentVariableFetcher


class SSHConnector:
    """ Connects to a distant server using SSH """

    TYPE_RSA = 'RSA'
    TYPE_DSA = 'DSA'
    TYPE_ED25519 = 'ED25519'
    TYPE_ECDSA = 'ECDSA'

    _user = ''
    _hostname = ''
    _port = 22

    def __init__(self, user, hostname, port):
        self._user = user
        self._hostname = hostname
        self._port = port

    def connect(self, key_file_path: str = None, key_passphrase: str = None, password: str = None, retry_count: int = 0):
        ssh_client = None
        try:
            logging.getLogger('root').debug(
                "{}: SSH connection attempt on {}:\nUser: {}\nPort: {}\nKey: {}\nPassword: {}\nPassphrase: {}\n".format(
                    self.__class__.__name__,
                    self._hostname,
                    self._user,
                    self._port,
                    key_file_path,
                    "empty" if password is None else "set",
                    "empty" if key_passphrase is None else "set",
                )
            )

            ssh_client = SSHClient(self._user, self._hostname, self._port)
            ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())
            ssh_client.connect(
                port=self._port,
                hostname=self._hostname,
                username=self._user,
                password=password,
                key_filename=key_file_path,
                passphrase=key_passphrase,
            )
        except PasswordRequiredException:
            if key_passphrase is None:
                key_passphrase = EnvironmentVariableFetcher.fetch(
                    env_var_names=mf.ENV_VAR_LINUX_PRIVATE_KEY_PASSPHRASE,
                    env_var_description='Linux key passphrase (for hostname “{}”): '.format(self._hostname),
                    sensitive=True
                )
                self.connect(key_file_path=key_file_path, key_passphrase=key_passphrase)
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
                    env_var_description='Linux user “{}” password for hostname “{}”: '.format(self._user, self._hostname),
                    sensitive=True
                )
                self.connect(password=password, retry_count=retry_count+1)
            else:
                logging.getLogger('root').error('{}: Connection to host “{}” failed with error “{}”.'.format(
                    self.__class__.__name__, self._hostname, exception
                ))
                quit(1)
        except BadHostKeyException:
            logging.getLogger('root').error('{}: Connection to host “{}” failed. Host is not in the known hosts.'.format(
                self.__class__.__name__, self._hostname
            ))
            quit(1)
        except SSHException as exception:
            logging.getLogger('root').error(
                '{}: Connection to host “{}” with user "{}" on port “{}” failed with this error: “{}”.'.format(
                    self.__class__.__name__, self._hostname, self._user, self._port, exception
                )
            )
            quit(1)

        return ssh_client

    def set_hostname(self, hostname: str):
        self._hostname = hostname

    def get_hostname(self):
        return self._hostname

    def _guess_ssh_key_type(self, key_file_path: str) -> str:
        # This is because paramiko does not offer any reliable way to guess a SSH private key type
        # Thus: this is not compatible on Windows (and this is why no specific class for running local bash was created)

        COMMAND_KEYGEN =  "ssh-keygen -l -f {}".format(key_file_path)
        COMMAND_AWK = "| awk '{ print $NF }'"
        COMMAND_TR = "| tr -d '()'"
        key_type_process_out, key_type_process_err = subprocess.Popen(
            COMMAND_KEYGEN + COMMAND_AWK + COMMAND_TR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        ).communicate()

        if key_type_process_err.decode() != '':
            logging.getLogger('root').debug("{}: Error while running command: \n\n{}".format(
                self.__class__.__name__,  key_type_process_err.decode()
            ))

        return key_type_process_out.decode()


class SSHClient(paramiko.SSHClient):
    _user = ''
    _hostname = ''
    _port = 22

    _sftp_client = None

    def __init__(self, user, hostname, port):
        self._user = user
        self._hostname = hostname
        self._port = port
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
        except Exception as exception:
            logging.getLogger('root').error(
                "Copying files from “" + filename + "” to " +
                "/boot/post_launch" + " on host " + self._hostname + " failed due to; \n" +
                str(exception)
            )

    def close(self):
        self._sftp_client.close()
        super(SSHClient, self).close()


class AskingPolicy(paramiko.MissingHostKeyPolicy):
    """
        Policy for asking to add the hostname key to the
        local `.HostKeys` object, and saving it.  This is used by `.SSHClient`.
    """

    def missing_host_key(self, client, hostname, key):


        client._host_keys.add(hostname, key.get_name(), key)
        if client._host_keys_filename is not None:
            client.save_host_keys(client._host_keys_filename)
        client._log(
            DEBUG,
            "Adding {} host key for {}: {}".format(
                key.get_name(), hostname, hexlify(key.get_fingerprint())
            ),
        )


class RejectPolicy(MissingHostKeyPolicy):
    """
    Policy for automatically rejecting the unknown hostname & key.  This is
    used by `.SSHClient`.
    """

    def missing_host_key(self, client, hostname, key):
        client._log(
            DEBUG,
            "Rejecting {} host key for {}: {}".format(
                key.get_name(), hostname, hexlify(key.get_fingerprint())
            ),
        )
        raise SSHException(
            "Server {!r} not found in known_hosts".format(hostname)
        )

if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
