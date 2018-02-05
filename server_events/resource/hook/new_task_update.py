import logging
import operator
import ftrack_api

logging.basicConfig()
logger = logging.getLogger()


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
    '''Modify the application environment.'''

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


###############################################################################

# Register in case event will be ran within ftrack_connect

def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.update', new_task_update
    )

#  Run event standalone


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    session = ftrack_api.Session()
    session.event_hub.subscribe(
        'topic=ftrack.update', new_task_update
    )
    logger.info('Listening for events. Use Ctrl-C to abort.')
    session.event_hub.wait()
