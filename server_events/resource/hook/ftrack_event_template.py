import logging
import ftrack_api

logging.basicConfig()
logger = logging.getLogger()


def event_name(event):
    '''Modify the application environment.'''

    for entity in event['data'].get('entities', []):
        # START of event script paylod

        pass

        # END of event script paylod
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
        'topic=ftrack.update', event_name
    )

#  Run event standalone


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    session = ftrack_api.Session()
    session.event_hub.subscribe(
        'topic=ftrack.update', event_name
    )
    logger.info('Listening for events. Use Ctrl-C to abort.')
    session.event_hub.wait()
