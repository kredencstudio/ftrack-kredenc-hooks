import logging
import ftrack
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import utils
from pprint import pprint

logging.basicConfig()
logger = logging.getLogger()


def thumbnail_update(event):
    '''Modify the application environment.'''

    for entity in event['data'].get('entities', []):

        # update created task thumbnail with first parent thumbnail
        for entity in event['data'].get('entities', []):
            if entity.get('entityType') == 'task' and entity['action'] == 'add':
                task = None
                try:
                    task = ftrack.Task(id=entity.get('entityId'))
                except:
                    return

                parent = task.getParent()
                if parent.get('thumbid') and not task.get('thumbid'):
                    task.set('thumbid', value=parent.get('thumbid'))
                    print 'Updated thumbnail on %s/%s' % (parent.getName(),
                                                          task.getName())

            # Update task thumbnail from published version
            if entity['entityType'] == 'assetversion' and entity['action'] == 'encoded':

                pprint(entity)
                try:
                    version = ftrack.AssetVersion(id=entity.get('entityId'))
                    task = ftrack.Task(version.get('taskid'))
                    thumbid = version.get('thumbid')
                except:
                    continue

                if thumbid:
                    task.set('thumbid', value=thumbid)

                    parent = task.getParent()
                    parent.set('thumbid', value=thumbid)

                    print 'Updating thumbnail for task and shot %s' % (task.getName())


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
        thumbnail_update
    )


# allow the event to run independently
if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)

    ftrack.setup()

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.update',
        thumbnail_update)
    ftrack.EVENT_HUB.wait()
