import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from plugins_func.functions.retrieve_from_cyjdata import (
    RetrievalRuntimeClient,
    _format_context,
    _load_config,
    close_retrieval_runtime_client,
    retrieve_from_cyjdata,
)
from plugins_func.register import Action


def connection(**plugin_overrides):
    plugin = {
        "base_url": "http://retrieval-runtime:8090",
        "allowed_hosts": ["retrieval-runtime"],
        "domains": ["product", "publicKnowledge", "courseCatalog"],
        "max_results": 4,
        "timeout_seconds": 3.2,
    }
    plugin.update(plugin_overrides)
    return SimpleNamespace(config={"plugins": {"retrieve_from_cyjdata": plugin}})


class RetrievalRuntimePluginTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.auth_env = patch.dict(
            os.environ,
            {"RETRIEVAL_AUTH_TOKEN": "test-retrieval-token-0000000000000000"},
        )
        self.auth_env.start()
        self.addCleanup(self.auth_env.stop)

    async def test_returns_bounded_grounded_context(self):
        payload = {
            "contractVersion": 1,
            "items": [
                {
                    "kind": "product",
                    "title": "幼猫粮",
                    "summary": "适合离乳期幼猫",
                    "score": 0.91,
                    "sourceRef": "product:123",
                    "ignored": "x" * 10000,
                }
            ],
            "degraded": True,
            "degradedReasons": ["knowledge:POLARSEARCH_UNAVAILABLE"],
        }
        fake_client = SimpleNamespace(retrieve=AsyncMock(return_value=payload))
        conn = connection()
        with patch(
            "plugins_func.functions.retrieve_from_cyjdata._get_client",
            new=AsyncMock(return_value=fake_client),
        ):
            response = await retrieve_from_cyjdata(conn, "幼猫吃什么粮")

        self.assertEqual(Action.REQLLM, response.action)
        self.assertIn("幼猫粮", response.result)
        self.assertIn("product:123", response.result)
        self.assertIn("资料不足时明确说明", response.result)
        self.assertNotIn("ignored", response.result)
        self.assertLessEqual(len(response.result), 6000)

    async def test_timeout_is_generic_and_does_not_interrupt_conversation(self):
        fake_client = SimpleNamespace(
            retrieve=AsyncMock(side_effect=httpx.ReadTimeout("contains secret"))
        )
        conn = connection()
        with patch(
            "plugins_func.functions.retrieve_from_cyjdata._get_client",
            new=AsyncMock(return_value=fake_client),
        ):
            response = await retrieve_from_cyjdata(conn, "查询内部资料")

        self.assertEqual(Action.REQLLM, response.action)
        self.assertIn("暂时不可用", response.result)
        self.assertNotIn("secret", response.result)

    async def test_client_is_closed_with_connection(self):
        fake_client = SimpleNamespace(close=AsyncMock())
        conn = connection()
        conn._retrieval_runtime_client = fake_client

        await close_retrieval_runtime_client(conn)

        fake_client.close.assert_awaited_once()
        self.assertIsNone(conn._retrieval_runtime_client)

    def test_config_rejects_untrusted_host_and_restricted_domain(self):
        with self.assertRaises(ValueError):
            _load_config(connection(base_url="http://attacker.invalid"))

        config = _load_config(connection(domains=["restrictedKnowledge", "product"]))
        self.assertEqual(("product",), config.domains)

        config = _load_config(connection(domains="product;publicKnowledge"))
        self.assertEqual(("product", "publicKnowledge"), config.domains)
        self.assertNotIn(config.auth_token, map(str, config.identity))

        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            _load_config(connection())

    def test_client_sends_runtime_token_as_a_header(self):
        config = _load_config(connection())
        with patch(
            "plugins_func.functions.retrieve_from_cyjdata.httpx.AsyncClient"
        ) as client_factory:
            RetrievalRuntimeClient(config)

        headers = client_factory.call_args.kwargs["headers"]
        self.assertEqual(config.auth_token, headers["X-Retrieval-Token"])

    def test_context_without_results_is_explicit(self):
        context = _format_context(
            "问题",
            {
                "contractVersion": 1,
                "items": [],
                "answerable": False,
                "degraded": False,
            },
        )
        self.assertIn("没有找到足够可靠的资料", context)
        self.assertIn("现有资料不足以可靠回答", context)


if __name__ == "__main__":
    unittest.main()
