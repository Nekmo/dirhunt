from dirhunt.sources.robots import Robots

SOURCE_CLASSES = [
    Robots,
]


def get_source_name(cls):
    return cls.__name__.lower()


class Sources(object):

    def __init__(self, callback, excluded_sources=()):
        self.callback = callback
        self.sources = [cls(self.callback) for cls in SOURCE_CLASSES if get_source_name(cls) not in excluded_sources]

    def add_domain(self, domain):
        for source in self.sources:
            source.add_domain(domain)

    def finished(self):
        for source in self.sources:
            if source.is_running():
                return False
        return True
