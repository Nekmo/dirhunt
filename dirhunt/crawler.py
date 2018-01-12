import queue
import traceback
from concurrent.futures import ThreadPoolExecutor
import functools
from concurrent.futures.thread import _python_exit
from queue import Queue
from threading import Lock, ThreadError
import datetime

import atexit
import humanize as humanize
import requests
import sys
from bs4 import BeautifulSoup
from requests import RequestException

from dirhunt.cli import random_spinner
from dirhunt.url import Url


MAX_RESPONSE_SIZE = 1024 * 512
TIMEOUT = 10


def reraise_with_stack(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            raise e
    return wrapped


class CrawlerUrl(object):
    def __init__(self, crawler, url, depth=3, source=None, exists=None, type=None):
        """

        :type crawler: Crawler
        :type depth: int Máxima recursión sin haber subido respecto esta url
        """
        self.flags = set()
        self.depth = depth
        if not isinstance(url, Url):
            url = Url(url)
        if url.is_valid():
            url.query = ''
            url.fragment = ''
        self.url = url
        self.crawler = crawler
        self.source = source
        self.exists = exists
        self.type = type
        self.resp = None

    def add_self_directories(self, exists=None, type_=None):
        for url in self.url.breadcrumb():
            self.crawler.add_url(CrawlerUrl(self.crawler, url, self.depth - 1, self, exists, type_))
            # TODO: si no se puede añadir porque ya se ha añadido, establecer como que ya existe si la orden es exists

    def start(self):
        from dirhunt.processors import get_processor, GenericProcessor, Error

        session = self.crawler.sessions.get_session()
        try:
            resp = session.get(self.url.url, stream=True, timeout=TIMEOUT, allow_redirects=False)
        except RequestException as e:
            self.crawler.results.put(Error(self, e))
            self.close()
            return self

        self.set_type(resp.headers.get('Content-Type'))
        self.flags.add(str(resp.status_code))
        text = ''
        soup = None

        if resp.status_code < 300 and self.maybe_directory():
            text = resp.raw.read(MAX_RESPONSE_SIZE, decode_content=True)
            soup = BeautifulSoup(text, 'html.parser')
        if self.maybe_directory():
            processor = get_processor(resp, text, self, soup) or GenericProcessor(resp, self)
            processor.process(text, soup)
            self.crawler.results.put(processor)
            self.flags.update(processor.flags)
        # TODO: Podemos fijarnos en el processor.index_file. Si existe y es un 200, entonces es que existe.
        if self.exists is None and resp.status_code < 404:
            self.exists = True
        self.add_self_directories(True if (not self.maybe_rewrite() and self.exists) else None,
                                  'directory' if not self.maybe_rewrite() else None)
        self.close()
        return self

    def set_type(self, content_type):
        from dirhunt.processors import INDEX_FILES
        if not self.type and not (content_type or '').startswith('text/html'):
            self.type = 'asset'
        if not self.type and (content_type or '').startswith('text/html') and self.url.name in INDEX_FILES:
            self.type = 'document'
    def maybe_rewrite(self):
        return self.type not in ['asset', 'directory']

    def maybe_directory(self):
        return self.type not in ['asset', 'document', 'rewrite']

    def result(self):
        # Cuando se ejecuta el result() de future, si ya está processed, devolverse a sí mismo
        return self

    def close(self):
        self.crawler.processed[self.url.url] = self
        del self.crawler.processing[self.url.url]


class Session(object):
    def __init__(self, sessions):
        self.sessions = sessions
        self.session = requests.Session()

    def get(self, url, **kwargs):
        response = self.session.get(url, **kwargs)
        self.sessions.availables.add(self)
        return response


class Sessions(object):
    def __init__(self):
        self.availables = set()

    def get_session(self):
        if not self.availables:
            return self.create_session()
        return self.availables.pop()

    def create_session(self):
        return Session(self)


class Crawler(object):
    def __init__(self, max_workers=None, interesting_extensions=None, interesting_files=None):
        self.domains = set()
        self.results = Queue()
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

    def erase(self):
        if not sys.stdout.isatty():
            return
        CURSOR_UP_ONE = '\x1b[1A'
        ERASE_LINE = '\x1b[2K'
        sys.stdout.write(CURSOR_UP_ONE + ERASE_LINE)

    def print_progress(self, finished=False):
        if not sys.stdout.isatty():
            return
        print('{} {} {}'.format(
            next(self.spinner),
            'Finished after' if finished else 'Started',
            (humanize.naturaldelta if finished else humanize.naturaltime)(datetime.datetime.now() - self.start_dt),
        ))

    def print_results(self, exclude=None):
        exclude = exclude or set()
        print('Starting...')
        while True:
            result = None
            try:
                result = self.results.get(timeout=.5)
            except queue.Empty:
                pass
            self.erase()
            if result and result.maybe_directory() and not (result.crawler_url.flags & exclude):
                print(result)
            self.print_progress()
            if not self.processing:
                # Ended?
                self.erase()
                self.print_progress(True)
                print('End')
                return

    def restart(self):
        try:
            self.add_lock.release()
        except (ThreadError, RuntimeError):
            pass

    def close(self):
        self.closing = True
        self.executor.shutdown(False)
        atexit.unregister(_python_exit)
