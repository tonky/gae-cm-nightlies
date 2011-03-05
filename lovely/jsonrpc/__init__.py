DEFAULT_JSON_IMPL = None

try:
    import json
    DEFAULT_JSON_IMPL = json
except ImportError:
    pass

try:
    import simplejson
    DEFAULT_JSON_IMPL = simplejson
except ImportError:
    pass


class JSONImplementationNotFound(Exception):
    def __init__(self):
        super(JSONImplementationNotFound, self).__init__(
            "Unable to find any json implementation"
            " you need either Python 2.6+ or simplejson installed")
