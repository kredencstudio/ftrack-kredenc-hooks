import sys
import argparse
import logging
import os
import getpass

import ftrack


class ClientReviewSort(ftrack.Action):
    '''Custom action.'''

    #: Action identifier.
    identifier = 'client.review.sort'

    #: Action label.
    label = 'Sort Review'


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

        if len(selection) == 0:
            return False

        return True


    def discover(self, event):
        '''Return action config if triggered on a single selection.'''
        data = event['data']

        # If selection contains more than one item return early since
        # this action will only handle a single version.
        selection = data.get('selection', [])

        if not self.validateSelection(selection):
            return

        entityType = selection[0]['entityType']
        if entityType != 'reviewsession':
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
            }]
        }


    def launch(self, event):

        data = event['data']
        selection = data.get('selection', [])
        session = ftrack.ReviewSession(selection[0]['entityId'])
        objs = session.getObjects()

        sort_start = objs[0].get('sort_order')
        names = {}
        for obj in objs:
            names[obj.get('name')] = obj
            if sort_start > obj.get('sort_order'):
                sort_start = obj.get('sort_order')

        names_sorted = sorted(names)
        for key in names_sorted:
            order = sort_start + names_sorted.index(key)
            names[key].set('sort_order', order)

        return {
            'success': True,
            'message': 'Client Review sorted!'
        }


def register(registry, **kw):
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    '''Register action. Called when used as an event plugin.'''
    logging.basicConfig(level=logging.INFO)
    action = ClientReviewSort()
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
    action = ClientReviewSort()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
