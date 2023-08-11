import string
from typing import Iterable

from bs4 import BeautifulSoup

from dirhunt.exceptions import SourceError
from dirhunt.sources.base import SourceBase


ABUSE = "VirusTotal is trying to prevent scraping and abuse, we are going to bother"
VT_URL = "https://www.virustotal.com/es/domain/{domain}/information/"
ABUSE_MESSAGE_ERROR = "VirusTotal abuse has failed (scraping detected). Validate the captcha manually: {url}"


class VirusTotal(SourceBase):
    async def search_by_domain(self, domain: str) -> Iterable[str]:
        """Search by domain in VirusTotal."""
        url = VT_URL.format(domain=domain)
        async with self.sources.crawler.session.get(url) as response:
            response.raise_for_status()
            html = await response.text()
        if ABUSE in html:
            raise SourceError(ABUSE_MESSAGE_ERROR.format(url=url))
        soup = BeautifulSoup(html, "html.parser")
        return [
            url.text.strip(string.whitespace)
            for url in soup.select("#detected-urls .enum a")
        ]
