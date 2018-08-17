

try:
    from mock import patch, Mock, call
except ImportError:
    from unittest.mock import patch, Mock, call
