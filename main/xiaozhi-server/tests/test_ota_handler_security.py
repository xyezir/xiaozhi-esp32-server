import json
import time
import unittest
from unittest.mock import patch

from core.api.ota_handler import OTAHandler


class _Request:
    method = "POST"
    scheme = "http"

    def __init__(self, headers, body):
        self.headers = headers
        self._body = body

    async def text(self):
        return json.dumps(self._body)


class _Logger:
    def __init__(self):
        self.messages = []

    def bind(self, **_kwargs):
        return self

    def debug(self, message):
        self.messages.append(message)

    def info(self, message):
        self.messages.append(message)

    def warning(self, message):
        self.messages.append(message)

    def error(self, message):
        self.messages.append(message)


class OTAHandlerSecurityTest(unittest.IsolatedAsyncioTestCase):
    def _handler(self, **server_overrides):
        server = {
            "auth_key": "test-only-secret",
            "auth": {"enabled": False},
            "port": 8000,
            "http_port": 8003,
            "websocket": "ws://device.example/xiaozhi/v1/",
            "mqtt_gateway": None,
            **server_overrides,
        }
        logger = _Logger()
        with patch("core.api.base_handler.setup_logging", return_value=logger):
            handler = OTAHandler({"server": server, "firmware_cache_ttl": 30})
        handler._test_logger = logger
        handler._bin_cache = {
            "updated_at": int(time.time()),
            "ttl": 30,
            "files_by_model": {
                "esp32-s3-touch-amoled-1.75": [
                    ("2.0.0", "esp32-s3-touch-amoled-1.75_2.0.0.bin")
                ]
            },
        }
        return handler

    def _request(self):
        return _Request(
            {
                "device-id": "00:11:22:33:44:55",
                "client-id": "security-test-client",
                "device-model": "esp32-s3-touch-amoled-1.75",
                "device-version": "1.0.0",
                "Host": "attacker.invalid",
                "X-Forwarded-Host": "attacker.invalid",
                "X-Forwarded-Proto": "https",
            },
            {},
        )

    async def test_download_url_uses_trusted_public_ota_origin(self):
        response = await self._handler(
            ota_public_url="https://updates.example.com"
        ).handle_post(self._request())

        payload = json.loads(response.text)
        self.assertEqual("2.0.0", payload["firmware"]["version"])
        self.assertEqual(
            "https://updates.example.com/xiaozhi/ota/download/"
            "esp32-s3-touch-amoled-1.75_2.0.0.bin",
            payload["firmware"]["url"],
        )
        self.assertNotIn("attacker.invalid", payload["firmware"]["url"])

    async def test_missing_trusted_origin_fails_closed(self):
        response = await self._handler(
            vision_explain="http://legacy.invalid/not-the-trusted-path"
        ).handle_post(self._request())

        payload = json.loads(response.text)
        self.assertEqual("1.0.0", payload["firmware"]["version"])
        self.assertEqual("", payload["firmware"]["url"])

    async def test_malformed_configured_origins_fail_closed(self):
        for configured_origin in (
            "http://updates.example.com:not-a-port",
            "http://updates example.com",
            "http://updates%2eexample.com",
        ):
            with self.subTest(configured_origin=configured_origin):
                response = await self._handler(
                    ota_public_url=configured_origin
                ).handle_post(self._request())

                payload = json.loads(response.text)
                self.assertEqual("1.0.0", payload["firmware"]["version"])
                self.assertEqual("", payload["firmware"]["url"])

    async def test_vision_origin_is_allowed_only_for_exact_trusted_path(self):
        response = await self._handler(
            vision_explain="http://192.168.31.225:8003/mcp/vision/explain"
        ).handle_post(self._request())

        payload = json.loads(response.text)
        self.assertEqual(
            "http://192.168.31.225:8003/xiaozhi/ota/download/"
            "esp32-s3-touch-amoled-1.75_2.0.0.bin",
            payload["firmware"]["url"],
        )

    async def test_request_secrets_and_device_identifiers_are_not_logged(self):
        request = self._request()
        request.headers["Authorization"] = "Bearer test-only-secret"
        handler = self._handler(ota_public_url="https://updates.example.com")

        await handler.handle_post(request)

        logs = "\n".join(str(message) for message in handler._test_logger.messages)
        self.assertNotIn("Bearer test-only-secret", logs)
        self.assertNotIn("00:11:22:33:44:55", logs)
        self.assertNotIn("security-test-client", logs)


if __name__ == "__main__":
    unittest.main()
