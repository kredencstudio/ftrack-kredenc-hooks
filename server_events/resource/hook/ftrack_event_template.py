import logging
import ftrack
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import utils

logging.basicConfig()
logger = logging.getLogger()


def event_name(event):
    '''Modify the application environment.'''

    for entity in event['data'].get('entities', []):
        pass
        # do something with the event


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
        event_name
    )


# allow the event to run independently
if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)

    ftrack.setup()

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.update',
        event_name)
    ftrack.EVENT_HUB.wait()
