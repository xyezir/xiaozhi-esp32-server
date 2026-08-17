import os
import tempfile
import unittest
from unittest.mock import patch

from core.providers.asr.base import ASRProviderBase
from core.providers.asr.doubao_flash import ASRProvider
from core.providers.asr.dto.dto import InterfaceType


class _Response:
    def __init__(self, text="识别成功", status_code="20000000"):
        self.headers = {"X-Api-Status-Code": status_code}
        self._text = text

    def raise_for_status(self):
        return None

    def json(self):
        return {"result": {"text": self._text}}


class DoubaoFlashASRTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.output_dir = tempfile.TemporaryDirectory()
        self.audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self.audio_file.write(b"test-audio")
        self.audio_file.close()
        self.provider = ASRProvider(
            {
                "api_key": "new-console-api-key",
                "output_dir": self.output_dir.name,
                "request_timeout": 1,
            },
            True,
        )
        self.artifacts = ASRProviderBase.AudioArtifacts(
            pcm_frames=[b"audio"],
            pcm_bytes=b"audio",
            file_path="saved.wav",
            temp_path=self.audio_file.name,
        )

    def tearDown(self):
        os.unlink(self.audio_file.name)
        self.output_dir.cleanup()

    async def asyncTearDown(self):
        await self.provider.close()

    def test_requires_api_key_and_fixed_resource(self):
        with self.assertRaisesRegex(ValueError, "api_key"):
            ASRProvider({"output_dir": self.output_dir.name}, True)
        with self.assertRaisesRegex(ValueError, "resource_id"):
            ASRProvider(
                {
                    "api_key": "key",
                    "resource_id": "untrusted-resource",
                    "output_dir": self.output_dir.name,
                },
                True,
            )

    def test_non_stream_file_contract(self):
        self.assertEqual(self.provider.interface_type, InterfaceType.NON_STREAM)
        self.assertTrue(self.provider.requires_file())
        self.assertTrue(self.provider.prefers_temp_file())

    async def test_success_uses_new_api_key_contract_and_fixed_endpoint(self):
        with patch(
            "core.providers.asr.doubao_flash.requests.Session.post",
            return_value=_Response(),
        ) as post:
            text, file_path = await self.provider.speech_to_text(
                [], "session", self.artifacts
            )

        self.assertEqual((text, file_path), ("识别成功", "saved.wav"))
        args, kwargs = post.call_args
        self.assertEqual(args[0], ASRProvider.API_URL)
        self.assertEqual(kwargs["headers"]["X-Api-Key"], "new-console-api-key")
        self.assertEqual(
            kwargs["headers"]["X-Api-Resource-Id"],
            ASRProvider.RESOURCE_ID,
        )
        self.assertEqual(kwargs["json"]["audio"]["format"], "wav")
        self.assertNotIn("new-console-api-key", str(kwargs["json"]))

    async def test_provider_rejection_returns_empty_without_leaking_key(self):
        with patch(
            "core.providers.asr.doubao_flash.requests.Session.post",
            return_value=_Response(status_code="45000000"),
        ), patch("core.providers.asr.doubao_flash.logger") as provider_logger:
            result = await self.provider.speech_to_text(
                [], "session", self.artifacts
            )

        self.assertEqual(result, ("", "saved.wav"))
        log_call = provider_logger.bind.return_value.error.call_args
        self.assertIsNotNone(log_call)
        self.assertNotIn("new-console-api-key", str(log_call))

    async def test_close_releases_persistent_http_session(self):
        with patch.object(self.provider._http_session, "close") as close:
            await self.provider.close()
        close.assert_called_once_with()

    def test_request_timeout_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "request_timeout"):
            ASRProvider(
                {
                    "api_key": "key",
                    "request_timeout": 0,
                    "output_dir": self.output_dir.name,
                },
                True,
            )


if __name__ == "__main__":
    unittest.main()
