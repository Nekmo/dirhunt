import unittest
import requests_mock

from dirhunt.sources import Robots, VirusTotal
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
