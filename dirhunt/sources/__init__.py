from functools import cached_property
from typing import List, Type, Union

from typing_extensions import TYPE_CHECKING

from dirhunt.sources.commoncrawl import CommonCrawl
from dirhunt.sources.crtsh import CrtSh
from dirhunt.sources.google import Google
from dirhunt.sources.robots import Robots
from dirhunt.sources.ssl import CertificateSSL
from dirhunt.sources.virustotal import VirusTotal
from dirhunt.sources.wayback import Wayback


if TYPE_CHECKING:
    from dirhunt.sources.base import SourceBase


SOURCE_CLASSES: List[Type["SourceBase"]] = [
    # Robots,
    # VirusTotal,
    # Google,
    CommonCrawl,
    # CrtSh,
    # CertificateSSL,
    # Wayback,
]


def get_source_name(cls: Type["SourceBase"]):
    return cls.__name__.lower()


if TYPE_CHECKING:
    from dirhunt.crawler import Crawler


class Sources:
    """Sources class. This class is used to manage the sources."""

    def __init__(self, crawler: "Crawler"):
        self.crawler = crawler

    @cached_property
    def source_classes(self) -> List[Type["SourceBase"]]:
        """Return source classes."""
        return [
            cls
            for cls in SOURCE_CLASSES
            if cls not in self.crawler.configuration.exclude_sources
        ]

    async def add_domain(self, domain: str):
        """Add domain to sources."""
        for source_cls in self.source_classes:
            source = source_cls(self, domain)
            self.crawler.add_task(
                source.retrieve_urls(domain), f"{source.get_source_name()}-{domain}"
            )
