from bs4 import BeautifulSoup
from requests import RequestException

MAX_RESPONSE_SIZE = 1024 * 512
TIMEOUT = 10


class UrlInfo(object):
    def __init__(self, sessions, url):
        self.sessions = sessions
        self.url = url

    def data(self):
        session = self.sessions.get_session()
        try:
            resp = session.get(self.url.url, stream=True, timeout=TIMEOUT, allow_redirects=False)
        except RequestException as e:
            return
        try:
            text = resp.raw.read(MAX_RESPONSE_SIZE, decode_content=True)
        except RequestException as e:
            return
        soup = BeautifulSoup(text, 'html.parser')
        title = soup.select_one('title')
        body = soup.select_one('body')
        return {
            'text': text,
            'soup': soup,
            'title': title,
            'body': body,
        }
