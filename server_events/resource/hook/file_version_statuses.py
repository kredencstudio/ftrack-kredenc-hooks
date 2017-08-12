import logging
import ftrack
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import utils

logging.basicConfig()
logger = logging.getLogger()


def file_version_statuses(event):
    '''Modify the application environment.'''

    for entity in event['data'].get('entities', []):

        # Filter non-assetversions
        if entity.get('entityType') == 'assetversion' and entity['action'] == 'add':
            version = ftrack.AssetVersion(id=entity.get('entityId'))

            asset_type = version.getAsset().getType().getShort()

            file_status = utils.get_status_by_name('data')

            # Setting task status
            try:
                if asset_type in ['cam', 'cache', 'rig', 'scene']:
                    version.setStatus(file_status)
            except Exception as e:
                print 'status couldnt be set: %s' % ( e)
            else:
                print 'updated to "%s"' % (file_status.get('name'))


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
        file_version_statuses
    )


# allow the event to run independently
if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)

    ftrack.setup()

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.update',
        file_version_statuses)
    ftrack.EVENT_HUB.wait()
