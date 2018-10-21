import sys
import unittest

from requests.exceptions import ProxyError

from dirhunt.sessions import Sessions, normalize_proxy, RandomProxies, MAX_NEGATIVE_VOTES
from dirhunt.tests._compat import patch, Mock, MagicMock


class TestNormalizeProxy(unittest.TestCase):
    def test_proxy_none(self):
        self.assertEqual(normalize_proxy('None', None), None)

    def test_proxy_tor(self):
        self.assertEqual(normalize_proxy('tor', None), 'socks5://127.0.0.1:9150')

    def test_proxy_db(self):
        if sys.version_info < (3,):
            self.skipTest('Unsupported Mock in Python 2.7')
        mock = Mock()
        mock.proxies_lists.__getitem__ = Mock()
        mock.proxies_lists.__getitem__.return_value.__next__ = Mock()
        normalize_proxy('Random', mock)
        mock.proxies_lists.__getitem__.assert_called_once()
        mock.proxies_lists.__getitem__.return_value.__next__.assert_called_once()


class TestRandomProxies(unittest.TestCase):
    @patch('dirhunt.sessions.ProxiesList')
    def test_getitem(self, m):
        proxies_list = RandomProxies()['Random']
        self.assertIsInstance(proxies_list, MagicMock)
        m.assert_called_once_with(None)


class TestSession(unittest.TestCase):
    url = 'http://myurl'

    def test_proxy(self):
        proxy = 'http://10.1.2.3:3128'
        sessions = Sessions([proxy])
        session = sessions.sessions[0]
        m = Mock()
        session.session = m
        session.get(self.url)
        m.get.assert_called_once_with(self.url, proxies={'http': proxy, 'https': proxy})

    @patch('dirhunt.sessions.isinstance', return_value=True)
    def test_random_proxy_positive(self, m):
        proxy_instance = Mock()
        with patch('dirhunt.sessions.normalize_proxy', return_value=proxy_instance):
            sessions = Sessions()
            session = sessions.sessions[0]
            self.assertIs(session.proxy, proxy_instance)
            session_mock = Mock()
            session.session = session_mock
            session.get(self.url)
            proxy_instance.positive.assert_called_once()

    def _test_random_proxy_negative(self, votes):
        proxy_instance = Mock()
        proxy_instance.get_updated_proxy.return_value.votes = votes
        with patch('dirhunt.sessions.normalize_proxy', return_value=proxy_instance):
            sessions = Sessions()
            session = sessions.sessions[0]
            self.assertIs(session.proxy, proxy_instance)
            session_mock = Mock(**{'get.side_effect': ProxyError})
            session.session = session_mock
            with self.assertRaises(ProxyError):
                session.get(self.url)
        return proxy_instance

    @patch('dirhunt.sessions.isinstance', return_value=True)
    def test_random_proxy_negative(self, m):
        proxy_instance = self._test_random_proxy_negative(0)
        proxy_instance.negative.assert_called_once()

    @patch('dirhunt.sessions.isinstance', return_value=True)
    def test_random_proxy_negative_and_change(self, m):
        proxy_instance = self._test_random_proxy_negative(MAX_NEGATIVE_VOTES - 1)
        self.assertEqual(proxy_instance.negative.call_count, 4)


class TestSessions(unittest.TestCase):
    def test_delay_add_available(self):
        sessions = Sessions(delay=1)
        session = sessions.sessions[0]
        with patch('dirhunt.sessions.threading.Timer') as m:
            sessions.add_available(session)
        m.assert_called_once_with(sessions.delay, sessions.availables.put, [session])
        m.return_value.start.assert_called_once()

    def test_random_session(self):
        sessions = Sessions()
        sessions.availables.get()
        with patch('dirhunt.sessions.random.choice') as m:
            sessions.get_session()
        m.assert_called_once()
