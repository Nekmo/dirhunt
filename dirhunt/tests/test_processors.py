import unittest
from dirhunt.tests._compat import patch

import requests
import requests_mock
from bs4 import BeautifulSoup

from dirhunt.crawler import Crawler
from dirhunt.processors import (
    ProcessHtmlRequest,
    ProcessIndexOfRequest,
    ProcessBlankPageRequest,
    ProcessNotFound,
    ProcessRedirect,
    Error,
    ProcessCssStyleSheet,
    ProcessJavaScript,
    ProcessBase,
)
from dirhunt.tests.base import CrawlerTestBase
from dirhunt.tests.test_directory_lists import TestCommonDirectoryList


class TestProcessBase(CrawlerTestBase, unittest.TestCase):
    html = "text html"

    def test_search_keywords(self):
        """Test search keywords in HTML"""
        with requests_mock.mock() as m:
            m.register_uri(
                "GET",
                "http://test.com",
                text=self.html,
                headers={"Content-Type": "text/html"},
                status_code=300,
            )
            r = requests.get("http://test.com")
            crawler_url = self.get_crawler_url()
            crawler_url.crawler.interesting_keywords = ["text"]
            process_base = ProcessBase(r, crawler_url)
            process_base.search_keywords(self.html)
            self.assertEqual({"text"}, process_base.keywords_found)


class TestError(CrawlerTestBase, unittest.TestCase):
    def test_str(self):
        e = Error(self.get_crawler_url(), Exception("Foo bar"))
        self.assertIn("Foo bar", str(e))


class TestProcessRedirect(CrawlerTestBase, unittest.TestCase):
    html = ""

    def test_is_applicable(self):
        with requests_mock.mock() as m:
            m.register_uri(
                "GET",
                "http://test.com",
                text=self.html,
                headers={"Content-Type": "text/html"},
                status_code=300,
            )
            r = requests.get("http://test.com")
            self.assertTrue(ProcessRedirect.is_applicable(r, None, None, None))

    def test_process(self):
        with requests_mock.mock() as m:
            m.register_uri(
                "GET",
                "http://test.com",
                text=self.html,
                headers={"Location": "http://foo/"},
                status_code=300,
            )
            r = requests.get("http://test.com")
        with patch.object(Crawler, "add_url") as mock_method:
            p = ProcessRedirect(r, self.get_crawler_url())
            p.process("")
            urls = [
                crawler_url[0][0].url.url for crawler_url in mock_method.call_args_list
            ]
            self.assertEqual(urls, ["http://foo/"])

    def test_str(self):
        with requests_mock.mock() as m:
            m.register_uri(
                "GET",
                "http://test.com",
                text=self.html,
                headers={"Location": "http://foo/"},
                status_code=300,
            )
            r = requests.get("http://test.com")
        with patch.object(Crawler, "add_url"):
            p = ProcessRedirect(r, self.get_crawler_url())
            p.process("")
        self.assertIn("http://foo/", str(p))


class TestProcessNotFound(CrawlerTestBase, unittest.TestCase):
    html = ""

    def test_is_applicable(self):
        with requests_mock.mock() as m:
            m.register_uri(
                "GET",
                "http://test.com",
                text=self.html,
                headers={"Content-Type": "text/html"},
                status_code=404,
            )
            r = requests.get("http://test.com")
            self.assertTrue(ProcessNotFound.is_applicable(r, None, None, None))

    def test_fake(self):
        crawler_url = self.get_crawler_url()
        crawler_url.exists = True
        process = ProcessNotFound(None, crawler_url)
        self.assertIn("{}.fake".format(process.key_name), process.flags)

    def test_str(self):
        crawler_url = self.get_crawler_url()
        crawler_url.exists = True
        process = ProcessNotFound(None, crawler_url)
        str(process)


class TestProcessCssStyleSheet(CrawlerTestBase, unittest.TestCase):
    css = 'body { background-image: url("img/foo.png") }'

    def test_is_applicable(self):
        crawler_url = self.get_crawler_url()
        with requests_mock.mock() as m:
            m.get(self.url, text=self.css, headers={"Content-Type": "text/css"})
            r = requests.get(self.url)
            self.assertTrue(
                ProcessCssStyleSheet.is_applicable(r, self.css, crawler_url, None)
            )

    def test_process(self):
        process = ProcessCssStyleSheet(None, self.get_crawler_url())
        urls = process.process(self.css, None)
        links = [link.url for link in urls]
        self.assertEqual(links, ["http://domain.com/path/img/foo.png"])


class TestProcessJavaScript(CrawlerTestBase, unittest.TestCase):
    js = """
    "http://example.com" "/wrong/file/test<>b" "api/create.php?user=test"
    "index.html"
    """

    def test_is_applicable(self):
        crawler_url = self.get_crawler_url()
        with requests_mock.mock() as m:
            m.get(
                self.url,
                text=self.js,
                headers={"Content-Type": "application/javascript"},
            )
            r = requests.get(self.url)
            self.assertTrue(
                ProcessJavaScript.is_applicable(r, self.js, crawler_url, None)
            )

    def test_process(self):
        process = ProcessJavaScript(None, self.get_crawler_url())
        urls = process.process(self.js, None)
        links = [link.url for link in urls]
        self.assertEqual(
            links,
            [
                "http://example.com/",
                "http://domain.com/path/api/create.php",
                "http://domain.com/path/index.html",
            ],
        )


