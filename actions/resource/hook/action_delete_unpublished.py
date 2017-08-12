import sys
import argparse
import logging
import getpass

import ftrack


class VersionsCleanup(ftrack.Action):
    '''Custom action.'''

    #: Action identifier.
    identifier = 'versions.cleanup'

    #: Action label.
    label = 'Versions cleanup'


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

        Legacy plugins can only be started from a single Task.

        '''
        if len(selection) == 0 or selection[0]['entityType'] != 'assetversion':
            self.logger.info('Selection is not valid')
            return False

        return True

    def discover(self, event):
        '''Return action config if triggered on a single selection.'''

        # If selection contains more than one item return early since
        # this action will only handle a single version.
        selection = event['data'].get('selection', [])

        if not self.validateSelection(selection):
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
            }]
        }

    def launch(self, event):

        selection = event['data'].get('selection', [])

        version = ftrack.AssetVersion(selection[0]['entityId'])
        asset = version.getAsset()
        for v in asset.getVersions():
            if not v.get('ispublished'):
                v.delete()

        return {
            'success': True,
            'message': 'removed hidden versions'
        }


def register(registry, **kw):
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    '''Register action. Called when used as an event plugin.'''
    logging.basicConfig(level=logging.INFO)
    action = VersionsCleanup()
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
    action = VersionsCleanup()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
