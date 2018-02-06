import ftrack_api


def thumbnail_update(event):
    '''Update thumbnails automatically'''

    for entity in event['data'].get('entities', []):

        # update created task thumbnail with first parent thumbnail
        if entity['entityType'] == 'task' and entity['action'] == 'add':

            task = session.get('TypedContext', entity['entityId'])
            parent = task['parent']

            if parent.get('thumbnail') and not task.get('thumbnail'):
                task['thumbnail'] = parent['thumbnail']
                print('Updated thumbnail on %s/%s' % (parent['name'],
                                                            task['name']))

        # Update task thumbnail from published version
        if entity['entityType'] == 'assetversion' and entity['action'] == 'encoded':

            version = session.get('AssetVersion', entity['entityId'])
            thumbnail = version.get('thumbnail')
            task = version['task']

            if thumbnail:
                task['thumbnail'] = thumbnail
                task['parent']['thumbnail'] = thumbnail
                print(
                    'Updating thumbnail for task and shot {}'.format(task['name']))

        session.commit()

###############################################################################


session = ftrack_api.Session()
session.event_hub.subscribe(
    'topic=ftrack.update', thumbnail_update
)
session.event_hub.wait()
