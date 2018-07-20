# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.thread import _python_exit
from threading import Lock, ThreadError
import datetime

import atexit
import humanize as humanize
from click import get_terminal_size

from dirhunt._compat import queue, Queue
from dirhunt.cli import random_spinner
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.exceptions import EmptyError, RequestError, reraise_with_stack
from dirhunt.sessions import Sessions
from dirhunt.sources import Sources
from dirhunt.url_info import UrlsInfo

"""Flags importance"""


class Crawler(ThreadPoolExecutor):
    def __init__(self, max_workers=None, interesting_extensions=None, interesting_files=None, std=None,
                 progress_enabled=True, timeout=10, depth=3, not_follow_subdomains=False, exclude_sources=(),
                 not_allow_redirects=False):
        super(Crawler, self).__init__(max_workers)
        self.domains = set()
        self.results = Queue()
        self.index_of_processors = []
        self.sessions = Sessions()
        self.processing = {}
        self.processed = {}
        self.add_lock = Lock()
        self.spinner = random_spinner()
        self.start_dt = datetime.datetime.now()
        self.interesting_extensions = interesting_extensions or []
        self.interesting_files = interesting_files or []
        self.closing = False
        self.std = std or None
        self.progress_enabled = progress_enabled
        self.timeout = timeout
        self.not_follow_subdomains = not_follow_subdomains
        self.depth = depth
        self.sources = Sources(self.add_url, exclude_sources)
        self.not_allow_redirects = not_allow_redirects

    def add_init_urls(self, *urls):
        """Add urls to queue.
        """
        for crawler_url in urls:
            if not isinstance(crawler_url, CrawlerUrl):
                crawler_url = CrawlerUrl(self, crawler_url, depth=self.depth, timeout=self.timeout)
            self.add_domain(crawler_url.url.only_domain)
            self.add_url(crawler_url)

    def in_domains(self, domain):
        if self.not_follow_subdomains and domain not in self.domains:
            return False
        initial_domain = domain
        while True:
            if domain in self.domains:
                if initial_domain != domain:
                    # subdomain
                    self.add_domain(initial_domain)
                return True
            parts = domain.split('.')
            if len(parts) <= 2:
                return False
            domain = '.'.join(parts[1:])

    def add_domain(self, domain):
        if domain in self.domains:
            return
        self.domains.add(domain)
        self.sources.add_domain(domain)

    def add_url(self, crawler_url, force=False):
        """Add url to queue"""
        if not isinstance(crawler_url, CrawlerUrl):
            crawler_url = CrawlerUrl(self, crawler_url, depth=self.depth, timeout=self.timeout)
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
            future = self.submit(fn)
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

    def print_results(self, exclude=None, include=None):
        exclude = exclude or set()
        self.echo('Starting...')
        while True:
            result = None
            try:
                result = self.results.get(timeout=.5)
            except queue.Empty:
                pass
            self.erase()
            if result and result.maybe_directory() and not (result.crawler_url.flags & exclude) \
                    and (not include or (include & result.crawler_url.flags)):
                self.echo(result)
            self.print_progress()
            if self.sources.finished() and not self.processing:
                # Ended?
                self.erase()
                self.print_progress(True)
                return

    def print_urls_info(self):
        if not self.index_of_processors:
            self.echo('No interesting files detected ¯\_(ツ)_/¯')
            return
        self.echo('━' * get_terminal_size()[0])
        UrlsInfo(self.index_of_processors, self.sessions, self.std, self._max_workers, self.progress_enabled,
                 self.timeout).start()

    def restart(self):
        try:
            self.add_lock.release()
        except (ThreadError, RuntimeError):
            pass

    def close(self):
        self.closing = True
        self.shutdown(False)
        atexit.unregister(_python_exit)
