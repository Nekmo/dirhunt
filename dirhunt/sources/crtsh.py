from requests.exceptions import RequestException
from dirhunt.sessions import Sessions
from dirhunt.sources.base import SourceBase


CRTSH_URL = "https://crt.sh/"
USER_AGENT = "dirhunt"
TIMEOUT = 10


class CrtSh(SourceBase):
    async def search_by_domain(self, domain: str):
        async with self.sources.crawler.session.get(
            CRTSH_URL,
            params={"q": domain, "output": "json"},
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        ) as response:
            response.raise_for_status()
            certs = await response.json()
            common_names = {cert["common_name"] for cert in certs}
            return [
                f"https://{common_name}/"
                for common_name in common_names
                if "*" not in common_name
            ]