class TestProcessHtmlRequest(CrawlerTestBase, unittest.TestCase):
    def test_process(self):
        html = """
        <a href="dir/">dir</a>
        <script src="myscripts.js"></script>
        """
        with patch.object(Crawler, "add_url") as mock_method:
            process = ProcessHtmlRequest(None, self.get_crawler_url())
            soup = BeautifulSoup(html, "html.parser")
            process.process(html, soup)
            urls = [
                crawler_url[0][0].url.url for crawler_url in mock_method.call_args_list
            ]
            self.assertEqual(
                set(urls),
                {
                    "http://domain.com/path/myscripts.js",
                    "http://domain.com/path/dir/",
                    "http://domain.com/path/index.php",
                },
            )

    def test_href_links(self):
        html = """
        <a href="..">Top</a>
        <a href="dir/">dir</a>
        <a href="foo.php">foo.php</a>
        <a href="/spam/eggs">Eggs</a>
        """
        with patch.object(Crawler, "add_url") as mock_method:
            process = ProcessHtmlRequest(None, self.get_crawler_url())
            soup = BeautifulSoup(html, "html.parser")
            process.links(soup)
            urls = [crawler_url[0][0].url for crawler_url in mock_method.call_args_list]
            self.assertEqual(
                urls,
                [
                    "http://domain.com/",
                    "http://domain.com/path/dir/",
                    "http://domain.com/path/foo.php",
                    "http://domain.com/spam/eggs",
                ],
            )

    def test_refresh_links(self):
        html = """
        <meta http-equiv="refresh" content="0;URL=/someotherdirectory">
        """
        with patch.object(Crawler, "add_url") as mock_method:
            process = ProcessHtmlRequest(None, self.get_crawler_url())
            soup = BeautifulSoup(html, "html.parser")
            process.links(soup)
            args, kwargs = mock_method.call_args_list[0]
            self.assertEqual(args[0].url, "http://domain.com/someotherdirectory")

    def test_assets(self):
        html = """
        <link rel="stylesheet" type="text/css" href="spam/theme.css">
        <script src="myscripts.js"></script>
        <script src="//cnd.extern.com/script.js"></script>
        <img src="/smiley.gif">
        <img src="proto:invalid:url"> <!-- Ignore -->
        """
        with patch.object(Crawler, "add_url") as mock_method:
            process = ProcessHtmlRequest(None, self.get_crawler_url())
            soup = BeautifulSoup(html, "html.parser")
            process.assets(soup)
            urls = [crawler_url[0][0].url for crawler_url in mock_method.call_args_list]
            self.assertEqual(
                urls,
                [
                    "http://domain.com/path/spam/theme.css",
                    "http://domain.com/path/myscripts.js",
                    "http://cnd.extern.com/script.js",
                    "http://domain.com/smiley.gif",
                ],
            )

    def test_wordpress(self):
        html = """
        <script src="wp-content/myscripts.js"></script>
        """
        with patch.object(Crawler, "add_url"):
            process = ProcessHtmlRequest(None, self.get_crawler_url())
            soup = BeautifulSoup(html, "html.parser")
            process.assets(soup)
            self.assertIn("wordpress", process.crawler_url.flags)


class TestProcessIndexOfRequest(CrawlerTestBase, unittest.TestCase):
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
            m.get(
                "http://test.com", text=self.html, headers={"Content-Type": "text/html"}
            )
            r = requests.get("http://test.com")
            soup = BeautifulSoup(self.html, "html.parser")
            self.assertTrue(
                ProcessIndexOfRequest.is_applicable(r, self.html, crawler_url, soup)
            )

    def test_process(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(
            TestCommonDirectoryList.html,
            BeautifulSoup(TestCommonDirectoryList.html, "html.parser"),
        )
        links = [link.url for link in process.files]
        self.assertEqual(links, TestCommonDirectoryList.urls)

    def test_interesting_ext_files(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(self.html, BeautifulSoup(self.html, "html.parser"))
        self.assertEqual(
            [file.url for file in process.interesting_ext_files()],
            ["http://domain.com/path/foo.php"],
        )

    def test_interesting_name_files(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(self.html, BeautifulSoup(self.html, "html.parser"))
        self.assertEqual(
            [file.url for file in process.interesting_name_files()],
            ["http://domain.com/path/error_log"],
        )

    def test_interesting_files(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(self.html, BeautifulSoup(self.html, "html.parser"))
        self.assertEqual(
            [file.url for file in process.interesting_files()],
            ["http://domain.com/path/foo.php", "http://domain.com/path/error_log"],
        )

    def test_flag_nothing(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process("", BeautifulSoup("", "html.parser"))
        self.assertEqual(process.flags, {"index_of", "index_of.nothing"})

    def test_str(self):
        process = ProcessIndexOfRequest(None, self.get_crawler_url())
        process.process(self.html, BeautifulSoup(self.html, "html.parser"))
        str(process)


class TestProcessBlankPageRequest(CrawlerTestBase, unittest.TestCase):
    def test_is_applicable(self):
        html = '<html><!-- Foo --><head><title>Foo</title><script src="foo.js"></script></head><body>  </body></html>'
        crawler_url = self.get_crawler_url()
        with requests_mock.mock() as m:
            m.get("http://test.com", text=html, headers={"Content-Type": "text/html"})
            r = requests.get("http://test.com")
            soup = BeautifulSoup(html, "html.parser")
            self.assertTrue(
                ProcessBlankPageRequest.is_applicable(r, html, crawler_url, soup)
            )

    def test_not_applicable(self):
        html = "<html><head><title>Foo</title></head><body>  Hello    </body></html>"
        crawler_url = self.get_crawler_url()
        with requests_mock.mock() as m:
            m.get("http://test.com", text=html, headers={"Content-Type": "text/html"})
            r = requests.get("http://test.com")
            soup = BeautifulSoup(html, "html.parser")
            self.assertFalse(
                ProcessBlankPageRequest.is_applicable(r, html, crawler_url, soup)
            )
