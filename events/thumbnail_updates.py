import ftrack_api
import datetime


def thumbnail_updates(event):
    '''Update thumbnails automatically'''

    # import ftrack_api as local session
    session = ftrack_api.Session()
    # ----------------------------------

    # start of event procedure ----------------------------------
    for entity in event['data'].get('entities', []):

        # update created task thumbnail with first parent thumbnail
        if entity['entityType'] == 'task' and entity['action'] == 'add':
            now = datetime.datetime.now()
            print ("\n Current date and time : {}".format(now.strftime("%Y-%m-%d %H:%M:%S")))

            task = session.get('TypedContext', entity['entityId'])
            parent = task['parent']

            if parent.get('thumbnail') and not task.get('thumbnail'):
                task['thumbnail'] = parent['thumbnail']
                print('Updated thumbnail on %s/%s' % (parent['name'],
                                                      task['name']))

        # Update task thumbnail from published version
        if entity['entityType'] == 'assetversion' and entity['action'] == 'encoded':
            now = datetime.datetime.now()
            print ("\n Current date and time : {}".format(now.strftime("%Y-%m-%d %H:%M:%S")))

            version = session.get('AssetVersion', entity['entityId'])
            thumbnail = version.get('thumbnail')
            task = version['task']

            if thumbnail:
                task['thumbnail'] = thumbnail
                task['parent']['thumbnail'] = thumbnail
                print('Updating thumbnail for task and shot {}'.format(
                    task['name']))

        session.commit()
    # end of event procedure ----------------------------------

    # remove ftrack_api ----------------
    # del ftrack_api
    # ----------------------------------
