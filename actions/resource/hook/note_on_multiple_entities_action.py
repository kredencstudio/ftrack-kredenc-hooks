# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import sys
import argparse
import logging
import threading
import getpass
import ftrack


def async(fn):
    '''Run *fn* asynchronously.'''
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class NoteOnMultipleEntitiesAction(ftrack.Action):
    '''Action to write note on multiple entities.'''

    #: Action identifier.
    identifier = 'note-on-multiple-entities'

    #: Action label.
    label = 'Write notes'

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
        selection = data.get('selection', [])

        if not self.validateSelection(selection):
            return

        entityType = selection[0]['entityType']
        # If selection contains more than one item return early since
        # this action can only handle a single version.
        if entityType in ['reviewsession', 'Component', 'assetVersion']:
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
                'icon':"http://www.sportswurlz.com/pix/pub/icos/edit2.png"
            }]
        }

    @async
    def createNotes(self, selection, text, category):
        entityCount = len(selection)
        logging.info('Creating notes on {0} entities'.format(entityCount))

        job = ftrack.createJob(
            'Creating notes ({0} of {1})'.format(1, entityCount), 'running'
        )
        try:
            for index, item in enumerate(selection, start=1):
                entityType = item['entityType']
                entityId = item['entityId']
                entity = None

                if index != 1:
                    job.setDescription('Creating notes ({0} of {1})'.format(index, entityCount))

                if entityType == 'show':
                    entity = ftrack.Project(entityId)
                elif entityType == 'task':
                    entity = ftrack.Task(entityId)
                elif entityType == 'assetversion':
                    entity = ftrack.AssetVersion(entityId)

                if not entity:
                    logging.warning(
                        u'Entity ({0}, {1}) not a valid type, skipping..'
                        .format(entityId, entityType)
                    )

                entity.createNote(text, category)
        except Exception:
            job.setStatus('failed')

        logging.info('Note creation completed.')
        job.setStatus('done')

    def launch(self, event):
        '''Callback method for action.'''
        data = event['data']
        logging.info(u'Launching action with data: {0}'.format(data))

        selection = data.get('selection', [])
        if not selection:
            return {'success': False}

        if 'values' in data:
            text = data['values'].get('note_text')
            category = data['values'].get('note_category', 'auto')
            self.createNotes(selection, text, category)

            return {
                'success': True,
                'message': 'Started creating notes'
            }

        options = [
            {'label': category.getName(), 'value': category.getId()}
            for category in ftrack.getNoteCategories()
        ]
        options.insert(0, {'label': 'Default', 'value': 'auto'})


        return {
            'items': [
                {
                    'value': '## Writing note on **{0}** items. ##'.format(len(selection)),
                    'type': 'label'
                }, {
                    'label': 'Content',
                    'name': 'note_text',
                    'value': '',
                    'type': 'textarea'
                }, {
                    'label': 'Note category',
                    'type': 'enumerator',
                    'name': 'note_category',
                    'value': 'auto',
                    'data': options
                }
            ]
        }


def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'note-on-multiple-entities'
    )

    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return

    # Validate that registry is an instance of ftrack.Registry. If not,
    # assume that register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(registry, ftrack.Registry):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack.Registry instance.'.format(registry)
        )
        return

    action = NoteOnMultipleEntitiesAction()
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

    # Set up basic logging
    logging.basicConfig(level=loggingLevels[namespace.verbosity])

    # Subscribe to action.
    ftrack.setup()
    action = NoteOnMultipleEntitiesAction()
    action.register()

    # Wait for events
    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
