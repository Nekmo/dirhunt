import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from dirhunt.crawler import Crawler
from dirhunt.crawler_url import CrawlerUrl
from dirhunt.processors import ProcessHtmlRequest


class TestProcessHtmlRequest(unittest.TestCase):
    def get_crawler_url(self):
         crawler = Crawler()
         return CrawlerUrl(crawler, 'http://domain.com/path/')

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
