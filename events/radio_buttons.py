# import ftrack_api
#
#
# def radio_buttons(event):
#     '''Provides a readio button behaviour to any bolean attribute in
#        radio_button group.'''
#
#     # import ftrack_api as local session
#
#     session = ftrack_api.Session()
#     # ----------------------------------
#
#     # start of event procedure ----------------------------------
#     for entity in event['data'].get('entities', []):
#
#         if entity['entityType'] == 'assetversion':
#
#             group = session.query(
#                 'CustomAttributeGroup where name is "radio_button"').one()
#             radio_buttons = []
#             for g in group['custom_attribute_configurations']:
#                 radio_buttons.append(g['key'])
#
#             for key in entity['keys']:
#                 if (key in radio_buttons and entity['changes'] is not None):
#                     if entity['changes'][key]['new'] == '1':
#                         version = session.get('AssetVersion',
#                                               entity['entityId'])
#                         asset = session.get('Asset', entity['parentId'])
#                         for v in asset['versions']:
#                             if version is not v:
#                                 v['custom_attributes'][key] = 0
#
#         session.commit()
#     # end of event procedure ----------------------------------
#
#     # remove ftrack_api ----------------
#     # del ftrack_api
#     # ----------------------------------
