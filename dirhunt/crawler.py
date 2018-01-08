import traceback
from concurrent.futures import ThreadPoolExecutor

import functools
from queue import Queue

import requests

from dirhunt.url import Url


MAX_RESPONSE_SIZE = 1024 * 512


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
            url.query = ''
            url.fragment = ''
        self.url = url
        self.crawler = crawler
        self.source = source
        self.exists = exists
        self.type = type

    def add_self_directories(self):
        for url in self.url.breadcrumb():
            self.crawler.add_url(CrawlerUrl(self.crawler, url, self.depth - 1, self, True, True))

    def start(self):
        from dirhunt.processors import get_processor, GenericProcessor

        if self.maybe_directory():
            session = self.crawler.sessions.get_session()
            resp = session.get(self.url.url, stream=True)
            text = resp.raw.read(MAX_RESPONSE_SIZE, decode_content=True)
            processor = get_processor(resp, text, self) or GenericProcessor(resp, text, self)
            processor.process()
            self.crawler.results.put(processor)
        self.crawler.processed.add(self.url.url)
        self.crawler.processing.remove(self.url.url)

    def maybe_directory(self):
        return self.type not in ['asset']


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
    def __init__(self, max_workers=4):
        self.results = Queue()
        self.sessions = Sessions()
        self.processing = set()
        self.processed = set()
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def add_urls(self, *urls):
        """Add urls to queue.
        """
        for url in urls:
            if not isinstance(url, CrawlerUrl):
                url = CrawlerUrl(self, url)
            self.add_url(url)

    def add_url(self, crawler_url):
        """Add url to queue"""
        url = crawler_url.url
        if url.url in self.processed or url.url in self.processing:
            return False
        self.processing.add(url.url)
        crawler_url.add_self_directories()
        self.executor.submit(reraise_with_stack(crawler_url.start))

    def print_results(self):
        while True:
            result = self.results.get()
            if result.maybe_directory():
                print(result)
