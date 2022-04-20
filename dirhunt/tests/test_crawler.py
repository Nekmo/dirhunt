import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import mock_open

from dirhunt import __version__
from dirhunt.tests._compat import Mock, patch
from dirhunt.crawler import Crawler
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.processors import GenericProcessor
from dirhunt.tests.base import CrawlerTestBase


REPORT_DATA = {
    "version": __version__,
    "processed": [
        {
            "crawler_url": {
                "depth": 3,
                "exists": None,
                "flags": [
                    "302",
                    "redirect"
                ],
                "type": "directory",
                "url": {
                    "address": "https://site.com/",
                    "domain": "site.com"
                }
            },
            "line": "",
            "processor_class": "ProcessRedirect",
            "status_code": 302
        },
    ],
    "processing": [
        "https://site.com/path/",
    ]
}


class TestCrawler(CrawlerTestBase, unittest.TestCase):
    def test_print_results(self):
        crawler = self.get_crawler()
        crawler_url = CrawlerUrl(crawler, self.url)
        crawler.results.put(GenericProcessor(None, crawler_url))
        crawler.print_results()

    @patch('dirhunt.crawler.json.dump')
    @patch('builtins.open')
    def test_create_report(self, _, mock_dump):
        crawler = self.get_crawler()
        crawler.results.put(GenericProcessor(None, CrawlerUrl(crawler, self.url)))
        crawler.create_report(crawler.get_resume_file())
        mock_dump.assert_called_once()

    @patch('dirhunt.crawler.json.load', return_value=REPORT_DATA)
    @patch('dirhunt.crawler.Crawler.echo', return_value=REPORT_DATA)
    @patch('dirhunt.crawler.Crawler.add_url', return_value=REPORT_DATA)
    @patch('builtins.open')
    def test_resume(self, _, m1, m2, m3):
        crawler = self.get_crawler()
        crawler.resume(crawler.get_resume_file())
        m3.assert_called_once()
        m2.assert_called_once()
        m1.assert_called_once_with(REPORT_DATA['processing'][0], lock=False)

    def test_print_results_limit(self):
        crawler = self.get_crawler(limit=1)
        crawler.current_processed_count = 1
        crawler_url = CrawlerUrl(crawler, self.url)
        crawler.results.put(GenericProcessor(None, crawler_url))
        crawler.print_results()
        self.assertTrue(crawler.closing)

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

    @patch('dirhunt.crawler.Crawler.create_report')
    @patch('dirhunt.crawler.unregister')
    def test_close(self, m1, m2):
        crawler = self.get_crawler()
        crawler.close(True)
        m2.assert_called_once()
        m1.assert_called_once()
