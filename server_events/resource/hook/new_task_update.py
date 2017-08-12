import logging
import ftrack
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import utils

logging.basicConfig()
logger = logging.getLogger()


def new_task_update(event):
    '''Modify the application environment.'''

    for entity in event['data'].get('entities', []):

        # Filter to only tasks
        if entity.get('entityType') == 'task' and entity['action'] == 'update':

            # Find task if it exists
            task = None
            try:
                task = ftrack.Task(id=entity.get('entityId'))
            except:
                return

            # Filter to tasks only
            if task and task.get('objecttypename') == 'Task':

                # Setting next task to NOT STARTED, if on NOT READY
                if task.getStatus().get('state') == 'DONE':
                    next_task = utils.get_next_task(task)
                    if next_task:
                        if next_task.getStatus().get('state') == 'NOT_STARTED':
                            if next_task.getStatus().get('name').lower() == 'not ready'.lower():

                                # Get path to next task
                                path = next_task.get('name')
                                for p in task.getParents():
                                    path = p.get('name') + '/' + path

                                # Setting next task status
                                try:
                                    next_task.setStatus(utils.get_status_by_name('ready'))
                                    print '%s updated to "Ready"' % path
                                except Exception as e:
                                    print '%s status couldnt be set: %s' % (path, e)
                                else:
                                    print '%s updated to "Ready"' % path


def register(registry, **kw):
    '''Register location plugin.'''

    # Validate that registry is the correct ftrack.Registry. If not,
    # assume that register is being called with another purpose or from a
    # new or incompatible API and return without doing anything.
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.update',
        new_task_update
    )


# allow the event to run independently
if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)

    ftrack.setup()

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.update',
        new_task_update)
    ftrack.EVENT_HUB.wait()
