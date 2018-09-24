import unittest
from dirhunt.tests._compat import patch

import requests
import requests_mock
from bs4 import BeautifulSoup

from dirhunt.crawler import Crawler
from dirhunt.processors import ProcessHtmlRequest, ProcessIndexOfRequest, ProcessBlankPageRequest, ProcessNotFound, \
    ProcessRedirect, Error
from dirhunt.tests.base import CrawlerTestBase


class TestError(CrawlerTestBase, unittest.TestCase):
    def test_str(self):
        e = Error(self.get_crawler_url(), Exception('Foo bar'))
        self.assertIn('Foo bar', str(e))


class TestProcessRedirect(CrawlerTestBase, unittest.TestCase):
    html = ''

    def test_is_applicable(self):
        with requests_mock.mock() as m:
            m.register_uri('GET', 'http://test.com', text=self.html, headers={'Content-Type': 'text/html'},
                           status_code=300)
            r = requests.get('http://test.com')
            self.assertTrue(ProcessRedirect.is_applicable(r, None, None, None))

    def test_process(self):
        with requests_mock.mock() as m:
            m.register_uri('GET', 'http://test.com', text=self.html, headers={'Location': 'http://foo/'},
                           status_code=300)
            r = requests.get('http://test.com')
        with patch.object(Crawler, 'add_url') as mock_method:
            p = ProcessRedirect(r, self.get_crawler_url())
            p.process('')
            urls = [crawler_url[0][0].url.url for crawler_url in mock_method.call_args_list]
            self.assertEqual(urls, ['http://foo/'])

    def test_str(self):
        with requests_mock.mock() as m:
            m.register_uri('GET', 'http://test.com', text=self.html, headers={'Location': 'http://foo/'},
                           status_code=300)
            r = requests.get('http://test.com')
        with patch.object(Crawler, 'add_url'):
            p = ProcessRedirect(r, self.get_crawler_url())
            p.process('')
        self.assertIn('http://foo/', str(p))


class TestProcessNotFound(CrawlerTestBase, unittest.TestCase):
    html = ''

    def test_is_applicable(self):
        with requests_mock.mock() as m:
            m.register_uri('GET', 'http://test.com', text=self.html, headers={'Content-Type': 'text/html'},
                           status_code=404)
            r = requests.get('http://test.com')
            self.assertTrue(ProcessNotFound.is_applicable(r, None, None, None))

    def test_fake(self):
        crawler_url = self.get_crawler_url()
        crawler_url.exists = True
        process = ProcessNotFound(None, crawler_url)
        self.assertIn('{}.fake'.format(process.key_name), process.flags)

    def test_str(self):
        crawler_url = self.get_crawler_url()
        crawler_url.exists = True
        process = ProcessNotFound(None, crawler_url)
        str(process)


class TestProcessHtmlRequest(CrawlerTestBase, unittest.TestCase):

    def test_process(self):
        html = """
        <a href="dir/">dir</a>
        <script src="myscripts.js"></script>        
        """
        with patch.object(Crawler, 'add_url') as mock_method:
            process = ProcessHtmlRequest(None, self.get_crawler_url())
            soup = BeautifulSoup(html, 'html.parser')
            process.process(html, soup)
            urls = [crawler_url[0][0].url.url for crawler_url in mock_method.call_args_list]
            self.assertEqual(set(urls), {
                'http://domain.com/path/myscripts.js',
                'http://domain.com/path/dir/',
                'http://domain.com/path/index.php',
            })

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

    def test_wordpress(self):
        html = """
        <script src="wp-content/myscripts.js"></script>
        """
        with patch.object(Crawler, 'add_url'):
            process = ProcessHtmlRequest(None, self.get_crawler_url())
            soup = BeautifulSoup(html, 'html.parser')
            process.assets(soup)
            self.assertIn('wordpress', process.crawler_url.flags)


class TestProcessIndexOfRequest(CrawlerTestBase, unittest.TestCase):
    html = """
    <html><head><title>Index Of</title></head><body>
    <a href="..">Top</a>
    <a href="dir/">dir</a>
    <a href="foo.php">foo.php</a>
    <a href="error_log">error_log</a>
    <a href="/spam/eggs">Eggs</a></body></html>
    """
    html_apache = """
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <html>
     <head>
      <title>Index of /wp-includes</title>
     </head>
     <body>
    <h1>Index of /wp-includes</h1>
    <pre><img src="/__apache/blank.gif" alt="Icon "> <a href="?C=N;O=D">Name</a>
    <a href="?C=M;O=A">Last modified</a>      <a href="?C=S;O=A">Size</a>  
    <a href="?C=D;O=A">Description</a><hr>
    <img src="/__ovh_icons/back.gif" alt="[PARENTDIR]"> <a href="/">Parent Directory</a>                             -   
    <img src="/__apache/folder.gif" alt="[DIR]"> <a href="ID3/">ID3/</a>                    2015-09-15 14:58    -   
    <img src="/__apache/folder.gif" alt="[DIR]"> <a href="IXR/">IXR/</a>                    2018-02-16 14:29    -   
    <img src="/__apache/unknown.gif" alt="[   ]"> <a href="author-template.php">author-template.php</a>     
    2018-02-16 14:29   16K  
    <img src="/__apache/unknown.gif" alt="[   ]"> <a href="bookmark-template.php">bookmark-template.php</a>   
    2018-02-16 14:29   11K  
    </pre>
    </body></html>    
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

    def test_str(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(self.html, BeautifulSoup(self.html, 'html.parser'))
        str(process)

    def test_process_apache(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        soup = BeautifulSoup(self.html_apache, 'html.parser')
        process.process(self.html_apache, soup)
        urls = [file.url for file in process.files if '?' not in file.full_path]
        self.assertEqual(urls, [
            'http://domain.com/',
            'http://domain.com/path/ID3/',
            'http://domain.com/path/IXR/',
            'http://domain.com/path/author-template.php',
            'http://domain.com/path/bookmark-template.php',
        ])


class TestProcessBlankPageRequest(CrawlerTestBase, unittest.TestCase):
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
