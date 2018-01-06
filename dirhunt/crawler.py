from concurrent.futures import ThreadPoolExecutor

import requests

from dirhunt.url import Url


class ProcessRequest(object):
    pass


class CrawlerRequest(object):
    def __init__(self, url, crawler):
        """

        :type crawler: Crawler
        """
        self.url = url
        self.crawler = crawler

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

    def add_url(self, url):
        """Add url to queue"""
        url = Url(url)
        url.query = ''
        url.fragment = ''
        url = url.url
        print(url)
        if url in self.processed or url in self.processing:
            return False
        self.processing.add(url)
        self.executor.submit(CrawlerRequest(url, self).start)
