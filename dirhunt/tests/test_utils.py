import unittest

import requests_mock

from dirhunt.tests._compat import patch, Mock
from dirhunt.utils import force_url, SCHEMES, catch_keyboard_interrupt, flat_list, multiplier_args


class TestForceUrl(unittest.TestCase):
    def test_full_url(self):
        self.assertEqual(force_url('http://domain.com'), 'http://domain.com')

    def test_http(self):
        with requests_mock.mock() as m:
            m.get('http://domain.com', text='', headers={'Content-Type': 'text/html'})
            self.assertEqual(force_url('domain.com'), 'http://domain.com')
            self.assertEqual(m.call_count, 1)

    def test_https(self):
        with requests_mock.mock() as m:
            m.get('http://domain.com', headers={'Location': 'https://domain.com'},
                  status_code=301)
            m.get('https://domain.com', text='', headers={'Content-Type': 'text/html'})
            self.assertEqual(force_url('domain.com'), 'https://domain.com')

    def test_default(self):
        with requests_mock.mock() as m:
            for prot in SCHEMES + ['alt']:
                m.get('{}://domain.com'.format(prot), headers={'Location': 'alt://domain.com'},
                      status_code=301)
            self.assertEqual(force_url('domain.com'), 'http://domain.com')


class TestCatchKeyboardInterrupt(unittest.TestCase):
    def test_keyboard_interrupt(self):
        m = Mock(side_effect=KeyboardInterrupt)
        with patch('dirhunt.utils.confirm_close', side_effect=KeyboardInterrupt) as mock_confirm_close:
            with self.assertRaises(KeyboardInterrupt):
                catch_keyboard_interrupt(m)()
            mock_confirm_close.assert_called_once()


class TestFlatList(unittest.TestCase):
    def test_without_items(self):
        self.assertEqual(flat_list([]), [])

    def test_without_sublists(self):
        self.assertEqual(flat_list([1, 2, 3]), [1, 2, 3])

    def test_with_sublists(self):
        self.assertEqual(flat_list([1, [2, 3], 4]), [1, 2, 3, 4])


class TestMultiplierArgs(unittest.TestCase):
    def test_without_multiplier(self):
        self.assertEqual(multiplier_args(['foo', 'bar']), ['foo', 'bar'])

    def test_multiplier(self):
        self.assertEqual(multiplier_args(['foo', 'bar*3']), ['foo'] + (['bar'] * 3))

    def test_invalid_multiplier(self):
        self.assertEqual(multiplier_args(['foo', 'bar*spam']), ['foo', 'bar*spam'])
