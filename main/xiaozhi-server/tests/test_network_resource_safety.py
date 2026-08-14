import unittest
from unittest.mock import patch

from core.utils.util import get_local_ip


class NetworkResourceSafetyTest(unittest.TestCase):
    def test_local_ip_socket_is_closed_when_route_probe_fails(self):
        with patch("core.utils.util.socket.socket") as socket_factory:
            local_socket = socket_factory.return_value.__enter__.return_value
            local_socket.connect.side_effect = OSError("route unavailable")

            self.assertEqual("127.0.0.1", get_local_ip())
            socket_factory.return_value.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
