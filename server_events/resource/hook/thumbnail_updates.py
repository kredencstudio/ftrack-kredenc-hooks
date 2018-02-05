import logging
import ftrack_api

logging.basicConfig()
logger = logging.getLogger()


def thumbnail_update(event):
    '''Update thumbnails automatically'''

    for entity in event['data'].get('entities', []):

        # update created task thumbnail with first parent thumbnail
        if entity['entityType'] == 'task' and entity['action'] == 'add':

            task = session.get('TypedContext', entity['entityId'])
            parent = task['parent']

            if parent.get('thumbnail') and not task.get('thumbnail'):
                task['thumbnail'] = parent['thumbnail']
                logger.info('Updated thumbnail on %s/%s' % (parent['name'],
                                                            task['name']))

        # Update task thumbnail from published version
        if entity['entityType'] == 'assetversion' and entity['action'] == 'encoded':

            version = session.get('AssetVersion', entity['entityId'])
            thumbnail = version.get('thumbnail')
            task = version['task']

            if thumbnail:
                task['thumbnail'] = thumbnail
                task['parent']['thumbnail'] = thumbnail
                logger.info(
                    'Updating thumbnail for task and shot {}'.format(task['name']))

        session.commit()


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.update', thumbnail_update
    )


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    session = ftrack_api.Session()
    session.event_hub.subscribe(
        'topic=ftrack.update', thumbnail_update
    )
    logger.info('Listening for events. Use Ctrl-C to abort.')
    session.event_hub.wait()
