import ftrack_api


def radio_buttons(event):
    '''Provides a readio button behaviour to any bolean attribute in
       radio_button group.'''

    for entity in event['data'].get('entities', []):

        if entity['entityType'] == 'assetversion':

            group = session.query(
                'CustomAttributeGroup where name is "radio_button"').one()
            radio_buttons = []
            for g in group['custom_attribute_configurations']:
                radio_buttons.append(g['key'])

            for key in entity['keys']:
                if (key in radio_buttons and entity['changes'] is not None):
                    if entity['changes'][key]['new'] == '1':
                        version = session.get(
                            'AssetVersion', entity['entityId'])
                        asset = session.get('Asset', entity['parentId'])
                        for v in asset['versions']:
                            if version is not v:
                                v['custom_attributes'][key] = 0

        session.commit()


###############################################################################

session = ftrack_api.Session()
session.event_hub.subscribe(
    'topic=ftrack.update', radio_buttons
)
session.event_hub.wait()
