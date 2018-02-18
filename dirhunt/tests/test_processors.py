import unittest
from unittest.mock import patch

import requests
import requests_mock
from bs4 import BeautifulSoup

from dirhunt.crawler import Crawler
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.processors import ProcessHtmlRequest, ProcessIndexOfRequest, ProcessBlankPageRequest


class ProcessTestBase(object):
    url = 'http://domain.com/path/'

    def get_crawler_url(self):
         crawler = Crawler(interesting_extensions=['php'], interesting_files=['error_log'])
         return CrawlerUrl(crawler, self.url)


class TestProcessHtmlRequest(ProcessTestBase, unittest.TestCase):

    def test_links(self):
        html = """
        <a href="..">Top</a>
        <a href="dir/">dir</a>
        <a href="foo.php">foo.php</a>
        <a href="/spam/eggs">Eggs</a>
        """
        with patch.object(Crawler, 'add_url') as mock_method:
            process = ProcessHtmlRequest(None, self.get_crawler_url())
            soup = BeautifulSoup(html, 'html.parser')
            process.links(soup)
            urls = [crawler_url[0][0].url for crawler_url in mock_method.call_args_list]
            self.assertEqual(urls, [
                'http://domain.com/',
                'http://domain.com/path/dir/',
                'http://domain.com/path/foo.php',
                'http://domain.com/spam/eggs',
            ])

    def test_assets(self):
        html = """
        <link rel="stylesheet" type="text/css" href="spam/theme.css">
        <script src="myscripts.js"></script>
        <script src="//cnd.extern.com/script.js"></script>        
        <img src="/smiley.gif"> 
        <img src="proto:invalid:url"> <!-- Ignore -->
        """
        with patch.object(Crawler, 'add_url') as mock_method:
            process = ProcessHtmlRequest(None, self.get_crawler_url())
            soup = BeautifulSoup(html, 'html.parser')
            process.assets(soup)
            urls = [crawler_url[0][0].url for crawler_url in mock_method.call_args_list]
            self.assertEqual(urls, [
                'http://domain.com/path/spam/theme.css',
                'http://domain.com/path/myscripts.js',
                'http://cnd.extern.com/script.js',
                'http://domain.com/smiley.gif',
            ])


class TestProcessIndexOfRequest(ProcessTestBase, unittest.TestCase):
    html = """
    <html><head><title>Index Of</title></head><body>
    <a href="..">Top</a>
    <a href="dir/">dir</a>
    <a href="foo.php">foo.php</a>
    <a href="error_log">error_log</a>
    <a href="/spam/eggs">Eggs</a></body></html>
    """

    def test_is_applicable(self):
        crawler_url = self.get_crawler_url()
        with requests_mock.mock() as m:
            m.get('http://test.com', text=self.html, headers={'Content-Type': 'text/html'})
            r = requests.get('http://test.com')
            soup = BeautifulSoup(self.html, 'html.parser')
            self.assertTrue(ProcessIndexOfRequest.is_applicable(r, self.html, crawler_url, soup))

    def test_process(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(self.html, BeautifulSoup(self.html, 'html.parser'))
        urls = [file.url for file in process.files]
        self.assertEqual(urls, [
            'http://domain.com/',
            'http://domain.com/path/dir/',
            'http://domain.com/path/foo.php',
            'http://domain.com/path/error_log',
            'http://domain.com/spam/eggs',
        ])

    def test_interesting_ext_files(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(self.html, BeautifulSoup(self.html, 'html.parser'))
        self.assertEqual([file.url for file in process.interesting_ext_files()], ['http://domain.com/path/foo.php'])

    def test_interesting_name_files(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(self.html, BeautifulSoup(self.html, 'html.parser'))
        self.assertEqual([file.url for file in process.interesting_name_files()], ['http://domain.com/path/error_log'])

    def test_interesting_files(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(self.html, BeautifulSoup(self.html, 'html.parser'))
        self.assertEqual([file.url for file in process.interesting_files()], [
            'http://domain.com/path/foo.php',
            'http://domain.com/path/error_log'
        ])

    def test_flag_nothing(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process('', BeautifulSoup('', 'html.parser'))
        self.assertEqual(process.flags, {'index_of', 'index_of.nothing'})


class TestProcessBlankPageRequest(ProcessTestBase, unittest.TestCase):
    def test_is_applicable(self):
        html = '<html><!-- Foo --><head><title>Foo</title><script src="foo.js"></script></head><body>  </body></html>'
        crawler_url = self.get_crawler_url()
        with requests_mock.mock() as m:
            m.get('http://test.com', text=html, headers={'Content-Type': 'text/html'})
            r = requests.get('http://test.com')
            soup = BeautifulSoup(html, 'html.parser')
            self.assertTrue(ProcessBlankPageRequest.is_applicable(r, html, crawler_url, soup))

    def test_not_applicable(self):
        html = '<html><head><title>Foo</title></head><body>  Hello    </body></html>'
        crawler_url = self.get_crawler_url()
        with requests_mock.mock() as m:
            m.get('http://test.com', text=html, headers={'Content-Type': 'text/html'})
            r = requests.get('http://test.com')
            soup = BeautifulSoup(html, 'html.parser')
            self.assertFalse(ProcessBlankPageRequest.is_applicable(r, html, crawler_url, soup))
