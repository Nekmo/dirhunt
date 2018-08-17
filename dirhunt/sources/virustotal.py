import string
from bs4 import BeautifulSoup

from dirhunt.sessions import Sessions
from dirhunt.sources.base import Source


ABUSE = 'VirusTotal is trying to prevent scraping and abuse, we are going to bother'
VT_URL = 'https://www.virustotal.com/es/domain/{domain}/information/'
ABUSE_MESSAGE_ERROR = "VirusTotal abuse has failed (scraping detected). Validate the captcha manually: {url}"


class VirusTotal(Source):
    def callback(self, domain):
        url = VT_URL.format(domain=domain)
        session = Sessions().get_session()
        html = session.get(url).text
        if ABUSE in html:
            self.add_error(ABUSE_MESSAGE_ERROR.format(url=url))
            return
        soup = BeautifulSoup(html, 'html.parser')

        for url in soup.select('#detected-urls .enum a'):
            self.add_result(url.text.strip(string.whitespace))
