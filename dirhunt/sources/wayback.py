from typing import Iterable

from dirhunt.sources.base import SourceBase


WAYBACK_LIMIT = 100
WAYBACK_URL = "https://web.archive.org/cdx/search/cdx"
WAYBACK_PARAMS = {
    "fl": "original",
    "collapse": "urlkey",
    "limit": WAYBACK_LIMIT,
    "matchType": "domain",
    "filter": "statuscode:200",
}
DEFAULT_ENCODING = "utf-8"
TIMEOUT = 10


class Wayback(SourceBase):
    async def search_by_domain(self, domain: str) -> Iterable[str]:
        """Search by domain in Wayback."""
        async with self.sources.crawler.session.get(
            WAYBACK_URL,
            params=dict(WAYBACK_PARAMS, url=domain),
            timeout=TIMEOUT,
        ) as response:
            response.raise_for_status()
            urls = []
            text = await response.text()
            for line in filter(bool, text.splitlines()):
                if isinstance(line, bytes):
                    line = line.decode(response.get_encoding() or DEFAULT_ENCODING)
                urls.append(line)
            return urls
