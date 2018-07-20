import unittest

from dirhunt.url_loop import is_url_loop


class TestUrlLoop(unittest.TestCase):

    def test_dir_loop(self):
        self.assertTrue(is_url_loop('http://localhost/a/a/a/a/a/'))

    def test_start_url(self):
        self.assertTrue(is_url_loop('http://localhost/sub/a/a/a/a/a/'))

    def test_group_loop(self):
        self.assertTrue(is_url_loop('http://localhost' + ('/a/b/c' * 5)))

    def test_group_insufficient_loop(self):
        self.assertFalse(is_url_loop('http://localhost' + ('/a/b/c' * 2)))

    def test_insufficient_loop(self):
        self.assertFalse(is_url_loop('http://localhost' + ('/a' * 2)))

    def test_invalid_end(self):
        self.assertFalse(is_url_loop('http://localhost' + ('/a' * 5) + '/b/c'))

    def test_ignore_end(self):
        self.assertTrue(is_url_loop('http://localhost' + ('/a/b/c' * 5) + '/d'))
