import ftrack_api
import datetime


def file_version_statuses(event):
    '''Set new version status to data if version matches given types'''

    # import ftrack_api as local session

    session = ftrack_api.Session()
    # ----------------------------------

    # start of event procedure ----------------------------------
    for entity in event['data'].get('entities', []):

        # Filter to new assetversions
        if (entity['entityType'] == 'assetversion'
                and entity['action'] == 'add'):

            now = datetime.datetime.now()
            print ("\n Current date and time : {}".format(now.strftime("%Y-%m-%d %H:%M:%S")))

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
    # end of event procedure ----------------------------------

    # remove ftrack_api ----------------
    # del ftrack_api
    # ----------------------------------
