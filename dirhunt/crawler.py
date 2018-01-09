import traceback
from concurrent.futures import ThreadPoolExecutor, Executor

import functools
from queue import Queue

import requests
from bs4 import BeautifulSoup
from requests import RequestException

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
        from dirhunt.processors import get_processor, GenericProcessor

        session = self.crawler.sessions.get_session()
        try:
            resp = session.get(self.url.url, stream=True, timeout=TIMEOUT, allow_redirects=False)
        except RequestException:
            return self
        text = ''
        soup = None
        if resp.status_code < 300 and self.maybe_directory():
            text = resp.raw.read(MAX_RESPONSE_SIZE, decode_content=True)
            soup = BeautifulSoup(text, 'html.parser')
        if self.maybe_directory():
            processor = get_processor(resp, text, self, soup) or GenericProcessor(resp, self)
            processor.process(text, soup)
            self.crawler.results.put(processor)
        # TODO: Podemos fijarnos en el processor.index_file. Si existe y es un 200, entonces es que existe.
        if self.exists is None and resp.status_code < 404:
            self.exists = True
        self.add_self_directories(True if (not self.maybe_rewrite() and self.exists) else None,
                                  'directory' if not self.maybe_rewrite() else None)
        self.crawler.processed[self.url.url] = self
        del self.crawler.processing[self.url.url]
        return self

    def maybe_rewrite(self):
        return self.type not in ['asset', 'directory']

    def maybe_directory(self):
        return self.type not in ['asset', 'document']

    def result(self):
        # Cuando se ejecuta el result() de future, si ya está processed, devolverse a sí mismo
        return self


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
    def __init__(self, max_workers=None):
        self.domains = set()
        self.results = Queue()
        self.sessions = Sessions()
        self.processing = {}
        self.processed = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

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
        url = crawler_url.url
        if not url.is_valid() or not self.in_domains(url.only_domain):
            return
        if url.url in self.processing or url.url in self.processed:
            return self.processing.get(url.url) or self.processed.get(url.url)
        fn = reraise_with_stack(crawler_url.start)
        if force:
            future = ThreadPoolExecutor(max_workers=1).submit(fn)
        else:
            future = self.executor.submit(fn)
        self.processing[url.url] = future
        return future

    def print_results(self):
        while True:
            result = self.results.get()
            if result.maybe_directory():
                print(result)
            if not self.processing:
                # Ended?
                print('Ended?')
                return
