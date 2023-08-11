import json
from json import JSONDecodeError
from typing import Iterable

from aiohttp import ClientError

from dirhunt.sources.base import SourceBase


COMMONCRAWL_URL = "https://index.commoncrawl.org/collinfo.json"
TIMEOUT = 10


class CommonCrawl(SourceBase):
    async def get_latest_craw_index(self):
        url = COMMONCRAWL_URL
        async with self.sources.crawler.session.get(url, timeout=TIMEOUT) as response:
            response.raise_for_status()
            crawl_indexes = await response.json()
        latest_crawl_index = crawl_indexes[0]
        return latest_crawl_index["cdx-api"]

    async def search_by_domain(self, domain: str) -> Iterable[str]:
        latest_crawl_index = await self.get_latest_craw_index()
        if not latest_crawl_index:
            return []
        async with self.sources.crawler.session.get(
            latest_crawl_index,
            params={"url": "*.{}".format(domain), "output": "json"},
            timeout=TIMEOUT,
        ) as response:
            response.raise_for_status()
            urls = set()
            while True:
                line = (await response.content.readline()).decode("utf-8")
                if not line:
                    break
                data = json.loads(line)
                urls.add(data["url"])
            return urls
