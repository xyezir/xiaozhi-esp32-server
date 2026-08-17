import os
import sys
import tempfile
import unittest


SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVER_ROOT not in sys.path:
    sys.path.insert(0, SERVER_ROOT)

from core.providers.tools.server_mcp.mcp_client import ServerMCPClient


class ServerMCPSecretHeadersTest(unittest.TestCase):
    def _token_file(self, value):
        handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False)
        self.addCleanup(lambda: os.unlink(handle.name))
        with handle:
            handle.write(value)
        return handle.name

    def test_reads_bearer_token_from_file(self):
        path = self._token_file("test-secret\n")
        client = ServerMCPClient(
            {
                "url": "https://example.invalid/mcp",
                "headers": {"X-Client": "xiaozhi"},
                "authorization_token_file": path,
            }
        )

        headers = client._build_http_headers()

        self.assertEqual("Bearer test-secret", headers["Authorization"])
        self.assertEqual("xiaozhi", headers["X-Client"])

    def test_rejects_ambiguous_authorization_sources(self):
        path = self._token_file("test-secret")
        client = ServerMCPClient(
            {
                "url": "https://example.invalid/mcp",
                "headers": {"authorization": "Bearer inline-secret"},
                "authorization_token_file": path,
            }
        )

        with self.assertRaisesRegex(ValueError, "cannot be combined"):
            client._build_http_headers()

    def test_rejects_empty_or_multiline_tokens(self):
        for value in ("", "first\nsecond"):
            with self.subTest(value=value):
                path = self._token_file(value)
                client = ServerMCPClient(
                    {
                        "url": "https://example.invalid/mcp",
                        "authorization_token_file": path,
                    }
                )
                with self.assertRaisesRegex(ValueError, "one non-empty line"):
                    client._build_http_headers()


if __name__ == "__main__":
    unittest.main()
