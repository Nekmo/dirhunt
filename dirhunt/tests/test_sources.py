import unittest

from dirhunt.sources import Robots
from dirhunt.sources.robots import DirhuntRobotFileParser
from dirhunt.tests._compat import patch

ROBOTS = """
User-agent: *
Disallow: /secret/
"""


class TestRobots(unittest.TestCase):

    def test_parse(self):
        def read(self):
            self.parse(ROBOTS.splitlines())

        with patch.object(Robots, 'add_result') as mock_add_result:
            with patch.object(DirhuntRobotFileParser, 'read', side_effect=read, autospec=True):
                Robots(lambda x: x).callback('domain.com')
                mock_add_result.assert_called_once_with('http://domain.com/secret/')

    def test_https(self):
        def read(self):
            if self.url.startswith('http:'):
                raise IOError
            self.parse(ROBOTS.splitlines())

        with patch.object(Robots, 'add_result') as mock_add_result:
            with patch.object(DirhuntRobotFileParser, 'read', side_effect=read, autospec=True):
                Robots(lambda x: x).callback('domain.com')
                mock_add_result.assert_called_once_with('https://domain.com/secret/')
