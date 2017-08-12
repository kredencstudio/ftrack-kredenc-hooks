import sys
import argparse
import logging
import getpass

import ftrack


class SetVersion(ftrack.Action):
    '''Custom action.'''

    #: Action identifier.
    identifier = 'version.set'

    #: Action label.
    label = 'Version Set'


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
        '''Return true if the selection is valid'''
        if len(selection) == 1 and selection[0]['entityType'] == 'assetversion':
            self.logger.info('Selection is valid')
            return True
        else:
            self.logger.info('Selection is _not_ valid')
            return False

    def discover(self, event):
        ''' Return action config if validation passed'''
        selection = event['data'].get('selection', [])
        self.logger.info(u'Discovering action with selection: {0}'.format(selection))
        if not self.validateSelection(selection):
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
            }]
        }


    def launch(self, event):
        if 'values' in event['data']:
            # Do something with the values or return a new form.
            values = event['data']['values']

            data = event['data']
            selection = data.get('selection', [])
            version = ftrack.AssetVersion(selection[0]['entityId'])

            success = True
            msg = 'Increased version number.'

            if not values['version_number']:
                success = False
                msg = 'No number was submitted.'
            else:
                if int(values['version_number']) <= 0:
                    success = False
                    msg = 'Negative or zero is not valid.'
                else:
                    version.set('version', int(values['version_number']))

            return {
                'success': success,
                'message': msg
            }

        return {
            'items': [
                {
                    'label': 'Version number',
                    'type': 'number',
                    'name': 'version_number'
                }
            ]
        }


def register(registry, **kw):
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    '''Register action. Called when used as an event plugin.'''
    logging.basicConfig(level=logging.INFO)
    action = SetVersion()
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
    action = SetVersion()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
