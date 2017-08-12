import sys
import argparse
import logging
import threading
import getpass

import ftrack


def async(fn):
    '''Run *fn* asynchronously.'''
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class ComponentRename(ftrack.Action):
    '''Custom action.'''

    #: Action identifier.
    identifier = 'component.rename'

    #: Action label.
    label = 'Component rename'

    #: Action Icon.
    icon = "https://some.online.accessible.image.to.use.as.icon"


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
        if len(selection) == 1 and selection[0]['entityType'] == 'assetversion':
            self.logger.info('Selection is valid')
            return True
        else:
            self.logger.info('Selection is _not_ valid')
            return False



    def discover(self, event):
        '''Return action config if triggered on asset versions.'''
        selection = event['data'].get('selection', [])
        self.logger.info(u'Discovering action with selection: {0}'.format(selection))
        if not self.validateSelection(selection):
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier
            }]
        }


    def getComponentsInSelection(self, selection):
        '''Return list of versions in *selection*.'''
        versions = []
        components = []
        for item in selection:
            self.logger.info(
                'Looking for versions on entity ({0}, {1})'.format(item['entityId'], item['entityType'])
            )

            if item['entityType'] == 'assetversion':
                versions.append(ftrack.AssetVersion(item['entityId']))
                continue

            entity = None
            if item['entityType'] == 'show':
                entity = ftrack.Project(item['entityId'])
            elif item['entityType'] == 'task':
                entity = ftrack.Task(item['entityId'])

            if not entity:
                continue

            assets = entity.getAssets(includeChildren=True)
            self.logger.info('Found {0} assets on entity'.format(len(assets)))
            for asset in assets:
                assetVersions = asset.getVersions()
                self.logger.info(
                    'Found {0} versions on asset {1}'.format(len(assetVersions), asset.getId())
                )
                versions.extend(assetVersions)

        for version in versions:
            components.extend(version.getComponents())

        self.logger.info('Found {0} versions in selection'.format(len(versions)))
        return components

    # @async
    def renameSelection(self, selection, old_name, new_name):

        components = self.getComponentsInSelection(selection)

        for component in components:
            if component.getName() == old_name:
                component.set('name', new_name)


    def launch(self, event):
        '''Callback method for action.'''
        selection = event['data'].get('selection', [])
        userId = event['source']['user']['id']
        self.logger.info(u'Launching action with selection: {0}'.format(selection))

        #################################################################################

        if 'values' in event['data']:
            job = ftrack.createJob(description="Rename Components", status="running")

            try:
                ftrack.EVENT_HUB.publishReply(
                    event,
                    data={
                        'success': True,
                        'message': 'Renaming components...'
                    }
                )

                self.renameSelection(selection, event['data']['values'].get('old_name'), event['data']['values'].get('new_name'))

                # inform the user that the job is done
                job.setStatus('done')
            except:
                # fail the job if something goes wrong
                job.setStatus('failed')
                raise

        # TODO: get all existing component names / DONE (turned off because of speed)
        # components = self.getComponentsInSelection(selection)
        #
        # componentNames = []

        # for component in components:
        #     name = component.getName()
        #     if name not in componentNames:
        #         componentNames.append(name)

        # componentMenu = []
        #
        # for name in componentNames:
        #     componentMenu.append({'label': name, 'value': name})

        # return {
        #     'items': [
        #         {
        #             'value': 'Rename components',
        #             'type': 'label'
        #         }, {
        #             'value': '---',
        #             'type': 'label'
        #         }, {
        #             'label': 'Old Name',
        #             'type': 'enumerator',
        #             'name': 'old_name',
        #             'value': componentMenu[0]['value'],
        #             'data': componentMenu,
        #         }, {
        #             'label': 'New name',
        #             'type': 'text',
        #             'name': 'new_name',
        #             'value': 'New Name',
        #         }
        #     ]
        # }

        return {
            'items': [
                {
                    'value': 'Rename components',
                    'type': 'label'
                }, {
                    'value': '---',
                    'type': 'label'
                }, {
                    'label': 'Old Name',
                    'type': 'text',
                    'name': 'old_name',
                    'value': 'Old Name',
                }, {
                    'label': 'New name',
                    'type': 'text',
                    'name': 'new_name',
                    'value': 'New Name',
                }
            ]
        }






def register(registry, **kw):
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    '''Register action. Called when used as an event plugin.'''
    logging.basicConfig(level=logging.INFO)
    action = ComponentRename()
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
    action = ComponentRename()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
