import unittest

from bs4 import BeautifulSoup

from dirhunt.directory_lists import ApacheDirectoryList, CommonDirectoryList
from dirhunt.processors import ProcessIndexOfRequest
from dirhunt.tests.base import CrawlerTestBase


class DirectoryListsTestBase(CrawlerTestBase):
    html = ''

    def get_beautiful_soup(self, html=None):
        html = html or self.html
        return BeautifulSoup(html, 'html.parser')

    def get_processor(self):
        return ProcessIndexOfRequest(None, self.get_crawler_url())


class TestApacheDirectoryLists(DirectoryListsTestBase, unittest.TestCase):
    html = """
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
        beautiful_soup = self.get_beautiful_soup()
        self.assertTrue(ApacheDirectoryList.is_applicable(self.html, self.get_crawler_url(), beautiful_soup))

    def test_is_not_applicable(self):
        beautiful_soup = self.get_beautiful_soup(TestCommonDirectoryList.html)
        self.assertFalse(ApacheDirectoryList.is_applicable(TestCommonDirectoryList.html,
                                                           self.get_crawler_url(), beautiful_soup))

    def test_get_links(self):
        directory_list = ApacheDirectoryList(self.get_processor())
        links = directory_list.get_links(self.html, self.get_beautiful_soup())
        test_data = [(link.url, link.extra) for link in links]
        self.assertEqual(test_data, [
            ('http://domain.com/', {}),
            ('http://domain.com/path/ID3/', {'created_at': '2015-09-15 14:58'}),
            ('http://domain.com/path/IXR/', {'created_at': '2018-02-16 14:29'}),
            ('http://domain.com/path/author-template.php', {'created_at': '2018-02-16 14:29', 'filesize': '16K'}),
            ('http://domain.com/path/bookmark-template.php', {'created_at': '2018-02-16 14:29', 'filesize': '11K'}),
        ])


class TestCommonDirectoryList(DirectoryListsTestBase, unittest.TestCase):
    html = """
    <html><head><title>Index Of</title></head><body>
    <a href="..">Top</a>
    <a href="dir/">dir</a>
    <a href="foo.php">foo.php</a>
    <a href="error_log">error_log</a>
    <a href="/spam/eggs">Eggs</a></body></html>
    """
    urls = [
        'http://domain.com/',
        'http://domain.com/path/dir/',
        'http://domain.com/path/foo.php',
        'http://domain.com/path/error_log',
        'http://domain.com/spam/eggs',
    ]

    def test_process(self):
        directory_list = CommonDirectoryList(self.get_processor())
        links = directory_list.get_links(self.html, self.get_beautiful_soup())
        urls = [link.url for link in links]
        self.assertEqual(urls, self.urls)

    def test_is_applicable(self):
        beautiful_soup = self.get_beautiful_soup()
        self.assertTrue(CommonDirectoryList.is_applicable(self.html, self.get_crawler_url(), beautiful_soup))
