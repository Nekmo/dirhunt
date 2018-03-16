# -*- coding: utf-8 -*-
import traceback
from concurrent.futures import ThreadPoolExecutor
import functools
from concurrent.futures.thread import _python_exit
from threading import Lock, ThreadError
import datetime

import atexit
import humanize as humanize

from dirhunt._compat import queue, Queue, get_terminal_size
from dirhunt.cli import random_spinner
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.sessions import Sessions
from dirhunt.url_info import UrlInfo

"""Flags importance"""


def reraise_with_stack(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            raise e
    return wrapped


class Crawler(object):
    def __init__(self, max_workers=None, interesting_extensions=None, interesting_files=None, std=None,
                 progress_enabled=True):
        self.domains = set()
        self.results = Queue()
        self.index_of_processors = []
        self.sessions = Sessions()
        self.processing = {}
        self.processed = {}
        self.max_workers = max_workers
        self.add_lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.spinner = random_spinner()
        self.start_dt = datetime.datetime.now()
        self.interesting_extensions = interesting_extensions or []
        self.interesting_files = interesting_files or []
        self.closing = False
        self.std = std or None
        self.progress_enabled = progress_enabled

    def add_init_urls(self, *urls):
        """Add urls to queue.
        """
        for crawler_url in urls:
            if not isinstance(crawler_url, CrawlerUrl):
                crawler_url = CrawlerUrl(self, crawler_url)
            self.domains.add(crawler_url.url.only_domain)
            self.add_url(crawler_url)

    def in_domains(self, domain):
        initial_domain = domain
        while True:
            if domain in self.domains:
                if initial_domain != domain:
                    # subdomain
                    self.domains.add(domain)
                return True
            parts = domain.split('.')
            if len(parts) <= 2:
                return False
            domain = '.'.join(parts[1:])

    def add_url(self, crawler_url, force=False):
        """Add url to queue"""

        self.add_lock.acquire()
        url = crawler_url.url
        if not url.is_valid() or not url.only_domain or not self.in_domains(url.only_domain):
            self.add_lock.release()
            return
        if url.url in self.processing or url.url in self.processed:
            self.add_lock.release()
            return self.processing.get(url.url) or self.processed.get(url.url)

        fn = reraise_with_stack(crawler_url.start)
        if self.closing:
            self.add_lock.release()
            return
        if force:
            future = ThreadPoolExecutor(max_workers=1).submit(fn)
        else:
            future = self.executor.submit(fn)
        self.processing[url.url] = future
        self.add_lock.release()
        return future

    def echo(self, body):
        if self.std is None:
            return
        # TODO: remove ANSI chars on is not tty
        self.std.write(str(body))
        self.std.write('\n')

    def erase(self):
        if self.std is None or not self.std.isatty():
            return
        CURSOR_UP_ONE = '\x1b[1A'
        ERASE_LINE = '\x1b[2K'
        # This can be improved. In the future we may want to define stdout/stderr with an cli option
        # fn = sys.stderr.write if sys.stderr.isatty() else sys.stdout.write
        self.std.write(CURSOR_UP_ONE + ERASE_LINE)

    def print_progress(self, finished=False):
        if not self.progress_enabled:
            # Cancel print progress on
            return
        self.echo('{} {} {}'.format(
            next(self.spinner),
            'Finished after' if finished else 'Started',
            (humanize.naturaldelta if finished else humanize.naturaltime)(datetime.datetime.now() - self.start_dt),
        ))

    def print_results(self, exclude=None):
        exclude = exclude or set()
        self.echo('Starting...')
        while True:
            result = None
            try:
                result = self.results.get(timeout=.5)
            except queue.Empty:
                pass
            self.erase()
            if result and result.maybe_directory() and not (result.crawler_url.flags & exclude):
                self.echo(result)
            self.print_progress()
            if not self.processing:
                # Ended?
                self.erase()
                self.print_progress(True)
                self.echo('End')
                return

    def getted_interesting_files(self):
        for processor in self.index_of_processors:
            for file in processor.interesting_files():
                yield file

    def print_urls_info(self):
        url_len = 0
        for file in self.getted_interesting_files():
            url_len = max(url_len, len(file.url))
        for processor in self.index_of_processors:
            for file in processor.interesting_files():
                size = get_terminal_size()
                line = UrlInfo(self.sessions, file.address).line(size.columns, url_len)
                print(line)

    def restart(self):
        try:
            self.add_lock.release()
        except (ThreadError, RuntimeError):
            pass

    def close(self):
        self.closing = True
        self.executor.shutdown(False)
        atexit.unregister(_python_exit)
