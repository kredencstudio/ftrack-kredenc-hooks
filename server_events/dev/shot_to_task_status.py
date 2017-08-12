# import sys
# import os
# import pprint
# import ftrack
#
#
# def callback(event):
#     """ This plugin sets the task status from the version status update.
#     """
#
#     for entity in event['data'].get('entities', []):
#
#         # Filter non-assetversions
#         if entity.get('entityType') == 'task' and entity['action'] == 'update':
#
#             # Find task if it exists
#             task = None
#             try:
#                 obj = ftrack.Task(id=entity.get('entityId'))
#             except:
#                 return
#
#             # Filter to tasks only
#
#             if obj and (obj.get('objecttypename') in ['Shot', 'Asset Build']):
#                 status = obj.getStatus()
#
#                 tasks = obj.getTasks()
#                 print tasks
#
#                 # Proceed if we have status
#                 for task in tasks:
#
#                     # Get path to task for logging
#                     path = task.get('name')
#                     for p in task.getParents():
#                         path = p.get('name') + '/' + path
#
#                     # Setting task status
#                     try:
#                         task.setStatus(status)
#                     except Exception as e:
#                         print '%s status couldnt be set: %s' % (path, e)
#                     else:
#                         print '%s updated to "%s"' % (path, status.get('name'))
#
#
# # Subscribe to events with the update topic.
# ftrack.setup()
# ftrack.EVENT_HUB.subscribe('topic=ftrack.update', callback)
# ftrack.EVENT_HUB.wait()
