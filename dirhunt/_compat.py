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


try:
    from mock import patch, Mock
except ImportError:
    from unittest.mock import patch, Mock


