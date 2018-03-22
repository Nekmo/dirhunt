import unittest
from concurrent.futures import ThreadPoolExecutor

from dirhunt.tests._compat import Mock, patch
from dirhunt.crawler import Crawler
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.processors import GenericProcessor
from dirhunt.tests.base import CrawlerTestBase


class TestCrawler(CrawlerTestBase, unittest.TestCase):
    def test_print_results(self):
        crawler = self.get_crawler()
        crawler_url = CrawlerUrl(crawler, self.url)
        crawler.results.put(GenericProcessor(None, crawler_url))
        crawler.print_results()

    def test_add_url(self):
        crawler = self.get_crawler()
        crawler.domains.add('domain.com')
        crawler_url = CrawlerUrl(crawler, self.url)
        with patch.object(ThreadPoolExecutor, 'submit') as mock_method:
            crawler.add_url(crawler_url)

    def test_add_init_urls(self):
        crawler = self.get_crawler()
        with patch.object(Crawler, 'add_url') as m:
            crawler.add_init_urls(self.url)
            m.assert_called_once()
            self.assertEqual(crawler.domains, {'domain.com'})

    def test_erase_tty(self):
        crawler = self.get_crawler()
        crawler.std = Mock(**{'isatty.return_value': True})
        crawler.erase()
