import unittest

from dirhunt.sessions import Sessions, Session, normalize_proxy
from dirhunt.tests._compat import patch, Mock


class TestNormalizeProxy(unittest.TestCase):
    def test_proxy_none(self):
        self.assertEqual(normalize_proxy('None'), None)

    def test_proxy_tor(self):
        self.assertEqual(normalize_proxy('tor'), 'socks5://127.0.0.1:9150')


class TestSession(unittest.TestCase):
    def test_proxy(self):
        proxy = 'http://10.1.2.3:3128'
        sessions = Sessions([proxy])
        session = sessions.sessions[0]
        url = 'http://myurl'
        m = Mock()
        session.session = m
        session.get(url)
        m.get.assert_called_once_with(url, proxies={'http': proxy, 'https': proxy})



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
