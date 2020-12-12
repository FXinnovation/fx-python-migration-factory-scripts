#!/usr/bin/env python3

import logging
import smtplib
from abc import ABC
from email.message import EmailMessage
from threading import Thread

import pymsteams
import time
import validators

from mf import BRAND
from mf.utils import EnvironmentVariableFetcher


class SendEventDecider:
    _whitelist: [str] = None
    _blacklist: [str] = None

    def __init__(self, whitelist: [str], blacklist: [str]):
        self._whitelist = whitelist
        self._blacklist = blacklist

    def should_send(self, event_name: str):
        if event_name in self._blacklist:
            logging.getLogger('root').debug("{}: Event “{}” would be sent but it is blacklisted.".format(
                self.__class__.__name__, event_name
            ))
            return False

        if len(self._whitelist) > 0 and event_name not in self._whitelist:
            logging.getLogger('root').debug("{}: Event “{}” would be sent but it is not whitelisted.".format(
                self.__class__.__name__, event_name
            ))
            return False

        return True


class CanNotify(ABC):
    """ Interface for classes that can notify """

    def get_name(self):
        pass

    def notify(self, event: str, message: str):
        pass


class NotifierBag:
    """ Data class containing all available Notifiers """

    _bag: {str: CanNotify} = {}

    def add(self, notifier: CanNotify):
        self._bag[notifier.get_name()] = notifier

    def get(self, notifier_name: str):
        if notifier_name not in self._bag:
            return None

        return self._bag[notifier_name]

    def get_all(self):
        return self._bag


class Notifier:
    """ Handles all kind of notifications """

    AGENT_INSTALLED = 'AgentInstalled'
    POST_LAUNCH_SCRIPTS_UPDATED = 'PostLaunchScriptsUpdated'
    REPLICATION_DONE = 'ReplicationDone'
    TEST_TARGETS_READY = 'TestTargetsReady'
    CUTOVER_TARGETS_READY = 'CutoverTargetsReady'

    AGENT_INSTALLED_MESSAGE = 'The CloudEndure agents are now installed for the {} project.'
    POST_LAUNCH_SCRIPTS_UPDATED_MESSAGE = 'The post launch scripts has been copied on the servers of the {} project.'
    REPLICATION_DONE_MESSAGE = 'The initial replication for all the servers in the {} project is done.'
    TEST_TARGETS_READY_MESSAGE = 'Test targets of the {} project are up and running.'
    CUTOVER_TARGETS_READY_MESSAGE = 'Cutover targets of the {} project are up and running.'

    ALL_EVENTS = {
        AGENT_INSTALLED: AGENT_INSTALLED_MESSAGE,
        POST_LAUNCH_SCRIPTS_UPDATED: POST_LAUNCH_SCRIPTS_UPDATED_MESSAGE,
        REPLICATION_DONE: REPLICATION_DONE_MESSAGE,
        TEST_TARGETS_READY: TEST_TARGETS_READY_MESSAGE,
        CUTOVER_TARGETS_READY: CUTOVER_TARGETS_READY_MESSAGE,
    }

    _notifier_bag: NotifierBag = None
    _enabled_notifiers: [str] = []

    def __init__(self, config: dict):
        # Don't forget to add any new Notifier implementation to the Notifier bag.
        # This is because we don't have a dependency injection framework
        self._notifier_bag = NotifierBag()
        self._notifier_bag.add(
            TeamsNotifier(
                config[TeamsNotifier.NAME]['webhook_urls'],
                config[TeamsNotifier.NAME]['event_whitelist'],
                config[TeamsNotifier.NAME]['event_blacklist'],
            )
        )
        self._notifier_bag.add(NullNotifier())

        self._enabled_notifiers = config['enabled_notifiers']

    def notify(self, event: str, message: str):
        if event not in self.ALL_EVENTS:
            logging.getLogger('error').error(
                '{}: “{}” is not a authorized event. Cancelling notifications.'.format(self.__class__.__name__, event)
            )
            return

        self._do_notify(event, message)

    def _do_notify(self, event: str, message: str):
        tasks = []
        for notifier_name, notifier in self._notifier_bag.get_all().items():
            if notifier_name not in self._enabled_notifiers:
                continue

            task = Thread(target=notifier.notify, args=[event, message])
            task.start()
            tasks.append(task)

        for task in tasks:
            task.join()


class NullNotifier(CanNotify):
    """ Dummy Notifier that does nothing (example) """

    NAME = 'null'

    def get_name(self):
        return self.NAME

    def notify(self, event: str, message: str):
        logging.getLogger('root').debug("{}: Notify “{}” with message: “{}”.".format(
            self.__class__.__name__, event, message
        ))

        # Allows to test concurrency
        time.sleep(0.1)


