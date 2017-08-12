# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass
import sys
import pprint
import logging
import os

import ftrack
import ftrack_connect.application


class LaunchApplicationAction(object):
    '''Discover and launch action.'''

    identifier = 'ftrack-connect-launch-apps'

    def __init__(self, applicationStore, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchApplicationAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.applicationStore = applicationStore
        self.launcher = launcher

    def register(self):
        '''Register discover actions on logged in user.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

    def validateSelection(self, selection):
        '''Return true if the selection is valid.
        '''
        self.logger.info(selection)

        return True

    def validateArtist(self, selection):
        '''Return true if the artist matches system user.
        '''
        # filter on artist attribute
        user = os.getenv('systemuser')
        self.logger.info('USER: {}'.format(user))

        taskid = selection[0].get('entityId')
        task = ftrack.Task(taskid)
        artist = task.get('artist')
        self.logger.info('ARTIST: {}'.format(artist))

        if user != artist:
            return False

        return True

    def discover(self, event):
        '''Return discovered applications.'''
        items = []
        data = event['data']
        selection = data.get('selection', [])

        if not self.validateSelection(selection):
            return

        if not self.validateArtist(selection):
            return

        applications = self.applicationStore.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            applicationIdentifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'variant': application.get('variant', None),
                'icon': application.get('icon', 'default'),
                'applicationIdentifier': applicationIdentifier
            })

        return {
            'items': items
        }

    def launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        items = []
        data = event['data']
        selection = data.get('selection', [])

        if not self.validateArtist(selection):
            return

        applicationIdentifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()

        self.logger.info("YEAH")

        # Here you can modify the context setting extra data etc
        # which can be retrieved by parsing the FTRACK_CONNECT_EVENT
        # environment variable in the application.

        return self.launcher.launch(
            applicationIdentifier, context
        )


class ApplicationStore(ftrack_connect.application.ApplicationStore):

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name version',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._searchFilesystem(
                expression=prefix + [
                    'Python*', 'Python.app'
                ],
                label='Python',
                variant='{version}',
                applicationIdentifier='python_{version}',
                icon='http://www.unixstickers.com/image/data/stickers/python/python.sh.png'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._searchFilesystem(
                expression=[
                    'C:\\', 'Python*', 'python.exe'
                ],
                label='Python',
                variant='{version}',
                applicationIdentifier='python_{version}',
                icon='http://www.unixstickers.com/image/data/stickers/python/python.sh.png'
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


def register(registry, **kw):
    '''Register hooks.'''
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    # Create store containing applications.
    applicationStore = ApplicationStore()

    # Create a launcher with the store containing applications.
    launcher = ftrack_connect.application.ApplicationLauncher(
        applicationStore
    )

    # Create action and register to respond to discover and launch actions.
    action = LaunchApplicationAction(applicationStore, launcher)
    action.register()
