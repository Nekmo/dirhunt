import unittest

import requests
import requests_mock

from dirhunt.crawler_url import CrawlerUrl
from dirhunt.tests.base import CrawlerTestBase

from dirhunt.tests._compat import patch, Mock


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
        self.assertEqual(crawler.current_processed_count, 1)

    @requests_mock.mock()
    def test_session_exception(self, req_mock):
        req_mock.get(self.url, exc=requests.exceptions.ConnectTimeout)
        crawler = self.get_crawler()
        with patch('dirhunt.crawler_url.CrawlerUrl.close') as m:
            crawler_url = CrawlerUrl(crawler, self.url)
            self.assertEqual(crawler_url.start(), crawler_url)
            self.assertEqual(crawler.current_processed_count, 1)
            m.assert_called_once()

    def test_session_read_exception(self):
        crawler = self.get_crawler()
        crawler.sessions = Mock()
        crawler.sessions.get_session.return_value.get.return_value.status_code = 200
        crawler.sessions.get_session.return_value.get.return_value.raw.read.side_effect = \
            requests.exceptions.ConnectTimeout()
        with patch('dirhunt.crawler_url.CrawlerUrl.close') as m:
            crawler_url = CrawlerUrl(crawler, self.url)
            self.assertEqual(crawler_url.start(), crawler_url)
            self.assertEqual(crawler.current_processed_count, 1)
            m.assert_called_once()
