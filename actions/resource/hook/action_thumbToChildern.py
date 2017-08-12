# :coding: utf-8
# :copyright: Copyright (c) 2015 Milan Kolar

import sys
import argparse
import logging
import getpass

import ftrack


class ThumbToChildren(ftrack.Action):
    '''Custom action.'''

    #: Action identifier.
    identifier = 'thumb.to.children'

    #: Action label.
    label = 'Thumbnail to Children'

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
                'icon': "https://cdn3.iconfinder.com/data/icons/transfers/100/239322-download_transfer-128.png"
            }]
        }


    def launch(self, event):
        '''Callback method for action.'''
        selection = event['data'].get('selection', [])
        self.logger.info(u'Launching action with selection {0}'.format(selection))

        job = ftrack.createJob(description="Push thumbnails to Childrens", status="running")

        try:
            ftrack.EVENT_HUB.publishReply(
                event,
                data={
                    'success': True,
                    'message': 'Created job for updating thumbnails!'
                }
            )

            for entity in selection:


                entity = ftrack.Task(entity['entityId'])
                tasks = entity.getTasks()

                thumbid = entity.get('thumbid')

                for task in tasks:
                    if thumbid:
                        task.set('thumbid', value=thumbid)

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
    '''Register action. Called when used as an event plugin.'''
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return

    logging.basicConfig(level=logging.INFO)
    action = ThumbToChildren()
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
    action = ThumbToChildren()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
