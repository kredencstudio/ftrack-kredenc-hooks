# import ftrack_api


def version_to_task_status(event, session):
    '''Push version status to task'''

    for entity in event['data'].get('entities', []):
        # Filter non-assetversions
        if (entity['entityType'] == 'assetversion' and
                'statusid' in entity['keys']):

            version = session.get('AssetVersion', entity['entityId'])
            version_status = session.get('Status', entity['changes']['statusid']['new'])
            task_status = version_status
            task = version['task']
            print('version status: {}'.format(version_status['name']))

            status_to_set = None
            # Filter to versions with status change to "render complete"
            if version_status['name'].lower() == 'reviewed':
                status_to_set = 'Change requested'

            if version_status['name'].lower() == 'approved':
                status_to_set = 'Complete'
                if task['type']['name'] == 'Lighting':
                    status_to_set = 'To render'
            print('status to set: {}'.format(status_to_set))

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
                    print('{} status couldnt be set: {}'.format(path, e))
                    # print '{} status couldnt be set: {}'
                else:
                    print('{} updated to "{}"'.format(
                        path, task_status['name']))
                    # print '{} updated to "{}"'



session = ftrack_api.Session()
session.event_hub.subscribe(
    'topic=ftrack.update', version_to_task_status
)
session.event_hub.wait()
