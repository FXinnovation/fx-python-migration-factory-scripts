#!/usr/bin/env python3

import logging
from abc import ABC
import pymsteams
import asyncio
import validators


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

    async def notify(self, event: str, message: str):
        pass


class NotifierBag:
    """ Data class containing all available Notifiers """

    _bag: {str: CanNotify} = {}

    def add(self, notifier: CanNotify):
        self._bag[notifier.get_name()] = notifier

    def get(self, notifier_name: str):
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
            TeamsNotifier(config[TeamsNotifier.NAME]['webhook_urls'], config[TeamsNotifier.NAME]['event_whitelist'])
        )
        self._notifier_bag.add(NullNotifier())

        self._enabled_notifiers = config['enabled_notifiers']

    def notify(self, event: str, message: str):
        if event not in self.ALL_EVENTS:
            logging.getLogger('error').error(
                '{}: “{}” is not a authorized event. Cancelling notifications.'.format(self.__class__.__name__, event)
            )
            return

        asyncio.run(self._do_notify(event, message))

    async def _do_notify(self, event: str, message: str):
        tasks = []
        for notifier_name, notifier in self._notifier_bag.get_all().items():
            if notifier_name not in self._enabled_notifiers:
                continue

            tasks.append(asyncio.create_task(notifier.notify(event, message)))

        for task in tasks:
            await task


class NullNotifier(CanNotify):
    """ Dummy Notifier that does nothing (example) """

    NAME = 'null'

    def get_name(self):
        return self.NAME

    async def notify(self, event: str, message: str):
        await asyncio.create_task(self._do_notify(event, message))

    async def _do_notify(self, event: str, message: str):
        logging.getLogger('root').debug("{}: Notify “{}” with message: “{}”.".format(
            self.__class__.__name__, event, message
        ))

        return await asyncio.sleep(0.1)


class TeamsNotifier(CanNotify):
    """ Handles notification to Microsoft Teams """

    NAME = 'teams'

    _webook_urls: [str] = []
    _send_event_decider: SendEventDecider = None

    def __init__(self, webhook_urls: [str], event_whitelist: [str], event_blacklist: [str]):
        self._event_decider = SendEventDecider(whitelist=event_whitelist, blacklist=event_blacklist)
        self._webook_urls = webhook_urls

    def get_name(self):
        return self.NAME

    async def notify(self, event: str, message: str):
        if not self._send_event_decider.should_send():
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

            tasks.append(asyncio.create_task(self._do_notify(webhook_url, message)))

        for task in tasks:
            await task

    async def _do_notify(self, webhook_url: str, message: str):
        logging.getLogger('root').debug("{}: Sending message: {}\n to: {}".format(
            self.__class__.__name__, message, webhook_url
        ))

        teams_connector = pymsteams.connectorcard(webhook_url)
        teams_connector.text(message)
        teams_connector.send()


if __name__ == '__main__':
    print("This file is a library file. It cannot be called directly.")