class TeamsNotifier(CanNotify):
    """ Handles notification to Microsoft Teams """

    NAME = 'teams'

    _webook_urls: [str] = []
    _send_event_decider: SendEventDecider = None

    def __init__(self, webhook_urls: [str], event_whitelist: [str], event_blacklist: [str]):
        self._send_event_decider = SendEventDecider(whitelist=event_whitelist, blacklist=event_blacklist)
        self._webook_urls = webhook_urls

    def get_name(self):
        return self.NAME

    def notify(self, event: str, message: str):
        if not self._send_event_decider.should_send(event):
            return

        if len(self._webook_urls) > 10:
            logging.getLogger('root').warning(
                '{}: More than 10 webhooks were configured. Be cautious of rate limits.'.format(self.__class__.__name__)
            )

        tasks = []
        for webhook_url in self._webook_urls:
            if not validators.url(webhook_url):
                logging.getLogger('error').error(
                    '{}: “{}” is not a valid URL.'.format(self.__class__.__name__, webhook_url)
                )

            task = Thread(target=self._do_notify, args=[webhook_url, message])
            task.start()
            tasks.append(task)

        for task in tasks:
            task.join()

    def _do_notify(self, webhook_url: str, message: str):
        logging.getLogger('root').debug("{}: Sending message: {}\n to: {}".format(
            self.__class__.__name__, message, webhook_url
        ))

        teams_connector = pymsteams.connectorcard(webhook_url)
        teams_connector.text(message)
        teams_connector.send()


class SMTPNotifier(CanNotify):
    """ Handles notification by email with SMTP """

    NAME = 'smtp'

    _destination_emails: [str] = []
    _send_event_decider: SendEventDecider = None
    _needs_authentication: bool = None
    _username: bool = None
    _password: bool = None
    _host: str = None
    _port: int = None
    _tls: bool = None

    def __init__(self, config: dict):

        self._needs_authentication = self._get_config_value(
            config, 'needs_authentication', False
        )
        self._host = self._get_config_value(
            config, 'host', '127.0.0.1', 'MF_NOTIFIER_SMTP_HOST', '[Notify SMTP] Host'
        )
        self._port = self._get_config_value(
            config, 'port', 465, 'MF_NOTIFIER_SMTP_PORT', '[Notify SMTP] Port'
        )
        self._tls = self._get_config_value(
            config, 'tls', True, 'MF_NOTIFIER_SMTP_TLS', '[Notify SMTP] Use TLS'
        )
        self._destination_emails = self._get_config_value(
            config, 'destination_emails', []
        )
        self._event_whitelist = config[self.NAME]['event_whitelist']
        self._event_blacklist = config[self.NAME]['event_blacklist']
        self._send_event_decider = SendEventDecider(whitelist=self._event_whitelist, blacklist=self._event_blacklist)

        if self._needs_authentication:
            self._username = EnvironmentVariableFetcher.fetch(['MF_NOTIFIER_SMTP_USERNAME'], '[Notify SMTP] Username')
            self._password = EnvironmentVariableFetcher.fetch(['MF_NOTIFIER_SMTP_PASSWORD'], '[Notify SMTP] Password')

    def get_name(self):
        return self.NAME

    def notify(self, event: str, message: str):
        if not self._send_event_decider.should_send(event):
            return

        if not self._check_destination_emails():
            return

        email_message = EmailMessage()
        email_message.set_content(message + "\n\nThis message was sent by {}.".format(BRAND))

        email_message['Subject'] = '[' + BRAND + '] ' + message
        email_message['To'] = self._destination_emails.split(';')
        if self._needs_authentication:
            email_message['From'] = self._username
        else:
            email_message['From'] = BRAND

        if self._tls:
            smtpclient = smtplib.SMTP_SSL(self._host, self._port)
        else:
            smtpclient = smtplib.SMTP(self._host, self._port)

        if self._needs_authentication:
            smtpclient.login(self._username, self._password)

        smtpclient.send_message(email_message)
        smtpclient.quit()

    def _do_notify(self, webhook_url: str, message: str):
        logging.getLogger('root').debug("{}: Sending message: {}\n to: {}".format(
            self.__class__.__name__, message, webhook_url
        ))

        teams_connector = pymsteams.connectorcard(webhook_url)
        teams_connector.text(message)
        teams_connector.send()

    def _get_config_value(
            self, config: dict, key: str, default, env_var_name: str = None, env_var_description: str = None
    ):
        value = None
        if key not in config or config[key] is None or config[key] == '' and env_var_name is not None:
            value = EnvironmentVariableFetcher.fetch([env_var_name], env_var_description)

        if value is None:
            value = config[key]

        if not value:
            return default

        return value

    def _check_destination_emails(self):
        for email in self._destination_emails:
            if not validators.email(email):
                logging.getLogger('error').error(
                    '{}: “{}” is not a valid email. Cancelling notifications.'.format(self.__class__.__name__, email)
                )
                return False

        return True


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
