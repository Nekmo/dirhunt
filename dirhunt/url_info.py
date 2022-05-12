# -*- coding: utf-8 -*-
import re
import socket
import string
import sys
from operator import itemgetter
from threading import Lock

import six
from bs4 import BeautifulSoup
from click import get_terminal_size
from colorama import Fore
from requests import RequestException
from urllib3.exceptions import ReadTimeoutError

from dirhunt.cli import random_spinner
from dirhunt.colors import status_code_colors
from dirhunt.exceptions import EmptyError, RequestError
from dirhunt.pool import Pool
from dirhunt.utils import colored, remove_ansi_escape

MAX_RESPONSE_SIZE = 1024 * 512
DEFAULT_UNKNOWN_SIZE = '???'
EXTRA_ORDER = ['created_at', 'filesize']

def sizeof_fmt(num, suffix='B'):
    if num is None:
        return DEFAULT_UNKNOWN_SIZE
    if isinstance(num, six.string_types):
        num = int(num)
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%d%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%d%s%s" % (num, 'Yi', suffix)


def format_extra(extra, length=0):
    length = max(0, length - 2)
    return ('[{:<%d}]' % length).format(' '.join(map(itemgetter(1), sorted(extra.items(),
                                                                           key=lambda x: EXTRA_ORDER.index(x[0])))))


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
            with session.get(self.url.url, stream=True, verify=False, timeout=self.timeout,
                             allow_redirects=False) as resp:
                text = resp.raw.read(MAX_RESPONSE_SIZE, decode_content=True)
        except (RequestException, ReadTimeoutError, socket.timeout):
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

    def line(self, line_size, url_column, extra_len):
        if not len(self.text):
            raise EmptyError
        if len(self.url_info) + url_column + extra_len + 20 < line_size:
            return self.one_line(line_size, url_column, extra_len)
        else:
            return self.multi_line(line_size, extra_len)

    def one_line(self, line_size, url_column, extra_len):
        text = self.text[:line_size-url_column-len(list(remove_ansi_escape(self.url_info)))-3]
        out = self.url_info
        out += colored(('{:<%d}' % url_column).format(self.url.url), Fore.LIGHTBLUE_EX) + "  "
        if self.url.extra:
            out += colored(' {} '.format(format_extra(self.url.extra, extra_len)), Fore.LIGHTBLUE_EX)
        out += text
        return out

    def multi_line(self, line_size, extra_len):
        out = colored('┏', Fore.LIGHTBLUE_EX) + ' {} {}\n'.format(
            self.url_info, colored(self.url.url, Fore.LIGHTBLUE_EX)
        )
        out += colored('┗', Fore.LIGHTBLUE_EX)
        if self.url.extra:
            out += colored(' {}'.format(format_extra(self.url.extra, extra_len)), Fore.LIGHTBLUE_EX)
        out += ' {}'.format(self.text[:line_size-2])
        return out

    def json(self):
        return {
            'text': self.text,
            'url': self.url.json(),
            'data': {
                'text': self.data['text'],
                'title': self.data['title'],
                'body': self.data['body'],
                'resp': {
                    'headers': dict(self.data['resp'].headers),
                    'status_code': self.data['resp'].status_code,
                },
            }
        }


class UrlsInfo(Pool):
    url_len = 0
    empty_files = 0
    error_files = 0
    count = 0
    current = 0

    def __init__(self, processors, sessions, std=None, max_workers=None, progress_enabled=True, timeout=10,
                 save_info=False):
        super(UrlsInfo, self).__init__(max_workers)
        self.lock = Lock()
        self.processors = processors
        self.sessions = sessions
        self.std = std
        self.spinner = random_spinner()
        self.progress_enabled = progress_enabled
        self.timeout = timeout
        self.urls_info = []
        self.lines = []
        self.save_info = save_info

    def callback(self, url_len, extra_len, file):
        url_info = None
        try:
            url_info = self._get_url_info(file)
        except EmptyError:
            self.empty_files += 1
        except RequestError:
            self.error_files += 1
        self.lock.acquire()
        self.erase()
        if self.save_info:
            self.urls_info.append(url_info)
        if url_info:
            size = get_terminal_size()
            self.echo(url_info.line(size[0], url_len, extra_len))
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

    def _get_url_info(self, file):
        return UrlInfo(self.sessions, file, self.timeout)

    def getted_interesting_files(self):
        for processor in self.processors:
            for file in processor.interesting_files():
                yield file

    def start(self):
        self.echo('Starting...')
        self.count = 0
        url_len = 0
        extra_len = 0
        for file in self.getted_interesting_files():
            url_len = max(url_len, len(file.url))
            extra_len = max(extra_len, len(format_extra(file.extra)))
            self.count += 1
        for file in self.getted_interesting_files():
            # TODO: issue #26. Añadir len() de contenido extra
            self.submit(url_len, extra_len, file)
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
