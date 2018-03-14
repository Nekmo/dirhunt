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
            pass

