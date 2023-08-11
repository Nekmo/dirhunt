import socket
import ssl
from typing import Iterable

from dirhunt.exceptions import SourceError
from dirhunt.sources.base import SourceBase


DEFAULT_SSL_PORT = 443


def get_url(protocol, domain, path):
    path = path.lstrip("/")
    return "{protocol}://{domain}/{path}".format(**locals())


class CertificateSSL(SourceBase):
    async def search_by_domain(self, domain: str) -> Iterable[str]:
        async with self.sources.crawler.session.get(f"https://{domain}") as response:
            response.raise_for_status()
            if response.connection is None:
                raise SourceError("Connection is not available.")
            cert = response.connection.transport.get_extra_info("peercert")
            alt_names = cert.get("subjectAltName") or ()
            urls = []
            for alt_name in alt_names:
                alt_name_domain = alt_name[1]
                alt_name_domain = alt_name_domain.replace(".*", "", 1)
                urls.append("https://{}/".format(alt_name_domain))
            return urls
