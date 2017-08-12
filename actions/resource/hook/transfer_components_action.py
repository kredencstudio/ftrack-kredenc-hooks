# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
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


class TransferComponentsAction(ftrack.Action):
    '''Action to transfer components between locations.'''

    #: Action identifier.
    identifier = 'transfer-components'

    #: Action label.
    label = 'Transfer component(s)'

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
        '''Return if *selection* is valid.'''
        if (
            len(selection) >= 1 and
            any(
                True for item in selection
                if item.get('entityType') in ('assetversion', 'task', 'show')
            )
        ):
            self.logger.info('Selection is valid')
            return True
        else:
            self.logger.info('Selection is _not_ valid')
            return False

    def discover(self, event):
        '''Return action config.'''
        selection = event['data'].get('selection', [])
        self.logger.info(u'Discovering action with selection: {0}'.format(selection))
        if not self.validateSelection(selection):
            return

        return super(TransferComponentsAction, self).discover(event)


    def getVersionsInSelection(self, selection):
        '''Return list of versions in *selection*.'''
        versions = []
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

        self.logger.info('Found {0} versions in selection'.format(len(versions)))
        return versions

    def getComponentsInLocation(self, selection, location):
        '''Return list of components in *selection*.'''
        versions = self.getVersionsInSelection(selection)

        components = []
        for version in versions:
            self.logger.info('Looking for components on version {0}'.format(version.getId()))
            components.extend(version.getComponents(location=location))

        self.logger.info('Found {0} components in selection'.format(len(components)))
        return components

    @async
    def transferComponents(
        self, selection, sourceLocation, targetLocation,
        userId=None,
        ignoreComponentNotInLocation=False,
        ignoreLocationErrors=False
    ):
        '''Transfer components in *selection* from *sourceLocation* to *targetLocation*.

        if *ignoreComponentNotInLocation*, ignore components missing in source
        location. If *ignoreLocationErrors* is specified, ignore all locations-
        related errors.

        Reports progress back to *userId* using a job.
        '''

        job = ftrack.createJob('Transfer components (Gathering...)', 'running', user=userId)
        try:
            components = self.getComponentsInLocation(selection, sourceLocation)
            amount = len(components)
            self.logger.info('Transferring {0} components'.format(amount))

            for index, component in enumerate(components, start=1):
                self.logger.info('Transferring component ({0} of {1})'.format(index, amount))
                job.setDescription('Transfer components ({0} of {1})'.format(index, amount))

                try:
                    targetLocation.addComponent(component, manageData=True)
                except ftrack.ComponentInLocationError:
                    self.logger.info('Component ({}) already in target location'.format(component))
                except ftrack.ComponentNotInLocationError:
                    if ignoreComponentNotInLocation or ignoreLocationErrors:
                        self.logger.exception('Failed to add component to location')
                    else:
                        raise
                except ftrack.LocationError:
                    if ignoreLocationErrors:
                        self.logger.exception('Failed to add component to location')
                    else:
                        raise

            job.setStatus('done')
            self.logger.info('Transfer complete ({0} components)'.format(amount))

        except Exception:
            self.logger.exception('Transfer failed')
            job.setStatus('failed')

    def launch(self, event):
        '''Callback method for action.'''
        selection = event['data'].get('selection', [])
        userId = event['source']['user']['id']
        self.logger.info(u'Launching action with selection: {0}'.format(selection))

        if 'values' in event['data']:
            values = event['data']['values']
            self.logger.info(u'Received values: {0}'.format(values))
            sourceLocation = ftrack.Location(values['from_location'])
            targetLocation = ftrack.Location(values['to_location'])
            if sourceLocation == targetLocation:
                return {
                    'success': False,
                    'message': 'Source and target locations are the same.'
                }

            ignoreComponentNotInLocation = (
                values.get('ignore_component_not_in_location') == 'true'
            )
            ignoreLocationErrors = (
                values.get('ignore_location_errors') == 'true'
            )

            self.logger.info(
                'Transferring components from {0} to {1}'.format(sourceLocation, targetLocation)
            )
            self.transferComponents(
                selection,
                sourceLocation,
                targetLocation,
                userId=userId,
                ignoreComponentNotInLocation=ignoreComponentNotInLocation,
                ignoreLocationErrors=ignoreLocationErrors
            )
            return {
                'success': True,
                'message': 'Transferring components...'
            }

        allLocations = [
            {
                'label': location.get('name'),
                'value': location.get('id')
            }
            for location in ftrack.getLocations(excludeInaccessible=True)
        ]

        if len(allLocations) < 2:
            self.transferComponents(selection, sourceLocation, targetLocation)
            return {
                'success': False,
                'message': 'Did not find two accessible locations'
            }

        return {
            'items': [
                {
                    'value': 'Transfer components between locations',
                    'type': 'label'
                }, {
                    'label': 'Source location',
                    'type': 'enumerator',
                    'name': 'from_location',
                    'value': allLocations[0]['value'],
                    'data': allLocations
                }, {
                    'label': 'Target location',
                    'type': 'enumerator',
                    'name': 'to_location',
                    'value': allLocations[1]['value'],
                    'data': allLocations
                }, {
                    'value': '---',
                    'type': 'label'
                }, {
                    'label': 'Ignore missing',
                    'type': 'enumerator',
                    'name': 'ignore_component_not_in_location',
                    'value': 'false',
                    'data': [
                        {'label': 'Yes', 'value': 'true'},
                        {'label': 'No', 'value': 'false'}
                    ]
                }, {
                    'label': 'Ignore errors',
                    'type': 'enumerator',
                    'name': 'ignore_location_errors',
                    'value': 'false',
                    'data': [
                        {'label': 'Yes', 'value': 'true'},
                        {'label': 'No', 'value': 'false'}
                    ]
                }
            ]
        }


def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'transfer-components'
    )

    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return

    # Validate that registry is an instance of ftrack.Registry. If not,
    # assume that register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(registry, ftrack.Registry):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack.Registry instance.'.format(registry)
        )
        return

    action = TransferComponentsAction()
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

    # Set up basic logging
    logging.basicConfig(level=loggingLevels[namespace.verbosity])

    # Subscribe to action.
    ftrack.setup()
    action = TransferComponentsAction()
    action.register()

    # Wait for events
    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
