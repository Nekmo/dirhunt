from concurrent.futures import ThreadPoolExecutor

import requests

from dirhunt.url import Url


class ProcessRequest(object):
    def __init__(self, request):
        pass


class CrawlerRequest(object):
    def __init__(self, url, crawler, depth=3):
        """

        :type crawler: Crawler
        :type depth: int Máxima recursión sin haber subido respecto esta url
        """
        self.depth = depth
        self.url = url
        self.crawler = crawler
        self.add_self_directories()

    def add_self_directories(self):
        for url in Url(self.url).breadcrumb():
            self.crawler.add_url(url.url)

    def start(self):
        session = self.crawler.sessions.get_session()
        session.get(self.url)
        self.crawler.processing.remove(self.url)
        self.crawler.processed.add(self.url)


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
        self.sessions = Sessions()
        self.processing = set()
        self.processed = set()
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def add_urls(self, *urls):
        """Add urls to queue.
        """
        for url in urls:
            self.add_url(url)

    def add_url(self, url, depth=3):
        """Add url to queue"""
        url = Url(url)
        url.query = ''
        url.fragment = ''
        url = url.url
        if url in self.processed or url in self.processing:
            return False
        print(url)
        self.processing.add(url)
        self.executor.submit(CrawlerRequest(url, self, depth).start)
