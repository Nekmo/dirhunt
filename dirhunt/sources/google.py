import asyncio
import datetime
import json
import os
from http.cookies import Morsel, SimpleCookie
from pathlib import Path
from typing import Iterable, Optional

from dirhunt.sources.base import SourceBase

TIMEOUT = 10
WAIT = 2
GOOGLE_INDEX_URL = "https://www.google.com/"
GOOGLE_SEARCH_URL = "https://www.google.com/search"


class Google(SourceBase):
    @property
    def google_cookies(self) -> Optional[Morsel]:
        return self.sources.crawler.session.cookie_jar._cookies.get(("google.com", "/"))

    @property
    def google_consent_cookie(self) -> Optional[Morsel]:
        return self.google_cookies.get("CONSENT")

    @property
    def google_cookies_path(self) -> Path:
        return self.cache_dir / "google_cookies.txt"

    async def request(self, url: str, params: Optional[dict] = None):
        """Request to Google."""
        async with self.sources.crawler.session.get(
            url,
            params=params,
            timeout=TIMEOUT,
            headers={
                "User-Agent": "'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)'"
            },
        ) as response:
            response.raise_for_status()
            return await response.text()

    def save_cookies(self):
        """Save cookies to file."""
        data = self.google_cookies.output(header="")
        os.makedirs(str(self.google_cookies_path.parent), exist_ok=True)
        with open(self.google_cookies_path, "w") as f:
            f.write(data)

    def load_cookies(self):
        """Load cookies from file."""
        with open(self.google_cookies_path, "r") as f:
            lines = f.readlines()
            cookie = SimpleCookie()
            for line in lines:
                cookie.load(line)
            self.sources.crawler.session.cookie_jar._cookies[
                ("google.com", "/")
            ] = cookie

    """Google Source class."""

    async def search_by_domain(self, domain: str) -> Iterable[str]:
        """Search by domain in Google."""
        # TODO: lock for concurrent requests.
        # Load cookies from file if exists or request to Google if not.
        cookies_path_exists = self.google_cookies_path.exists()
        if not self.google_cookies and cookies_path_exists:
            self.load_cookies()
        if not self.google_cookies and not cookies_path_exists:
            await self.request(GOOGLE_INDEX_URL)
            await asyncio.sleep(2)
        # Set consent cookie if it is pending.
        if self.google_consent_cookie and self.google_consent_cookie.value.startswith(
            "PENDING"
        ):
            now = datetime.datetime.now()
            cookie_value = f"YES+cb.{now.year}{now.month:02}{now.day:02}-17-p0.de+F+678"
            self.google_consent_cookie.set("CONSENT", cookie_value, cookie_value)
        # Save cookies to file if not exists.
        if self.google_cookies and not cookies_path_exists:
            self.save_cookies()
        text = await self.request(
            GOOGLE_SEARCH_URL,
            params={
                "q": f"site:{domain}",
                "hl": "en",
                "tbs": "0",
                "safe": "off",
                "cr": "",
                "btnG": "Google Search",
            },
        )
        # TODO:
        return []
