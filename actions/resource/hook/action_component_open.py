# :coding: utf-8
# :copyright: Copyright (c) 2015 Milan Kolar

import sys
import argparse
import logging
import getpass
import subprocess
import os

import ftrack


class ComponentOpen(ftrack.Action):
    '''Custom action.'''

    #: Action identifier.
    identifier = 'component.open'

    #: Action label.
    label = 'Open File'


    def __init__(self):
        '''Initialise action handler.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def register(self):
        '''Register action.'''
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

        if len(selection) == 1 and selection[0]['entityType'] == 'Component':
            self.logger.info('Selection is valid')
            return True
        else:
            self.logger.info('Selection is _not_ valid')
            return False



    def discover(self, event):
        '''Return action config if triggered on a single selection.'''
        selection = event['data'].get('selection', [])
        self.logger.info(u'Discovering action with selection: {0}'.format(selection))
        if not self.validateSelection(selection):
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
                'icon': 'https://cdn4.iconfinder.com/data/icons/rcons-application/32/application_go_run-256.png',
            }]
        }


    def launch(self, event):

        data = event['data']
        selection = data.get('selection', [])
        self.logger.info(selection)

        component = ftrack.Component(selection[0]['entityId'])
        path = component.getFilesystemPath()
        path = os.path.abspath(path)

        if sys.platform == 'win32':
            subprocess.Popen('explorer "%s"' % path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', path])
        else:  # linux
            try:
                subprocess.Popen(['xdg-open', path])
            except OSError:
                raise OSError('unsupported xdg-open call??')


        return {
            'success': True,
            'message': 'Component Opened'
        }


def register(registry, **kw):
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    '''Register action. Called when used as an event plugin.'''
    logging.basicConfig(level=logging.INFO)
    action = ComponentOpen()
    action.register()


def main(arguments=None):
    '''Set up logging and register action.'''
    if arguments is None:
        arguments = []

    parser = argparse.ArgumentParser()
    # Allow setting of logging level from arguments.
    loggingLevels = {}
    for level in (
        logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING,
        logging.ERROR, logging.CRITICAL
    ):
        loggingLevels[logging.getLevelName(level).lower()] = level

    parser.add_argument(
        '-v', '--verbosity',
        help='Set the logging output verbosity.',
        choices=loggingLevels.keys(),
        default='info'
    )
    namespace = parser.parse_args(arguments)

    '''Register action and listen for events.'''
    logging.basicConfig(level=loggingLevels[namespace.verbosity])

    ftrack.setup()
    action = ComponentOpen()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
