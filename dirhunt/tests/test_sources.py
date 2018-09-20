import sys
import unittest

import requests_mock

from dirhunt._compat import URLError
from dirhunt.sources import Robots, VirusTotal, Google
from dirhunt.sources.google import STOP_AFTER
from dirhunt.sources.robots import DirhuntRobotFileParser
from dirhunt.sources.virustotal import VT_URL, ABUSE
from dirhunt.tests._compat import patch, call

ROBOTS = """
User-agent: *
Disallow: /secret/
"""
ABUSE_DIV = '<div class="enum"><a>{url}</a></div>'


class TestRobots(unittest.TestCase):

    def test_parse(self):
        def read(self):
            self.parse(ROBOTS.splitlines())

        with patch.object(Robots, 'add_result') as mock_add_result:
            with patch.object(DirhuntRobotFileParser, 'read', side_effect=read, autospec=True):
                Robots(lambda x: x, None).callback('domain.com')
                mock_add_result.assert_called_once_with('http://domain.com/secret/')

    def test_https(self):
        def read(self):
            if self.url.startswith('http:'):
                raise IOError
            self.parse(ROBOTS.splitlines())

        with patch.object(Robots, 'add_result') as mock_add_result:
            with patch.object(DirhuntRobotFileParser, 'read', side_effect=read, autospec=True):
                Robots(lambda x: x, None).callback('domain.com')
                mock_add_result.assert_called_once_with('https://domain.com/secret/')

    @requests_mock.Mocker()
    def test_401(self, m):
        url = 'http://domain.com/robots.txt'
        m.get(url, status_code=401)
        rp = DirhuntRobotFileParser(url)
        rp.read()
        self.assertTrue(rp.disallow_all)

    @requests_mock.Mocker()
    def test_404(self, m):
        url = 'http://domain.com/robots.txt'
        m.get(url, status_code=404)
        rp = DirhuntRobotFileParser(url)
        rp.read()
        self.assertTrue(rp.allow_all)


class TestVirusTotal(unittest.TestCase):

    @requests_mock.Mocker()
    def test_urls(self, m):
        domain = 'domain.com'
        url = VT_URL.format(domain=domain)
        detect_urls = ['http://{}/{}'.format(domain, i) for i in range(10)]
        m.get(url, text='<html><body><div id="detected-urls">{}</div></body></html>'.format(
            '\n'.join([ABUSE_DIV.format(url=detect_url) for detect_url in detect_urls])
        ))
        with patch.object(VirusTotal, 'add_result') as mock_add_result:
            VirusTotal(lambda x: x, None).callback(domain)
            mock_add_result.assert_has_calls([call(detect_url) for detect_url in detect_urls])

    @requests_mock.Mocker()
    def test_abuse(self, m):
        domain = 'domain.com'
        url = VT_URL.format(domain=domain)
        m.get(url, text=ABUSE)
        with patch.object(VirusTotal, 'add_error') as mock_add_error:
            VirusTotal(lambda x: x, lambda x: x).callback(domain)
            mock_add_error.assert_called()


class TestGoogle(unittest.TestCase):

    @patch.object(Google, 'add_result')
    def test_search(self, m1):
        domain = 'domain'
        urls = ['http://domain/path1', 'http://domain/path2']

        with patch('dirhunt.sources.google.search', side_effect=lambda x, stop: iter(urls)) as m2:
            Google(lambda x: x, None).callback(domain)
            m2.assert_called_once_with('site:{}'.format(domain), stop=STOP_AFTER)
        m1.assert_has_calls([call(url) for url in urls])

    @patch.object(Google, 'add_error')
    def test_failure(self, m1):
        if sys.version_info < (3,):
            self.skipTest('Unsupported Mock usage in Python 2.7')

        def search_iter(*args):
            raise URLError('Test')

        with patch('dirhunt.sources.google.search', return_value=map(search_iter, [0])):
            Google(lambda x: x, lambda x: x).callback('domain')
        m1.assert_called_once()
