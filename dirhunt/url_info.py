import re
import string
import sys
from bs4 import BeautifulSoup
from requests import RequestException

MAX_RESPONSE_SIZE = 1024 * 512
TIMEOUT = 10


def sizeof_fmt(num, suffix='B'):
    if num is None:
        return '???'
    if isinstance(num, str):
        num = int(num)
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%d%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%d%s%s" % (num, 'Yi', suffix)


class UrlInfo(object):
    def __init__(self, sessions, url):
        self.sessions = sessions
        self.url = url

    def data(self):
        session = self.sessions.get_session()
        try:
            resp = session.get(self.url.url, stream=True, timeout=TIMEOUT, allow_redirects=False)
        except RequestException:
            return
        try:
            text = resp.raw.read(MAX_RESPONSE_SIZE, decode_content=True)
        except RequestException:
            return
        try:
            soup = BeautifulSoup(text, 'html.parser')
        except NotImplementedError:
            soup = title = body = None
        else:
            title = soup.select_one('title')
            if title:
                title = title.string
            body = soup.select_one('body')
            if body:
                body = str(body)
        if sys.version_info >= (3,):
            text = text.decode('utf-8', errors='ignore')
        return {
            'resp': resp,
            'text': text,
            'soup': soup,
            'title': title,
            'body': body,
        }

    def line(self, line_size, url_column):
        data = self.data()
        text = data['title'] or data['body'] or data['text'] or ''
        text = re.sub('[{}]'.format(string.whitespace), ' ', text)
        text = re.sub(' +', ' ', text)
        f = '({}) ({:>6}) '
        text = text[:line_size-url_column-len(f.format(200, '100KiB'))-3]
        f += '{:<%d}' % url_column
        size = data['resp'].headers.get('Content-Length')
        size = len(data.get('text', '')) if size is None else size
        return (f + '  {}').format(
            data['resp'].status_code,
            sizeof_fmt(size),
            self.url.url,
            text
        )
