from json import JSONEncoder


class JsonReportEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        elif hasattr(obj, 'json'):
            return obj.json()
        return super(JsonReportEncoder, self).default(obj)
