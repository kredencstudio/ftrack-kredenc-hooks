import logging
import ftrack_api

logging.basicConfig()
logger = logging.getLogger()


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


# Register in case event will be ran within ftrack_connect

def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.update', file_version_statuses
    )

#  Run event standalone


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    session = ftrack_api.Session()
    session.event_hub.subscribe(
        'topic=ftrack.update', file_version_statuses
    )
    logger.info('Listening for events. Use Ctrl-C to abort.')
    session.event_hub.wait()
