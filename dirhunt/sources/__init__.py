from dirhunt.sources.robots import Robots

SOURCE_CLASSES = [
    Robots,
]


class Sources(object):

    def __init__(self, callback, excluded_sources=()):
        self.callback = callback
        self.sources = [cls(self.callback) for cls in SOURCE_CLASSES if cls.__name__ not in excluded_sources]

    def add_domain(self, domain):
        for source in self.sources:
            source.add_domain(domain)
