import os
import sys


# Finds and returns Shared libraries include path.
def get_shared_libraries_path(endpoint='Shared'):
    expected = 'Libraries%s%s' % (os.sep, endpoint)
    for path in sys.path:
        if path.endswith(expected) and 'System.bundle' not in path:
            return path+os.sep
    bundle_path = Core.bundle_path
    if not os.path.isdir(bundle_path):
        raise OSError(2, 'Bundle path not detected correctly, please fix it in js2py_plex.py!', bundle_path)
    libraries_path = os.path.join(bundle_path, 'Contents', 'Libraries', endpoint)
    if not os.path.isdir(libraries_path):
        raise OSError(2, 'Bundle %s path not detected correctly, is it even present in the channel?' % expected, libraries_path)
    Log('Bundle %s directory not found in the sys.path, patching it in...' % expected)
    sys.path.insert(0, libraries_path)
    return libraries_path+os.sep

# Somewhat ugly hack to import Js2Py, PyJsParser and six libraries from git submodules
# (six is a depencendy for Js2Py).
try:
    libraries_path = get_shared_libraries_path('Shared')
except OSError, e:
    Log.Error('%s See "%s"' % (e.strerror, e.filename))
    raise

for dir in ['certifi', 'chardet', 'idna', 'iso8601', 'm3u8', 'oauthlib', 'requests', 'requests_oauthlib', 'rt_api', 'urllib3']:
    lib_path = libraries_path+dir
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)

try:
    libraries_path = get_shared_libraries_path('Repos')
except OSError, e:
    Log.Error('%s See "%s"' % (e.strerror, e.filename))
    raise

for dir in ['rt_api']:
    lib_path = libraries_path+dir
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)

from rt_api.api import Api

api = Api()