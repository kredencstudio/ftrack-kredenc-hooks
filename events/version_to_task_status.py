import ftrack_api
import datetime

def version_to_task_status(event):
    '''Push version status to task'''

    # import ftrack_api as local session
    session = ftrack_api.Session()
    # ----------------------------------

    # start of event procedure ----------------------------------
    for entity in event['data'].get('entities', []):
        # Filter non-assetversions
        if (entity['entityType'] == 'assetversion'
                and 'statusid' in entity['keys']):

            now = datetime.datetime.now()
            print ("\n Current date and time : {}".format(now.strftime("%Y-%m-%d %H:%M:%S")))

            version = session.get('AssetVersion', entity['entityId'])
            version_status = session.get('Status',
                                         entity['changes']['statusid']['new'])
            task_status = version_status
            task = version['task']

            status_to_set = None
            # Filter to versions with status change to "render complete"
            if version_status['name'].lower() == 'reviewed':
                status_to_set = 'Change requested'
            elif version_status['name'].lower() == 'approved':
                status_to_set = 'Complete'
                if task['type']['name'] == 'Lighting':
                    status_to_set = 'To render'
            elif version_status['name'].lower() == 'data':
                continue

            if status_to_set is not None:
                task_status = session.query(
                    'Status where name is "{}"'.format(status_to_set)).one()

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
                    print('task: {} status couldnt be set: {}'.format(path, e))
                    # print '{} status couldnt be set: {}'
                else:
                    print('task:{} updated to "{}"'.format(path,
                                                      task_status['name']))
    # end of event procedure ----------------------------------

    # remove ftrack_api ----------------
    # del ftrack_api
    # ----------------------------------
