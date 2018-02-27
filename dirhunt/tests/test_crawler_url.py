import unittest

import requests_mock

from dirhunt.crawler_url import CrawlerUrl
from dirhunt.tests.base import CrawlerTestBase


class TestCrawlerUrl(CrawlerTestBase, unittest.TestCase):
    def test_start(self):
        crawler = self.get_crawler()
        crawler.closing = True
        crawler_url = CrawlerUrl(crawler, self.url)
        crawler.processing[self.url] = crawler_url
        with requests_mock.mock() as m:
            m.get(self.url, headers={'Content-Type': 'text/html'})
            crawler_url.start()
        self.assertIn(self.url, crawler.processed)
        self.assertNotIn(self.url, crawler.processing)
