import asyncio
import datetime
import json
import os
from functools import cached_property
from pathlib import Path
from typing import List, Iterable, Optional

from aiohttp import ClientError
from platformdirs import user_cache_dir
from typing_extensions import TYPE_CHECKING

from dirhunt import __version__
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.exceptions import SourceError
from dirhunt.utils import get_message_from_exception

if TYPE_CHECKING:
    from dirhunt.sources import Sources


class SourceBase:
    max_cache_age = datetime.timedelta(days=7)
    allow_subdomains = False
    wait_locks = {}
    wait_between_requests = None

    def __init__(self, sources: "Sources", domain: str):
        self.sources = sources
        self.domain = domain

    @classmethod
    def get_source_name(cls) -> str:
        return cls.__name__.lower()

    @property
    def cache_dir(self) -> Path:
        return Path(user_cache_dir()) / "dirhunt" / self.get_source_name()

    @property
    def cache_file(self) -> Path:
        return self.cache_dir / f"{self.domain}.json"

    @cached_property
    def is_cache_expired(self) -> bool:
        return (
            not self.cache_file.exists()
            or self.cache_file.stat().st_mtime
            < (datetime.datetime.now() - self.max_cache_age).timestamp()
        )

    def get_from_cache(self) -> Optional[List[str]]:
        with open(self.cache_file) as file:
            data = json.load(file)
            if data["version"] != __version__:
                return None
            return data["urls"]

    async def search_by_domain(self, domain: str) -> Iterable[str]:
        raise NotImplementedError

    async def retrieve_urls(self, domain: str):
        urls = None
        acquired_lock = False
        if not self.is_cache_expired:
            urls = self.get_from_cache()
        if not urls and self.wait_between_requests:
            acquired_lock = True
            await self.acquire_wait_lock()
        if urls is None:
            try:
                urls = await self.search_by_domain(domain)
            except (ClientError, SourceError, asyncio.TimeoutError) as e:
                self.sources.crawler.print_error(
                    f"Failed to retrieve {domain} using the source {self.get_source_name()}: "
                    f"{get_message_from_exception(e)}"
                )
                urls = []
            else:
                self.save_to_cache(urls)
        for url in urls:
            await self.add_url(url)
        if acquired_lock:
            await self.release_wait_lock()

    def save_to_cache(self, urls: Iterable[str]) -> None:
        cache_data = {
            "version": __version__,
            "domain": self.domain,
            "urls": list(urls),
        }
        os.makedirs(str(self.cache_file.parent), exist_ok=True)
        with open(self.cache_file, "w") as file:
            json.dump(cache_data, file)

    async def add_url(self, url: str):
        """Add url to crawler."""
        await self.sources.crawler.add_crawler_url(
            CrawlerUrl(self.sources.crawler, url)
        )

    async def acquire_wait_lock(self):
        """Acquire wait lock."""
        if self.get_source_name() not in self.wait_locks:
            self.wait_locks[self.get_source_name()] = asyncio.Lock()
        await self.wait_locks[self.get_source_name()].acquire()

    async def release_wait_lock(self):
        """Release wait lock."""
        if self.get_source_name() in self.wait_locks:
            await asyncio.sleep(self.wait_between_requests)
            self.wait_locks[self.get_source_name()].release()
