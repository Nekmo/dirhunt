import unittest

import sys

from dirhunt.exceptions import DirHuntError, catch, reraise_with_stack
from dirhunt.tests._compat import Mock, patch

class TestDirHuntError(unittest.TestCase):
    def test_extra_body(self):
        self.assertIn('Foo', str(DirHuntError('Foo')))

    def test_body(self):
        e = DirHuntError()
        e.body = 'Foo'
        self.assertIn('Foo', str(e))

    def test_extra_and_body(self):
        e = DirHuntError('Foo')
        e.body = 'Bar'
        self.assertIn('Foo', str(e))
        self.assertIn('Bar', str(e))


class TestCatch(unittest.TestCase):
    def test_ok(self):
        m = Mock()
        catch(m)()
        m.assert_called_once()

    def test_error(self):
        if sys.version_info < (3,):
            self.skipTest('Unsupported Mock in Python 2.7')
        m = Mock(side_effect=DirHuntError)
        with patch('sys.stderr.write') as mock_write:
            catch(m)()
            m.assert_called_once()
            mock_write.assert_called_once()


class TestReraiseWithStack(unittest.TestCase):
    def test_ok(self):
        if sys.version_info < (3,):
            self.skipTest('Unsupported Mock in Python 2.7')
        m = Mock()
        reraise_with_stack(m)()
        m.assert_called_once()

    def test_error(self):
        if sys.version_info < (3,):
            self.skipTest('Unsupported Mock in Python 2.7')
        m = Mock(side_effect=KeyError)
        with patch('traceback.print_exc') as mock_print_exc:
            with self.assertRaises(KeyError):
                reraise_with_stack(m)()
            m.assert_called_once()
            mock_print_exc.assert_called_once()
