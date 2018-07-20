import unittest

from colorama import Fore

from dirhunt.colors import status_code_colors


class TestColors(unittest.TestCase):
    def test_100(self):
        self.assertEqual(status_code_colors(120), Fore.WHITE)

    def test_200(self):
        self.assertEqual(status_code_colors(200), Fore.LIGHTGREEN_EX)

    def test_201(self):
        self.assertEqual(status_code_colors(201), Fore.GREEN)

    def test_300(self):
        self.assertEqual(status_code_colors(300), Fore.LIGHTBLUE_EX)

    def test_500(self):
        self.assertEqual(status_code_colors(500), Fore.LIGHTMAGENTA_EX)

    def test_404(self):
        self.assertEqual(status_code_colors(404), Fore.MAGENTA)
