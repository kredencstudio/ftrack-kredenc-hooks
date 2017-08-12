# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import sys
import argparse
import logging
import os
import getpass
import threading

import ftrack


def async(fn):
    '''Run *fn* asynchronously.'''
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class ImportThumbnails(ftrack.Action):
    '''Batch import thumbnails to a project.'''

    #: Action identifier.
    identifier = 'ftrack.batch.import.thumbnails'

    #: Action label.
    label = 'Batch import thumbnails'

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


    def validate_input(self, input_values):
        '''Validate the input parameters.'''

        if not input_values:
            return False

        try:
            folder_path = input_values['folder_path']
        except:
            folder_path = None

        if not folder_path:
            return False

        if not os.path.isdir(folder_path):
            return False

        return True

    @async
    def upload_files_as_thumbnails(self, files):
        '''Upload the files as thumbnails.'''
        job = ftrack.createJob(
            'Creating thumbnails.', 'running'
        )

        try:
            for ftrack_path, file_path in files:
                try:
                    entity = ftrack.getFromPath(ftrack_path)
                except ftrack.FTrackError:
                    print 'Could not find entity with path "{}"'.format(
                        ftrack_path
                    )
                    continue

                entity.createThumbnail(file_path)
        except Exception:
            # Except anything and fail the job.
            job.setStatus('failed')
            job.setDescription('Creating thumbnails failed.')

        job.setStatus('done')
        job.setDescription('Creating thumbnails done.')

    def get_files(self, path, project_name):
        '''Return a list of tuples with ftrack path and filepaths.'''
        all_files = []
        for filename in os.listdir(path):
            absolute_file_path = os.path.join(path, filename)
            if os.path.isfile(absolute_file_path):
                ftrack_path, _ = os.path.splitext(filename)
                all_files.append(
                    (
                        '{}.{}'.format(project_name, ftrack_path),
                        absolute_file_path
                    )
                )

        return all_files

    def discover(self, event):
        '''Return action config if triggered on a single asset version.'''
        data = event['data']

        # If selection contains more than one item return early since
        # this action can only handle a single version.
        selection = data.get('selection', [])
        if (
            not len(selection) or
            len(selection) > 1 or
            selection[0]['entityType'] != 'show'
        ):
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier
            }]
        }

    def launch(self, event):
        '''Callback method for action.'''
        project_id = event['data']['selection'][0]['entityId']
        project = ftrack.Project(project_id)

        try:
            input_values = event['data']['values']
        except KeyError:
            input_values = None

        if not self.validate_input(input_values):
            return {
                'items': [{
                    'type': 'label',
                    'value': '''
This action will batch import thumbnails to selected project.

Specify a *folder path* to a folder on your disk which
contains images you want to use. The images should be named
to match the entity path in ftrack.

For example:

    0010.png
    0010.010.png
    0010.010.generic.png

This will set the thumbnail for the *sequence*, *shot* and the
*generic task*.
                    '''
                }, {
                    'type': 'text',
                    'label': 'Folder path',
                    'name': 'folder_path'
                }]
            }

        files = self.get_files(input_values['folder_path'], project.getName())

        self.upload_files_as_thumbnails(files)

        return {
            'success': True,
            'message': 'Action completed successfully'
        }


def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''

    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return
    '''Register action. Called when used as an event plugin.'''
    logging.basicConfig(level=logging.INFO)
    action = ImportThumbnails()
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
    action = ImportThumbnails()
    action.register()

    # Wait for events
    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
