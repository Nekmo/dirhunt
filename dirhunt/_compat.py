# -*- coding: utf-8 -*-
import sys


if sys.version_info >= (3,):
    from urllib.parse import urlparse, urljoin
else:
    from urlparse import urlparse, urljoin


if sys.version_info >= (3,):
    from queue import Queue
    import queue
else:
    from Queue import Queue
    import Queue as queue


if sys.version_info >= (3,):
    from shutil import get_terminal_size
else:
    from backports.shutil_get_terminal_size import get_terminal_size


try:
    from mock import patch, Mock
except ImportError:
    from unittest.mock import patch, Mock
