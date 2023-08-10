import json

from requests.exceptions import RequestException
from dirhunt.sessions import Sessions
from dirhunt.sources.base import SourceBase


WAYBACK_URL = "https://web.archive.org/cdx/search/cdx"
WAYBACK_PARAMS = {"fl": "original", "collapse": "urlkey", "limit": "10000"}
DEFAULT_ENCODING = "utf-8"
BASE64_URL = "%22data:%3C;base64"
TIMEOUT = 10


class Wayback(SourceBase):
    def callback(self, domain):
        session = Sessions().get_session()
        try:
            with session.get(
                WAYBACK_URL,
                params=dict(WAYBACK_PARAMS, url="*.{}".format(domain)),
                stream=True,
                timeout=TIMEOUT,
            ) as response:
                response.raise_for_status()
                for line in filter(bool, response.iter_lines()):
                    if isinstance(line, bytes):
                        line = line.decode(response.encoding or DEFAULT_ENCODING)
                    if BASE64_URL in line:
                        continue
                    self.add_result(line)
        except RequestException as e:
            self.add_error("Error on Wayback source: {}".format(e))
            return
