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
            with requests.get(self.url) as response:
                status_code = response.status_code
                text = response.text
        except RequestException:
            pass
        else:
            if status_code in (401, 403):
                self.disallow_all = True
            elif status_code >= 400 and status_code < 500:
                self.allow_all = True
            self.parse(text.splitlines())


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
