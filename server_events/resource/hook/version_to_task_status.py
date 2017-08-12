import logging
import ftrack
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import utils

logging.basicConfig()
logger = logging.getLogger()


def version_to_task_status(event):
    '''Modify the application environment.'''

    for entity in event['data'].get('entities', []):

        # Filter non-assetversions
        if entity.get('entityType') == 'assetversion' and entity['action'] == 'update':
            version = ftrack.AssetVersion(id=entity.get('entityId'))
            version_status = version.getStatus()
            task_status = version_status
            try:
                task = version.getTask()
            except:
                return

            # Filter to versions with status change to "render complete"
            if version_status.get('name').lower() == 'reviewed':
                task_status = utils.get_status_by_name('change requested')

            if version_status.get('name').lower() == 'approved':
                task_status = utils.get_status_by_name('complete')
                if task.getType().getName() == 'Lighting':
                    task_status = utils.get_status_by_name('to render')

            # Proceed if the task status was set
            if task_status:
                # Get path to task
                path = task.get('name')
                for p in task.getParents():
                    path = p.get('name') + '/' + path

                # Setting task status
                try:
                    task.setStatus(task_status)
                except Exception as e:
                    print '%s status couldnt be set: %s' % (path, e)
                else:
                    print '%s updated to "%s"' % (path, task_status.get('name'))


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
        version_to_task_status
    )


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)

    ftrack.setup()

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.update',
        version_to_task_status)
    ftrack.EVENT_HUB.wait()
