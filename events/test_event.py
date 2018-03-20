# import ftrack_api
#
#
# def test_event(event):
#     '''just a testing event'''
#
#     # import ftrack_api as local session
#     from unidecode import unidecode
#     session = ftrack_api.Session()
#     # ----------------------------------
#     print '\n'
#     # start of event procedure ----------------------------------
#     for entity in event['data'].get('entities', []):
#         if (entity['entityType'] == 'task' and entity['action'] == 'update'):
#
#             task = session.get('Task', entity['entityId'])
#             user = session.query(
#                 'select first_name, last_name from User where assignments any (context_id = "{0}")'.
#                 format(task['id'])).first()
#
#             # encode diacritic
#             user['first_name'] = unidecode(user['first_name'])
#             user['last_name'] = unidecode(user['last_name'])
#
#             print user['first_name'], user['last_name']
#
#             # print task.keys()
#             # print '\n'
#             # print task['assignments']
#             print '\n'
#             for e in entity.keys():
#                 print e, entity[e]
#             print '\n'
#     # end of event procedure ----------------------------------
#
#     # remove ftrack_api ----------------
#     # del ftrack_api
#     # ----------------------------------
