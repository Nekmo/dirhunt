import string
from bs4 import BeautifulSoup
from requests import RequestException

from dirhunt.sessions import Sessions
from dirhunt.sources.base import Source


ABUSE = 'VirusTotal is trying to prevent scraping and abuse, we are going to bother'
VT_URL = 'https://www.virustotal.com/es/domain/{domain}/information/'
ABUSE_MESSAGE_ERROR = "VirusTotal abuse has failed (scraping detected). Validate the captcha manually: {url}"


class VirusTotal(Source):
    def callback(self, domain):
        url = VT_URL.format(domain=domain)
        session = Sessions().get_session()
        try:
            with session.get(url) as response:
                html = response.text
        except RequestException as e:
            self.add_error('Error on Crt.sh source: {}'.format(e))
            return
        if ABUSE in html:
            self.add_error(ABUSE_MESSAGE_ERROR.format(url=url))
            return
        soup = BeautifulSoup(html, 'html.parser')

        for url in soup.select('#detected-urls .enum a'):
            self.add_result(url.text.strip(string.whitespace))
