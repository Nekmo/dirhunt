

try:
    from mock import patch, Mock, MagicMock, call
except ImportError:
    from unittest.mock import patch, Mock, MagicMock, call
