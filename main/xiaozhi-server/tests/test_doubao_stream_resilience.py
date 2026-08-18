import unittest

from core.providers.asr.doubao_stream import ASRProvider


class _RejectedResponse:
    status_code = 403


class _RejectedConnection(Exception):
    response = _RejectedResponse()


class DoubaoStreamResilienceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.provider = ASRProvider(
            {
                "appid": "test-placeholder",
                "access_token": "test-placeholder",
            },
            True,
        )

    async def test_connection_failures_back_off_instead_of_retrying_per_frame(self):
        first_delay, first_error = self.provider._record_connection_failure(
            _RejectedConnection("response may contain sensitive diagnostics")
        )
        second_delay, second_error = self.provider._record_connection_failure(
            _RejectedConnection("response may contain sensitive diagnostics")
        )

        self.assertEqual(first_delay, 1.0)
        self.assertEqual(second_delay, 2.0)
        self.assertTrue(self.provider._connection_retry_pending())
        self.assertEqual(first_error, "HTTP 403")
        self.assertEqual(second_error, "HTTP 403")
        self.assertNotIn("sensitive", first_error)

    async def test_success_or_new_channel_resets_backoff(self):
        self.provider._record_connection_failure(RuntimeError("provider failed"))
        self.provider._reset_connection_backoff()

        self.assertFalse(self.provider._connection_retry_pending())
        self.assertEqual(self.provider._connection_failures, 0)

    def test_new_console_api_key_auth_takes_precedence(self):
        provider = ASRProvider(
            {
                "api_key": "new-console-key",
                "appid": "legacy-app",
                "access_token": "legacy-token",
                "resource_id": "volc.seedasr.sauc.duration",
            },
            True,
        )

        headers = provider.token_auth()

        self.assertEqual(headers["X-Api-Key"], "new-console-key")
        self.assertEqual(headers["X-Api-Resource-Id"], "volc.seedasr.sauc.duration")
        self.assertNotIn("X-Api-App-Key", headers)
        self.assertNotIn("X-Api-Access-Key", headers)

    def test_legacy_auth_remains_available_without_api_key(self):
        headers = self.provider.token_auth()

        self.assertEqual(headers["X-Api-App-Key"], "test-placeholder")
        self.assertEqual(headers["X-Api-Access-Key"], "test-placeholder")
        self.assertNotIn("X-Api-Key", headers)


if __name__ == "__main__":
    unittest.main()
