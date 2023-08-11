from itertools import chain
from typing import Iterable

from dirhunt.exceptions import SourceError
from dirhunt.sources.base import SourceBase
from dirhunt._compat import RobotFileParser


PROTOCOLS = ["https", "http"]


def get_url(protocol, domain, path):
    path = path.lstrip("/")
    return "{protocol}://{domain}/{path}".format(**locals())


class Robots(SourceBase):
    async def search_by_domain(self, domain: str) -> Iterable[str]:
        if domain not in self.sources.crawler.domain_protocols:
            raise SourceError(f"Protocol not available for domain: {domain}")
        protocols = self.sources.crawler.domain_protocols[domain]
        protocols = filter(lambda x: x in PROTOCOLS, protocols)
        protocols = sorted(protocols, key=lambda x: PROTOCOLS.index(x))
        protocol = protocols[0]
        rp = RobotFileParser()
        async with self.sources.crawler.session.get(
            get_url(protocol, domain, "robots.txt")
        ) as response:
            if response.status == 404:
                return []
            response.raise_for_status()
            lines = (await response.text()).splitlines()
            rp.parse(lines)
        entries = list(rp.entries)
        if rp.default_entry:
            entries.append(rp.default_entry)
        return [
            get_url(protocol, domain, ruleline.path)
            for ruleline in chain(*[entry.rulelines for entry in entries])
        ]
