import ftrack_api


def version_to_task_status(event):
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

            if status_to_set is not None:
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


def get_next_task(task):
        parent = task['parent']
        # tasks = parent['tasks']
        tasks = parent['children']

        def sort_types(types):
            data = {}
            for t in types:
                data[t] = t.get('sort')

            data = sorted(data.items(), key=operator.itemgetter(1))
            results = []
            for item in data:
                results.append(item[0])
            return results

        types_sorted = sort_types(session.query('Type'))
        next_types = None
        for t in types_sorted:
            if t['id'] == task['type_id']:
                next_types = types_sorted[(types_sorted.index(t) + 1):]

        for nt in next_types:
            for t in tasks:
                if nt['id'] == t['type_id']:
                    return t

        return None


def new_task_update(event):
    '''Set next task to ready when previous task is completed.'''

    for entity in event['data'].get('entities', []):

        if (entity['entityType'] == 'task' and
                'statusid' in entity['keys']):

            task = session.get('Task', entity['entityId'])

            status = session.get('Status', entity['changes']['statusid']['new'])
            state = status['state']['name']

            next_task = get_next_task(task)

            # Setting next task to NOT STARTED, if on NOT READY
            if next_task and state == 'Done':
                if next_task['status']['name'].lower() == 'not ready':

                    # Get path to task
                    path = task['name']
                    for p in task['ancestors']:
                        path = p['name'] + '/' + path

                    # Setting next task status
                    try:
                        status_to_set = session.query(
                            'Status where name is "{}"'.format('Ready')).one()
                        next_task['status'] = status_to_set
                    except Exception as e:
                        print '{} status couldnt be set: {}'.format(path, e)
                    else:
                        print '{} updated to "Ready"'.format(path)

            session.commit()


def file_version_statuses(event):
    '''Set new version status to data if version matches given types'''

    for entity in event['data'].get('entities', []):

        # Filter to new assetversions
        if (entity['entityType'] == 'assetversion' and
                entity['action'] == 'add'):

            version = session.get('AssetVersion', entity['entityId'])
            asset_type = version['asset']['type']['name']
            file_status = session.query(
                'Status where name is "{}"'.format('data')).one()

            # Setting task status
            try:
                if asset_type.lower() in ['cam', 'cache', 'rig', 'scene']:
                    version['status'] = file_status
            except Exception as e:
                print 'status couldnt be set: {}'.format(e)
            else:
                print 'updated to "{}"'.format(file_status['name'])

        session.commit()


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


def radio_buttons(event):
    '''Provides a readio button behaviour to any bolean attribute in
       radio_button group.'''

    for entity in event['data'].get('entities', []):

        if entity['entityType'] == 'assetversion':

            group = session.query(
                'CustomAttributeGroup where name is "radio_button"').one()
            radio_buttons = []
            for g in group['custom_attribute_configurations']:
                radio_buttons.append(g['key'])

            for key in entity['keys']:
                if (key in radio_buttons and entity['changes'] is not None):
                    if entity['changes'][key]['new'] == '1':
                        version = session.get(
                            'AssetVersion', entity['entityId'])
                        asset = session.get('Asset', entity['parentId'])
                        for v in asset['versions']:
                            if version is not v:
                                v['custom_attributes'][key] = 0

        session.commit()


session = ftrack_api.Session()

session.event_hub.subscribe(
    'topic=ftrack.update', version_to_task_status
)
session.event_hub.subscribe(
    'topic=ftrack.update', new_task_update
)
session.event_hub.subscribe(
    'topic=ftrack.update', file_version_statuses
)
session.event_hub.subscribe(
    'topic=ftrack.update', thumbnail_update
)
session.event_hub.subscribe(
    'topic=ftrack.update', radio_buttons
)


session.event_hub.wait()
