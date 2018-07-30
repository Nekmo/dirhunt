# -*- coding: utf-8 -*-
import re
import string
import sys
from threading import Lock

from bs4 import BeautifulSoup
from click import get_terminal_size
from colorama import Fore
from requests import RequestException

from dirhunt.cli import random_spinner
from dirhunt.colors import status_code_colors
from dirhunt.exceptions import EmptyError, RequestError
from dirhunt.pool import Pool
from dirhunt.utils import colored, remove_ansi_escape

MAX_RESPONSE_SIZE = 1024 * 512
DEFAULT_UNKNOWN_SIZE = '???'


def sizeof_fmt(num, suffix='B'):
    if num is None:
        return DEFAULT_UNKNOWN_SIZE
    if isinstance(num, str):
        num = int(num)
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%d%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%d%s%s" % (num, 'Yi', suffix)


class UrlInfo(object):
    _data = None
    _url_info = None
    _text = None

    def __init__(self, sessions, url, timeout=10):
        self.sessions = sessions
        self.url = url
        self.timeout = timeout

    def get_data(self):
        session = self.sessions.get_session()
        try:
            resp = session.get(self.url.url, stream=True, verify=False, timeout=self.timeout, allow_redirects=False)
        except RequestException:
            raise RequestError
        try:
            text = resp.raw.read(MAX_RESPONSE_SIZE, decode_content=True)
        except RequestException:
            raise RequestError
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

    @property
    def data(self):
        if self._data is None:
            self._data = self.get_data()
        return self._data

    def get_url_info(self):
        size = self.data['resp'].headers.get('Content-Length')
        size = len(self.data.get('text', '')) if size is None else size
        status_code = int(self.data['resp'].status_code)
        out = colored('({})'.format(status_code), status_code_colors(status_code)) + " "
        out += colored('({:>6})'.format(sizeof_fmt(size)), Fore.LIGHTYELLOW_EX) + " "
        return out

    @property
    def url_info(self):
        if self._url_info is None:
            self._url_info = self.get_url_info()
        return self._url_info

    def get_text(self):
        text = self.data['title'] or self.data['body'] or self.data['text'] or ''
        text = re.sub('[{}]'.format(string.whitespace), ' ', text)
        return re.sub(' +', ' ', text).strip(' ')

    @property
    def text(self):
        if self._text is None:
            self._text = self.get_text()
        return self._text

    def line(self, line_size, url_column):
        if not len(self.text):
            raise EmptyError
        if len(self.url_info) + url_column + 20 < line_size:
            return self.one_line(line_size, url_column)
        else:
            return self.multi_line(line_size)

    def one_line(self, line_size, url_column):
        text = self.text[:line_size-url_column-len(list(remove_ansi_escape(self.url_info)))-3]
        out = self.url_info
        out += colored(('{:<%d}' % url_column).format(self.url.url), Fore.LIGHTBLUE_EX) + "  "
        out += text
        return out

    def multi_line(self, line_size):
        out = colored('┏', Fore.LIGHTBLUE_EX) + ' {} {}\n'.format(
            self.url_info, colored(self.url.url, Fore.LIGHTBLUE_EX)
        )
        out += colored('┗', Fore.LIGHTBLUE_EX) + ' {}'.format(self.text[:line_size-2])
        return out


class UrlsInfo(Pool):
    url_len = 0
    empty_files = 0
    error_files = 0
    count = 0
    current = 0

    def __init__(self, processors, sessions, std=None, max_workers=None, progress_enabled=True, timeout=10):
        super(UrlsInfo, self).__init__(max_workers)
        self.lock = Lock()
        self.processors = processors
        self.sessions = sessions
        self.std = std
        self.spinner = random_spinner()
        self.progress_enabled = progress_enabled
        self.timeout = timeout

    def callback(self, url_len, file):
        line = None
        try:
            line = self._get_url_info(url_len, file)
        except EmptyError:
            self.empty_files += 1
        except RequestError:
            self.error_files += 1
        self.lock.acquire()
        self.erase()
        if line:
            self.echo(line)
        self.print_progress()
        self.lock.release()

    def erase(self):
        if self.std is None or not self.std.isatty():
            return
        CURSOR_UP_ONE = '\x1b[1A'
        ERASE_LINE = '\x1b[2K'
        # This can be improved. In the future we may want to define stdout/stderr with an cli option
        # fn = sys.stderr.write if sys.stderr.isatty() else sys.stdout.write
        self.std.write(CURSOR_UP_ONE + ERASE_LINE)

    def echo(self, body):
        if self.std is None:
            return
        # TODO: remove ANSI chars on is not tty
        self.std.write(str(body))
        self.std.write('\n')

    def _get_url_info(self, url_len, file):
        size = get_terminal_size()
        return UrlInfo(self.sessions, file.address, self.timeout).line(size[0], url_len)

    def getted_interesting_files(self):
        for processor in self.processors:
            for file in processor.interesting_files():
                yield file

    def start(self):
        self.echo('Starting...')
        self.count = 0
        url_len = 0
        for file in self.getted_interesting_files():
            url_len = max(url_len, len(file.url))
            self.count += 1
        for file in self.getted_interesting_files():
            self.submit(url_len, file)
        out = ''
        if self.empty_files:
            out += 'Empty files: {} '.format(self.empty_files)
        if self.error_files:
            out += 'Error files: {}'.format(self.error_files)
        if out:
            self.echo(out)

    def print_progress(self):
        if not self.progress_enabled:
            # Cancel print progress on
            return
        self.current += 1
        self.echo(('{} Interesting files {:>%d} / {}' % len(str(self.count))).format(
            next(self.spinner),
            self.current,
            self.count,
        ))
