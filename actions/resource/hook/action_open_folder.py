import sys
import argparse
import logging
import getpass
import subprocess
import os

import ftrack

PLUGIN_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))

if PLUGIN_DIRECTORY not in sys.path:
    sys.path.append(PLUGIN_DIRECTORY)


import ft_utils


class openFolder(ftrack.Action):
    '''Open folders action'''

    #: Action identifier.
    identifier = 'open.folders'

    #: Action label.
    label = 'Open Folders'

    #: Action Icon.
    icon = "https://cdn3.iconfinder.com/data/icons/stroke/53/Open-Folder-256.png"

    def __init__(self):
        '''Initialise action handler.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def register(self):
        '''Register action.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )


    def validateSelection(self, selection):
        '''Return true if the selection is valid.

        '''
        if len(selection) == 0 or selection[0]['entityType'] in ['assetversion', 'Component']:
            self.logger.info('Selection is not valid valid')
            return False

        return True

    def discover(self, event):
        selection = event['data'].get('selection', [])

        # validate selection, and only return action if it is valid.
        if not self.validateSelection(selection):
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
                'icon': self.icon
            }]
        }

    def get_paths(self, entity):
        '''Prepare all the paths for the entity.

        This function uses custom module to deal with paths.
        You will need to replace it with your logic.
        '''



        root = entity.getProject().getRoot()
        entity_type = entity.getObjectType().lower()

        if entity_type == 'task':
            if entity.getParent().getObjectType() == 'Asset Build':
                templates = ['asset.task']
            else:
                templates = ['shot.task']

        elif entity_type in ['shot', 'folder', 'sequence', 'episode']:
                templates = ['shot']

        elif entity_type in ['asset build', 'library']:
                templates = ['asset']

        paths = ft_utils.getPathsYaml(entity,
                                          templateList=templates,
                                          root=root)
        return paths

    def launch(self, event):
        '''Callback method for action.'''
        selection = event['data'].get('selection', [])
        self.logger.info(u'Launching action with selection \
                         {0}'.format(selection))

        # Prepare lists to keep track of failures and successes
        fails = []
        hits = set([])

        for item in selection:
            # Filter between 'tasks' and projects
            if item['entityType'] == 'task':
                entity = ftrack.Task(item['entityId'])
            else:
                entity = ftrack.Project(item['entityId'])

            # Get paths base on the entity.
            # This function needs to be chagned to fit your path logic
            paths = self.get_paths(entity)

            # For each path, check if it exists on the disk and try opening it
            for path in paths:
                if os.path.isdir(path):
                    self.logger.info('Opening: ' + path)

                    # open the folder
                    if sys.platform == 'darwin':
                        subprocess.Popen(['open', '--', path])
                    elif sys.platform == 'linux2':
                        subprocess.Popen(['gnome-open', '--', path])
                    elif sys.platform == 'win32':
                        subprocess.Popen(['explorer', path])

                    # add path to list of hits
                    hits.add(entity.getName())

            # Add entity to fails list if no folder could be openned for it
            if entity.getName() not in hits:
                fails.append(entity.getName())

        # Inform user of the result
        if len(hits) == 0:
            return {
                'success': False,
                'message': 'No folders found for: {}'.format(', '.join(fails))
            }

        if len(fails) > 0:
            return {
                'success': True,
                'message': 'No folders found for: {}'.format(', '.join(fails))
            }

        return {
            'success': True,
            'message': 'Opening folders'
        }


def register(registry, **kw):
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    '''Register action. Called when used as an event plugin.'''
    logging.basicConfig(level=logging.INFO)
    action = openFolder()
    action.register()


def main(arguments=None):
    '''Set up logging and register action.'''
    if arguments is None:
        arguments = []

    parser = argparse.ArgumentParser()
    # Allow setting of logging level from arguments.
    loggingLevels = {}
    for level in (
        logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING,
        logging.ERROR, logging.CRITICAL
    ):
        loggingLevels[logging.getLevelName(level).lower()] = level

    parser.add_argument(
        '-v', '--verbosity',
        help='Set the logging output verbosity.',
        choices=loggingLevels.keys(),
        default='info'
    )
    namespace = parser.parse_args(arguments)

    '''Register action and listen for events.'''
    logging.basicConfig(level=loggingLevels[namespace.verbosity])

    ftrack.setup()
    action = openFolder()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
