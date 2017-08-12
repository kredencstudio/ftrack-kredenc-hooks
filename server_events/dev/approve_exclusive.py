import ftrack
import utils

def callback(event):
    """ This plugin triggers when a task's status is updated to any DONE state.
    It searches for the next task via the sorting order in System settings>Types,
    and sets the next task to "Not started" if the next task is set to "Not ready".
    """

    for entity in event['data'].get('entities', []):

        pass
        # # Filter to only tasks
        # if entity.get('entityType') == 'assetversion' and entity['action'] == 'update':
        #
        #     version = ftrack.AssetVersion(id=entity.get('entityId'))
        #     version_status = version.getStatus()
        #
        #     if version_status.get('name').lower() == 'approved':
        #         task_status = utils.get_status_by_name('complete')


# Subscribe to events with the update topic.
ftrack.setup()
ftrack.EVENT_HUB.subscribe('topic=ftrack.update', callback)
ftrack.EVENT_HUB.wait()
