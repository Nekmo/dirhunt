

try:
    from mock import patch, Mock, MagicMock, call
except ImportError:
    from unittest.mock import patch, Mock, MagicMock, call


try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
