import operator
import ftrack


def get_asset_name_by_id(id):
    for t in ftrack.getAssetTypes():
        try:
            if t.get('typeid') == id:
                return t.get('name')
        except:
            return None


def get_status_by_name(name):
    statuses = ftrack.getTaskStatuses()

    result = None
    for s in statuses:
        if s.get('name').lower() == name.lower():
            result = s

    return result


def get_next_task(task):
    shot = task.getParent()
    tasks = shot.getTasks()

    def sort_types(types):
        data = {}
        for t in types:
            data[t] = t.get('sort')

        data = sorted(data.items(), key=operator.itemgetter(1))
        results = []
        for item in data:
            results.append(item[0])

        return results

    types_sorted = sort_types(ftrack.getTaskTypes())

    next_types = None
    for t in types_sorted:
        if t.get('typeid') == task.get('typeid'):
            try:
                next_types = types_sorted[(types_sorted.index(t) + 1):]
            except:
                pass

    for nt in next_types:
        for t in tasks:
            if nt.get('typeid') == t.get('typeid'):
                return t

    return None

def get_latest_version(versions):
    latestVersion = None
    if len(versions) > 0:
        versionNumber = 0
        for item in versions:
            if item.get('version') > versionNumber:
                versionNumber = item.getVersion()
                latestVersion = item
    return latestVersion


def get_thumbnail_recursive(task):
    if task.get('thumbid'):
        thumbid = task.get('thumbid')
        return ftrack.Attachment(id=thumbid)
    if not task.get('thumbid'):
        parent = ftrack.Task(id=task.get('parent_id'))
        return get_thumbnail_recursive(parent)
