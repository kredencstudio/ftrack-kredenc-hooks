import logging
import ftrack_api

logging.basicConfig()
logger = logging.getLogger()


def version_to_task_status(event):
    '''Push version status to task'''

    for entity in event['data'].get('entities', []):
        # Filter non-assetversions
        if (entity['entityType'] == 'assetversion' and
                'statusid' in entity['keys']):

            version = session.get('AssetVersion', entity['entityId'])
            version_status = version['status']
            task_status = version_status
            task = version['task']

            status_to_set = None
            # Filter to versions with status change to "render complete"
            if version_status['name'].lower() == 'reviewed':
                status_to_set = 'change requested'

            if version_status['name'].lower() == 'approved':
                status_to_set = 'complete'
                if task['type']['name'] == 'Lighting':
                    status_to_set = 'to render'

            if status_to_set:
                task_status = session.query(
                    'Status where name is "{}"'.format(status_to_set)).one()
            #
            # Proceed if the task status was set
            if task_status:
                # Get path to task
                path = task['name']
                for p in task['ancestors']:
                    path = p['name'] + '/' + path

                # Setting task status
                try:
                    task['status'] = task_status
                    session.commit()
                except Exception as e:
                    logger.info(
                        '{} status couldnt be set: {}'.format(path, e))
                    # print '{} status couldnt be set: {}'
                else:
                    logger.info('{} updated to "{}"'.format(
                        path, task_status['name']))
                    # print '{} updated to "{}"'


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.update', version_to_task_status
    )


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    session = ftrack_api.Session()
    session.event_hub.subscribe(
        'topic=ftrack.update', version_to_task_status
    )
    logger.info('Listening for events. Use Ctrl-C to abort.')
    session.event_hub.wait()
