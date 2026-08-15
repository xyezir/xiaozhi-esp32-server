import asyncio
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from core.providers.tts.huoshan_double_stream import (
    Header,
    Optional,
    Response,
    TTSProvider,
)
from core.providers.tts.dto.dto import InterfaceType


class HuoshanDoubleStreamTTSSecurityTest(unittest.TestCase):
    def setUp(self):
        self.output_dir = tempfile.TemporaryDirectory()
        self.provider = TTSProvider(
            {
                "appid": "test-app",
                "access_token": "secret-access-token",
                "resource_id": "test-resource",
                "speaker": "test-speaker",
                "ws_url": "wss://example.invalid/tts",
                "output_dir": self.output_dir.name,
                "tts_timeout": 7,
            },
            True,
        )

    def tearDown(self):
        self.output_dir.cleanup()

    def test_provider_is_dual_stream_and_connection_is_bounded(self):
        websocket = AsyncMock()
        stop_event = threading.Event()
        stop_event.set()
        self.provider.conn = SimpleNamespace(stop_event=stop_event)

        with patch(
            "core.providers.tts.huoshan_double_stream.websockets.connect",
            new=AsyncMock(return_value=websocket),
        ) as connect:
            asyncio.run(self.provider._ensure_connection())

        self.assertEqual(self.provider.interface_type, InterfaceType.DUAL_STREAM)
        self.assertEqual(connect.await_args.kwargs["open_timeout"], 7)
        self.assertEqual(connect.await_args.kwargs["close_timeout"], 5)
        headers = connect.await_args.kwargs["additional_headers"]
        self.assertEqual(headers["X-Api-App-Key"], "test-app")
        self.assertEqual(headers["X-Api-Access-Key"], "secret-access-token")
        self.assertNotIn("X-Api-Key", headers)

    def test_current_console_api_key_uses_single_header(self):
        provider = TTSProvider(
            {
                "api_key": "secret-current-console-key",
                "appid": "你的火山引擎语音合成服务appid",
                "access_token": "你的火山引擎语音合成服务access_token",
                "resource_id": "seed-tts-2.0",
                "speaker": "test-speaker",
                "ws_url": "wss://example.invalid/tts",
                "output_dir": self.output_dir.name,
            },
            True,
        )

        headers = provider._build_ws_headers()

        self.assertEqual(headers["X-Api-Key"], "secret-current-console-key")
        self.assertEqual(headers["X-Api-Resource-Id"], "seed-tts-2.0")
        self.assertNotIn("X-Api-App-Key", headers)
        self.assertNotIn("X-Api-Access-Key", headers)

    def test_explicit_api_key_wins_when_both_auth_modes_are_configured(self):
        provider = TTSProvider(
            {
                "api_key": "secret-current-console-key",
                "appid": "test-app",
                "access_token": "secret-access-token",
                "resource_id": "test-resource",
                "speaker": "test-speaker",
                "ws_url": "wss://example.invalid/tts",
                "output_dir": self.output_dir.name,
            },
            True,
        )

        headers = provider._build_ws_headers()

        self.assertEqual(set(headers) & {
            "X-Api-Key", "X-Api-App-Key", "X-Api-Access-Key"
        }, {"X-Api-Key"})

    def test_credentials_are_normalized_before_headers_are_built(self):
        provider = TTSProvider(
            {
                "appid": 123456,
                "access_token": "  secret-access-token  ",
                "resource_id": "test-resource",
                "speaker": "test-speaker",
                "ws_url": "wss://example.invalid/tts",
                "output_dir": self.output_dir.name,
            },
            True,
        )

        headers = provider._build_ws_headers()

        self.assertEqual(headers["X-Api-App-Key"], "123456")
        self.assertEqual(headers["X-Api-Access-Key"], "secret-access-token")

    def test_missing_auth_fails_before_network(self):
        provider = TTSProvider(
            {
                "api_key": "你的豆包语音新版控制台API Key",
                "appid": "你的火山引擎语音合成服务appid",
                "access_token": "你的火山引擎语音合成服务access_token",
                "resource_id": "test-resource",
                "speaker": "test-speaker",
                "ws_url": "wss://example.invalid/tts",
                "output_dir": self.output_dir.name,
            },
            True,
        )

        with self.assertRaisesRegex(ValueError, "鉴权未配置"):
            provider._build_ws_headers()

    def test_response_metadata_is_not_logged(self):
        response = Response(Header(message_type=9), Optional(event=51))
        response.optional.connectionId = "private-connection-id"
        response.optional.sessionId = "private-session-id"
        response.optional.response_meta_json = "secret-provider-response"
        response.optional.errorCode = 403
        bound_logger = Mock()

        with patch(
            "core.providers.tts.huoshan_double_stream.logger"
        ) as logger:
            logger.bind.return_value = bound_logger
            self.provider.print_response(response, "ignored")

        message = bound_logger.debug.call_args.args[0]
        self.assertIn("event=51", message)
        self.assertIn("error_code=403", message)
        self.assertNotIn("private", message)
        self.assertNotIn("secret", message)

    def test_provider_exception_payload_is_redacted(self):
        self.provider.ws = AsyncMock()
        self.provider.conn = SimpleNamespace(sentence_id="private-session-id")
        self.provider.send_text = AsyncMock(
            side_effect=RuntimeError("secret-access-token private reply")
        )
        bound_logger = Mock()

        with patch(
            "core.providers.tts.huoshan_double_stream.logger"
        ) as logger:
            logger.bind.return_value = bound_logger
            with self.assertRaises(RuntimeError):
                asyncio.run(self.provider.text_to_speak("private reply", None))

        messages = " ".join(
            call.args[0]
            for call in bound_logger.error.call_args_list
        )
        self.assertIn("RuntimeError", messages)
        self.assertNotIn("private reply", messages)
        self.assertNotIn("secret-access-token", messages)

    def test_placeholder_access_token_is_not_echoed(self):
        placeholder = "你的火山引擎语音合成服务access_token"
        bound_logger = Mock()

        with patch(
            "core.providers.tts.huoshan_double_stream.logger"
        ) as logger:
            logger.bind.return_value = bound_logger
            TTSProvider(
                {
                    "appid": "test-app",
                    "access_token": placeholder,
                    "resource_id": "test-resource",
                    "speaker": "test-speaker",
                    "ws_url": "wss://example.invalid/tts",
                    "output_dir": self.output_dir.name,
                },
                True,
            )

        message = bound_logger.error.call_args.args[0]
        self.assertIn("需要新版 API Key", message)
        self.assertNotIn(placeholder, message)
        self.assertNotIn("当前值", message)


if __name__ == "__main__":
    unittest.main()
