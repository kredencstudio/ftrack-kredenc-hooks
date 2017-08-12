# :coding: utf-8
# :copyright: Copyright (c) 2015 Milan Kolar

import sys
import argparse
import logging
import getpass

import ftrack


class ThumbToParent(ftrack.Action):
    '''Custom action.'''

    #: Action identifier.
    identifier = 'thumb.to.parent'

    #: Action label.
    label = 'Thumbnail to Parent'

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
        if len(selection) > 0:
            if selection[0]['entityType'] in ['assetversion', 'task']:
                return True

        return False

    def discover(self, event):
        '''Return action config if triggered on asset versions.'''
        selection = event['data'].get('selection', [])
        self.logger.info(u'Discovering action with selection: {0}'.format(selection))

        # validate selection, and only return action if it is valid.
        if not self.validateSelection(selection):
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
                'icon': "https://cdn3.iconfinder.com/data/icons/transfers/100/239419-upload_transfer-512.png"
            }]
        }


    def launch(self, event):
        '''Callback method for action.'''
        selection = event['data'].get('selection', [])
        self.logger.info(u'Launching action with selection {0}'.format(selection))

        job = ftrack.createJob(description="Push thumbnails to parents", status="running")

        try:
            ftrack.EVENT_HUB.publishReply(
                event,
                data={
                    'success': True,
                    'message': 'Created job for updating thumbnails!'
                }
            )

            for entity in selection:

                if entity['entityType'] == 'assetversion':
                    entity = ftrack.AssetVersion(entity['entityId'])
                    try:
                        parent = entity.getTask()
                    except:
                        parent = entity.getParent().getParent()
                elif entity['entityType'] == 'task':
                    entity = ftrack.Task(entity['entityId'])
                    parent = entity.getParent()

                thumbid = entity.get('thumbid')

                if thumbid:
                    parent.set('thumbid', value=thumbid)

            # inform the user that the job is done
            job.setStatus('done')
        except:
            # fail the job if something goes wrong
            job.setStatus('failed')
            raise

        return {
            'success': True,
            'message': 'Created job for updating thumbnails!'
        }



def register(registry, **kw):
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    '''Register action. Called when used as an event plugin.'''
    logging.basicConfig(level=logging.INFO)
    action = ThumbToParent()
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
    action = ThumbToParent()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
