import os
import re
import shutil
import subprocess
import operator

import ftrack
import ftrack_api
import ftrack_template


def version_get(string, prefix, suffix=None):
    """ Extract version information from filenames.
    Code from Foundry"s nukescripts.version_get()
    """

    if string is None:
        raise ValueError("Empty version string - no match")

    regex = "." + prefix + "\d+"
    matches = re.findall(regex, string, re.IGNORECASE)
    if not len(matches):
        msg = "No " + prefix + " found in \"" + string + "\""
        raise ValueError(msg)
    return (matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group())


def get_task_data(event):

    data = event["data"]
    app_id = event["data"]["application"]["identifier"].split("_")[0]

    session = ftrack_api.Session()
    task = session.get("Task", data["context"]["selection"][0]["entityId"])

    if app_id == "nukex":
        app_id = "nuke"

    templates = ftrack_template.discover_templates()
    work_file, template = ftrack_template.format(
        {app_id: app_id, "padded_version": "001"}, templates, entity=task
    )
    work_area = os.path.dirname(work_file)

    # Pyblish
    if app_id == "pyblish":
        task_area, template = ftrack_template.format(
            {}, templates, entity=task
        )
        data["command"].extend(["--path", task_area])
        return data

    # Finding existing work files
    if os.path.exists(work_area):
        max_version = 0
        for f in os.listdir(work_area):

            # If the file extension doesn't match, we'll ignore the file.
            if os.path.splitext(f)[1] != os.path.splitext(work_file)[1]:
                continue

            try:
                version = version_get(f, "v")[1]
                if version > max_version:
                    max_version = version
                    work_file = os.path.join(work_area, f)
            except:
                pass

    # If no work file exists, copy an existing publish
    publish_file = None
    if not os.path.exists(work_file):
        query = "Asset where parent.id is \"{0}\" and type.short is \"scene\""
        query += " and name is \"{1}\""
        asset = session.query(
            query.format(task["parent"]["id"], task["name"])
        ).first()

        # Skip if no assets are found
        if asset:
            for version in reversed(asset["versions"]):
                for component in version["components"]:
                    if component["name"] == app_id:
                        location_id = max(
                            component.get_availability().iteritems(),
                            key=operator.itemgetter(1)
                        )[0]
                        location = session.query(
                            "Location where id is \"{0}\"".format(location_id)
                        ).one()
                        publish_file = location.get_resource_identifier(
                            component
                        )

                if publish_file:
                    break

    # If no work file exists, create a work file
    if not os.path.exists(work_file):

        if not os.path.exists(os.path.dirname(work_file)):
            os.makedirs(os.path.dirname(work_file))

        # Copy the publish file if any exists,
        # else create a new work file from application
        if publish_file:
            shutil.copy(publish_file, work_file)
        else:

            # Create parent directory if it doesn't exist
            if not os.path.exists(os.path.dirname(work_file)):
                os.makedirs(os.path.dirname(work_file))

            # Call Nuke terminal to create an empty work file
            if app_id == "nuke":
                subprocess.call([
                    event["data"]["application"]["path"],
                    "-i",
                    "-t",
                    os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__), "..", "nuke_save.py"
                        )
                    ),
                    work_file
                ])
            # Call Mayapy terminal to create an empty work file
            if app_id == "maya":
                subprocess.call(
                    [
                        os.path.join(
                            os.path.dirname(
                                event["data"]["application"]["path"]
                            ),
                            "mayapy.exe"
                        ),
                        os.path.abspath(
                            os.path.join(
                                os.path.dirname(__file__), "..", "maya_save.py"
                            )
                        ),
                        work_file
                    ]
                )
            # Call hypthon terminal to create an empty work file
            if app_id == "houdini":
                subprocess.call([
                    os.path.join(
                        os.path.dirname(event["data"]["application"]["path"]),
                        "hython2.7.exe"
                    ),
                    os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__), "..", "houdini_save.py"
                        )
                    ),
                    work_file
                ])
    else:  # If work file exists check to see if it needs to be versioned up
        old_api_task = ftrack.Task(data["context"]["selection"][0]["entityId"])
        asset = old_api_task.getParent().createAsset(
            old_api_task.getName(),
            "scene",
            task=old_api_task
        )

        version = 1
        versions = asset.getVersions()
        if versions:
            version = versions[-1].getVersion()

        if version > int(version_get(work_file, "v")[1]):

            new_work_file = ftrack_template.format(
                {app_id: app_id, "padded_version": str(version).zfill(3)},
                templates,
                entity=task
            )[0]

            shutil.copy(work_file, new_work_file)
            work_file = new_work_file

    output = subprocess.check_output([
        "python",
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "open_work_file.py"
            )
        ),
        work_file
    ])

    data["command"].append(output.replace("\\", "/").splitlines()[0])
    return data


def modify_application_launch(event):
    """Modify the application launch command with potential files to open"""

    data = event["data"]
    selection = event["data"]["context"]["selection"]

    if not selection:
        return

    entityType = selection[0]["entityType"]

    # task based actions
    if entityType == "task":
        data = get_task_data(event)

    return data


def register(registry, **kw):
    """Register location plugin."""

    # Validate that registry is the correct ftrack.Registry. If not,
    # assume that register is being called with another purpose or from a
    # new or incompatible API and return without doing anything.
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return

    ftrack.EVENT_HUB.subscribe(
        "topic=ftrack.connect.application.launch",
        modify_application_launch
    )
