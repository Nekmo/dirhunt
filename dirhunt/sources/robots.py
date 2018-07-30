from itertools import chain

import requests
from requests import RequestException

from dirhunt.sources.base import Source
from dirhunt._compat import RobotFileParser, URLError


def get_url(protocol, domain, path):
    path = path.lstrip('/')
    return '{protocol}://{domain}/{path}'.format(**locals())


class DirhuntRobotFileParser(RobotFileParser):
    def read(self):
        """Reads the robots.txt URL and feeds it to the parser."""
        try:
            r = requests.get(self.url)
        except RequestException:
            pass
        else:
            if r.status_code in (401, 403):
                self.disallow_all = True
            elif r.status_code >= 400 and r.status_code < 500:
                self.allow_all = True
            self.parse(r.text.splitlines())


class Robots(Source):
    def callback(self, domain, protocol='http'):
        rp = DirhuntRobotFileParser()
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
