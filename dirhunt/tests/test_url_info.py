import unittest

import os
from subprocess import PIPE, STDOUT
from sys import stdout

import requests_mock

from dirhunt.sessions import Sessions
from dirhunt.url import Url
from dirhunt.url_info import UrlInfo, sizeof_fmt, DEFAULT_UNKNOWN_SIZE, UrlsInfo
from dirhunt.tests._compat import patch, Mock


class TestSizeofFmt(unittest.TestCase):
    def test_none(self):
        self.assertEqual(sizeof_fmt(None), DEFAULT_UNKNOWN_SIZE)

    def test_str(self):
        self.assertEqual(sizeof_fmt('123'), '123B')

    def test_num(self):
        self.assertEqual(sizeof_fmt(1024 ** 2), '1MiB')

    def test_yib(self):
        self.assertEqual(sizeof_fmt(1024 ** 8), '1YiB')


class TestUrlInfo(unittest.TestCase):
    url = 'https://domain.com/foo.php'

    def _get_url_info(self):
        return UrlInfo(Sessions(), Url(self.url))

    def _test_get_data(self, html, url_info=None):
        url_info = url_info or self._get_url_info()
        with requests_mock.mock() as m:
            m.get(self.url, text=html)
            return url_info.data

    def test_get_data_title(self):
        html = '<html><title>Foo</title></html>'
        self.assertEqual(self._test_get_data(html).get('title'), 'Foo')

    def test_get_data_body(self):
        body = '<body><h1>Hello world</h1></body>'
        html = '<html>{}</html>'.format(body)
        self.assertEqual(self._test_get_data(html).get('body'), body)

    def test_get_data_invalid_html(self):
        html = 'htm>/<><//tml'
        data = self._test_get_data(html)
        self.assertEqual(data.get('text'), html)
        for key in ['title', 'body']:
            self.assertIsNone(data.get(key))

    def test_use_multi_line(self):
        html = '<html><title>Foo</title></html>'
        url_info = self._get_url_info()
        self._test_get_data(html, url_info)
        with patch.object(UrlInfo, 'multi_line') as mock_one_line:
            url_info.line(30, len(self.url))
            mock_one_line.assert_called_once()

    def test_use_one_line(self):
        html = '<html><title>Foo</title></html>'
        url_info = self._get_url_info()
        self._test_get_data(html, url_info)
        with patch.object(UrlInfo, 'one_line') as mock_one_line:
            url_info.line(300, len(self.url))
            mock_one_line.assert_called_once()

    def test_one_line(self):
        html = '<html><title>Foo</title></html>'
        url_info = self._get_url_info()
        self._test_get_data(html, url_info)
        self.assertIn(self.url, url_info.one_line(200, len(self.url)))

    def test_multi_line(self):
        html = '<html><title>Foo</title></html>'
        url_info = self._get_url_info()
        self._test_get_data(html, url_info)
        self.assertIn(self.url, url_info.multi_line(30))


class TestUrlsInfo(unittest.TestCase):
    url = 'https://domain.com/foo.php'

    def test_callback(self):
        with patch.object(UrlsInfo, '_get_url_info') as m:
            UrlsInfo([self.url], Sessions()).callback(len(self.url), Url(self.url))
            m.assert_called_once()

    def test_start_empty(self):
        with patch.object(UrlsInfo, 'submit') as m:
            UrlsInfo([], Sessions()).start()
            m.assert_not_called()

    def test_erase(self):
        mstdout = Mock(**{'isatty.return_value': True})
        UrlsInfo([], Sessions(), std=mstdout).erase()
        mstdout.write.assert_called_once()

    def test_echo(self):
        mstdout = Mock(**{'isatty.return_value': True})
        UrlsInfo([], Sessions(), std=mstdout).echo('Foo')
        mstdout.write.assert_called()
