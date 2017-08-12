import sys
import argparse
import logging
import getpass
import ftrack


class AssetDelete(ftrack.Action):
    '''Custom action.'''

    #: Action identifier.
    identifier = 'asset.delete'

    #: Action label.
    label = 'Asset Delete'


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

        if len(selection) != 1:
            return False

        entity = selection[0]
        task = ftrack.Task(entity['entityId'])

        if task.getObjectType() not in ['Shot', 'Asset Build']:
            return False

        return True


    def discover(self, event):
        '''Return action config if triggered on a single selection.'''
        selection = event['data'].get('selection', [])

        self.logger.info(
            u'Discovering action with selection: {0}'.format(selection))

        if not self.validateSelection(selection):
            return

        # If selection contains more than one item return early since
        # this action will only handle a single version.


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

            success = True
            msg = 'Asset deleted.'

            asset = ftrack.Asset(values['asset'])
            asset.delete()

            return {
                'success': success,
                'message': msg
            }

        data = []
        shot = ftrack.Task(event['data']['selection'][0]['entityId'])
        for asset in shot.getAssets():
            if asset.getName():
                data.append({'label': asset.getName(), 'value': asset.getId()})
            else:
                data.append({'label': 'None', 'value': asset.getId()})

        return {
            'items': [
                {
                    'label': 'Asset',
                    'type': 'enumerator',
                    'name': 'asset',
                    'data': data
                }
            ]
        }


def register(registry, **kw):
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    '''Register action. Called when used as an event plugin.'''
    logging.basicConfig(level=logging.INFO)
    action = AssetDelete()
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
    action = AssetDelete()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
