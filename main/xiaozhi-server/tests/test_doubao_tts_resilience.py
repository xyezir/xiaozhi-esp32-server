import asyncio
import tempfile
import unittest
from unittest.mock import Mock, patch

from core.providers.tts.base import TTSProviderError
from core.providers.tts.doubao import TTSProvider


class DoubaoTTSResilienceTest(unittest.TestCase):
    def setUp(self):
        self.output_dir = tempfile.TemporaryDirectory()
        self.provider = TTSProvider(
            {
                "appid": "1",
                "access_token": "secret-access-token",
                "cluster": "volcano_tts",
                "voice": "test-voice",
                "format": "wav",
                "api_url": "https://example.invalid/tts",
                "authorization": "Bearer;",
                "output_dir": self.output_dir.name,
                "tts_timeout": 7,
            },
            True,
        )

    def tearDown(self):
        self.output_dir.cleanup()

    def test_http_403_is_status_only_and_not_retryable(self):
        response = Mock(status_code=403, content=b"secret-provider-response")
        response.json.return_value = {"message": "secret-provider-response"}

        with patch(
            "core.providers.tts.doubao.requests.post", return_value=response
        ) as post:
            with self.assertRaises(TTSProviderError) as raised:
                asyncio.run(self.provider.text_to_speak("private reply", None))

        self.assertEqual(raised.exception.status_code, 403)
        self.assertFalse(raised.exception.retryable)
        self.assertNotIn("private reply", str(raised.exception))
        self.assertNotIn("secret", str(raised.exception))
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["timeout"], 7)

    def test_non_retryable_failure_stops_after_one_attempt_and_redacts_logs(self):
        response = Mock(status_code=403, content=b"secret-provider-response")
        response.json.return_value = {"message": "secret-provider-response"}
        bound_logger = Mock()

        with patch(
            "core.providers.tts.doubao.requests.post", return_value=response
        ) as post, patch("core.providers.tts.base.logger") as logger:
            logger.bind.return_value = bound_logger
            self.provider.to_tts_stream("private reply")

        post.assert_called_once()
        messages = " ".join(
            str(call.args[0])
            for method in (bound_logger.warning, bound_logger.error)
            for call in method.call_args_list
        )
        self.assertIn("status=403", messages)
        self.assertIn("retryable=false", messages)
        self.assertNotIn("private reply", messages)
        self.assertNotIn("secret", messages)

    def test_transient_server_failure_remains_bounded(self):
        response = Mock(status_code=503, content=b"temporary")
        response.json.return_value = {"message": "temporary"}

        with patch(
            "core.providers.tts.doubao.requests.post", return_value=response
        ) as post, patch("core.providers.tts.base.logger"):
            self.provider.to_tts_stream("private reply")

        self.assertEqual(post.call_count, 5)

    def test_timeout_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "tts_timeout"):
            TTSProvider(
                {
                    "access_token": "test",
                    "output_dir": self.output_dir.name,
                    "tts_timeout": 0,
                },
                True,
            )


if __name__ == "__main__":
    unittest.main()
