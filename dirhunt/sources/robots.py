from itertools import chain

from dirhunt.sources.base import Source
from dirhunt._compat import RobotFileParser, URLError


def get_url(protocol, domain, path):
    path = path.lstrip('/')
    return '{protocol}://{domain}/{path}'.format(**locals())


class Robots(Source):
    def callback(self, domain, protocol='http'):
        rp = RobotFileParser()
        rp.set_url(get_url(protocol, domain, 'robots.txt'))
        try:
            rp.read()
        except (IOError, URLError):
            if protocol == 'http':
                self.callback(domain, 'https')
            return
        entries = list(rp.entries)
        if rp.default_entry:
            entries.append(rp.default_entry)
        for ruleline in chain(*[entry.rulelines for entry in entries]):
            self.add_result(get_url(protocol, domain, ruleline.path))
