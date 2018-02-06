# import ftrack_api
#
#
# def event_name(event):
#     '''Modify the application environment.'''
#
#     for entity in event['data'].get('entities', []):
#         # START of event script paylod
#
#         pass
#
#         # END of event script paylod
#         session.commit()
#
#
# ###############################################################################
#
#
# session = ftrack_api.Session()
# session.event_hub.subscribe(
#     'topic=ftrack.update', event_name
# )
# session.event_hub.wait()
