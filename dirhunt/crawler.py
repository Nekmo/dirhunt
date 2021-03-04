# -*- coding: utf-8 -*-
import json
import multiprocessing
import os
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.thread import _python_exit
from threading import Lock, ThreadError
import datetime

import humanize as humanize
from click import get_terminal_size

from dirhunt import processors
from dirhunt import __version__
from dirhunt._compat import queue, Queue, unregister
from dirhunt.cli import random_spinner
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.exceptions import EmptyError, RequestError, reraise_with_stack, IncompatibleVersionError
from dirhunt.json_report import JsonReportEncoder
from dirhunt.sessions import Sessions
from dirhunt.sources import Sources
from dirhunt.url_info import UrlsInfo

"""Flags importance"""


resume_dir = os.path.expanduser('~/.cache/dirhunt/')


class Crawler(ThreadPoolExecutor):
    urls_info = None

    def __init__(self, max_workers=None, interesting_extensions=None, interesting_files=None, std=None,
                 progress_enabled=True, timeout=10, depth=3, not_follow_subdomains=False, exclude_sources=(),
                 not_allow_redirects=False, proxies=None, delay=0, limit=1000, to_file=None, user_agent=None,
                 cookies=None, headers=None):
        if not max_workers and not delay:
            max_workers = (multiprocessing.cpu_count() or 1) * 5
        elif not max_workers and delay:
            max_workers = len(proxies or [None])
        super(Crawler, self).__init__(max_workers)
        self.domains = set()
        self.results = Queue()
        self.index_of_processors = []
        self.proxies = proxies
        self.delay = delay
        self.sessions = Sessions(proxies, delay, user_agent, cookies, headers)
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
        self.exclude_sources = exclude_sources
        self.sources = Sources(self.add_url, self.add_message, exclude_sources)
        self.not_allow_redirects = not_allow_redirects
        self.limit = limit
        self.current_processed_count = 0
        self.to_file = to_file

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

    def add_message(self, body):
        from dirhunt.processors import Message
        self.results.put(Message(body))

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
            if (self.sources.finished() and not self.processing) or \
                    self.current_processed_count >= self.limit and self.limit:
                # Ended
                if self.current_processed_count >= self.limit and self.limit:
                    # Force shutdown
                    self.closing = True
                    self.shutdown()
                self.erase()
                self.print_progress(True)
                return

    def print_urls_info(self):
        if not self.index_of_processors:
            self.echo(r'No interesting files detected ¯\_(ツ)_/¯')
            return
        self.echo('━' * get_terminal_size()[0])
        self.urls_info = UrlsInfo(self.index_of_processors, self.sessions, self.std, self._max_workers,
                                  self.progress_enabled, self.timeout, bool(self.to_file))
        self.urls_info.start()

    def restart(self):
        try:
            self.add_lock.release()
        except (ThreadError, RuntimeError):
            pass

    def options(self):
        return {
            'interesting_extensions': self.interesting_extensions,
            'interesting_files': self.interesting_files,
            'timeout': self.interesting_files,
            'depth': self.interesting_files,
            'not_follow_subdomains': self.not_follow_subdomains,
            'exclude_sources': self.exclude_sources,
            'not_allow_redirects': self.not_allow_redirects,
            'proxies': self.proxies,
            'delay': self.delay,
            'limit': self.limit,
        }

    @property
    def options_file(self):
        checksum = sha256(json.dumps(self.options(), sort_keys=True).encode('utf-8')).hexdigest()
        return os.path.join(resume_dir, checksum)

    def get_resume_file(self):
        return self.to_file or self.options_file

    def close(self, create_resume=False):
        self.closing = True
        self.shutdown(False)
        if create_resume:
            self.create_report(self.get_resume_file())
        unregister(_python_exit)

    def create_report(self, to_file):
        """Write to a file a report with current json() state. This file can be read
        to continue an analysis."""
        to_file = os.path.abspath(to_file)
        directory = os.path.dirname(to_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        data = self.json()
        with open(to_file, 'w') as f:
            json.dump(data, f, cls=JsonReportEncoder, indent=4, sort_keys=True)

    def resume(self, path):
        resume_data = json.load(open(path))
        file_version = resume_data.get('version')
        if file_version != __version__:
            raise IncompatibleVersionError(
                'Analysis file incompatible with the current version of dirhunt. '
                'Dirhunt version: {}. File version: {}'.format(__version__, file_version)
            )
        for data in resume_data['processed']:
            crawler_url_data = data['crawler_url']
            url = crawler_url_data['url']['address']
            crawler_url = CrawlerUrl(self, url, crawler_url_data['depth'], None, crawler_url_data['exists'],
                                     crawler_url_data['type'])
            crawler_url.flags = set(crawler_url_data['flags'])
            crawler_url.processor_data = data
            self.processed[url] = crawler_url
            self.echo(data['line'])
        for url in resume_data['processing']:
            self.add_url(url)

    def json(self):
        urls_infos = self.urls_info.urls_info if self.urls_info else []
        urls_infos = [urls_info.json() for urls_info in urls_infos]
        return {
            'version': __version__,
            'current_processed_count': self.current_processed_count,
            'domains': self.domains,
            'index_of_processors': self.index_of_processors,
            'processing': list(self.processing.keys()),
            'processed': list(filter(bool, [processed.processor_data for processed in self.processed.values()])),
            'urls_infos': urls_infos,
        }
