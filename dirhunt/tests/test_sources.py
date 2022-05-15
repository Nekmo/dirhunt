import ssl
import sys
import unittest

import requests_mock

from dirhunt._compat import URLError
from dirhunt.sources import Robots, VirusTotal, Google, CommonCrawl, CertificateSSL, CrtSh, Wayback
from dirhunt.sources.commoncrawl import COMMONCRAWL_URL
from dirhunt.sources.crtsh import CRTSH_URL
from dirhunt.sources.google import STOP_AFTER
from dirhunt.sources.robots import DirhuntRobotFileParser
from dirhunt.sources.virustotal import VT_URL, ABUSE
from dirhunt.sources.wayback import WAYBACK_URL, WAYBACK_PARAMS
from dirhunt.tests._compat import patch, call, urlencode

ROBOTS = """
User-agent: *
Disallow: /secret/
"""
ABUSE_DIV = '<div class="enum"><a>{url}</a></div>'
COMMONCRAWL_INDEXES = [
  {
    "id": "CC-MAIN-2021-49",
    "name": "November 2021 Index",
    "timegate": "https://index.commoncrawl.org/CC-MAIN-2021-49/",
    "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2021-49-index"
  },
]
COMMONCRAWL_RESULT = {'url': 'https://foo.com/bar/'}


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


class TestCommonCrawl(unittest.TestCase):
    @requests_mock.Mocker()
    def test_get_latest_craw_index(self, m):
        m.get(COMMONCRAWL_URL, json=COMMONCRAWL_INDEXES)
        common_crawl = CommonCrawl(lambda x: x, None)
        self.assertEqual(common_crawl.get_latest_craw_index(), COMMONCRAWL_INDEXES[0]['cdx-api'])

    @requests_mock.Mocker()
    def test_get_latest_craw_index_error(self, m):
        m.get(COMMONCRAWL_URL, status_code=403)
        common_crawl = CommonCrawl(lambda x: x, None)
        self.assertEqual(common_crawl.get_latest_craw_index(), None)

    @requests_mock.Mocker()
    def test_get_latest_craw_index_empty(self, m):
        m.get(COMMONCRAWL_URL, json=[])
        common_crawl = CommonCrawl(lambda x: x, None)
        self.assertEqual(common_crawl.get_latest_craw_index(), None)

    @requests_mock.Mocker()
    @patch.object(CommonCrawl, 'add_result')
    def test_get_latest_craw_index_empty(self, m1, m2):
        m1.get(COMMONCRAWL_URL, json=COMMONCRAWL_INDEXES)
        url = '{}?{}'.format(
            COMMONCRAWL_INDEXES[0]['cdx-api'],
            urlencode({'url': '*.domain', 'output': 'json'})
        )
        m1.get(url, json=COMMONCRAWL_RESULT)
        common_crawl = CommonCrawl(lambda x: x, None)
        common_crawl.callback('domain')

        m2.assert_has_calls([call(COMMONCRAWL_RESULT['url'])])


class TestCrtSh(unittest.TestCase):
    @requests_mock.Mocker()
    @patch.object(CrtSh, 'add_result')
    def test_callback(self, m, add_result_mock):
        domain = 'domain.com'
        m.get('{}?q={}&output=json'.format(CRTSH_URL, domain), json=[
            {'common_name': 'sub.domain.com'}, {'common_name': 'sub.domain.com'}, {'common_name': 'sub2.domain.com'}
        ])
        crtsh = CrtSh(lambda x: x, None)
        crtsh.callback(domain)
        add_result_mock.assert_has_calls([
            call('https://sub.domain.com/'), call('https://sub2.domain.com/')
        ], any_order=True)



class TestCertificateSSL(unittest.TestCase):
    @patch('dirhunt.sources.ssl.ssl')
    def test_callback(self, m):
        domain = 'foo.com'
        subdomain = 'sub.foo.com'
        with patch.object(CertificateSSL, 'add_result') as mock_add_result:
            m.create_default_context.return_value.wrap_socket.return_value\
                .__enter__.return_value.getpeercert.return_value = {'subjectAltName': (('DNS', subdomain),)}
            certificate_ssl = CertificateSSL(lambda x: x, None)
            certificate_ssl.callback(domain)
            mock_add_result.assert_called_once_with('https://{}/'.format(subdomain))

    @patch('dirhunt.sources.ssl.ssl.create_default_context', **{
        'return_value.wrap_socket.side_effect': ssl.SSLError
    })
    def test_certificate_error(self, m):
        subdomain = 'sub.foo.com'
        with patch.object(CertificateSSL, 'add_result') as mock_add_result:
            m.create_default_context.return_value.wrap_socket.return_value\
                .__enter__.return_value.getpeercert.return_value = {'subjectAltName': (('DNS', subdomain),)}
            certificate_ssl = CertificateSSL(lambda x: x, None)
            certificate_ssl.callback('foo.com')
            mock_add_result.assert_not_called()


class TestWayback(unittest.TestCase):
    @requests_mock.Mocker()
    @patch.object(Wayback, 'add_result')
    def test_callback(self, m, add_result_mock):
        domain = 'domain.com'
        subdomains = ['sub.domain.com', 'sub2.domain.com']
        m.get('{}?{}'.format(WAYBACK_URL, urlencode(dict(WAYBACK_PARAMS, url="*.{}".format(domain)))),
              text='\n'.join(subdomains))
        wayback = Wayback(lambda x: x, None)
        wayback.callback(domain)
        add_result_mock.assert_has_calls([call(subdomain) for subdomain in subdomains], any_order=True)
