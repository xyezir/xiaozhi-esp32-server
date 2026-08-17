import asyncio
import time
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from core.providers.memory.powermem.powermem import MemoryProvider


class FakeUserMemory:
    def __init__(self, config):
        self.config = config
        self.added = None
        self.search_limit = None

    def add(self, messages, user_id):
        self.added = (messages, user_id)
        return {"profile_extracted": True, "profile_content": "喜欢简洁回答"}

    def profile(self, user_id):
        return {"profile_content": "喜欢简洁回答，并关注宠物行业"}

    def search(self, query, user_id, limit):
        self.search_limit = limit
        return {
            "results": [
                {
                    "memory": f"第{index}条记忆" + "很长" * 80,
                    "updated_at": f"2026-08-18T02:00:{index:02d}.000",
                }
                for index in range(10)
            ]
        }


def provider_config(**overrides):
    config = {
        "type": "powermem",
        "enable_user_profile": True,
        "llm_provider": "openai",
        "llm_api_key": "test-key",
        "llm_model": "qwen-plus",
        "openai_base_url": "https://dashscope.example/v1",
        "embedding_provider": "openai",
        "embedding_api_key": "test-key",
        "embedding_model": "text-embedding-v4",
        "embedding_openai_base_url": "https://dashscope.example/v1",
        "embedding_dims": 1024,
        "vector_store": {
            "provider": "sqlite",
            "config": {"database_path": ":memory:", "collection_name": "test"},
        },
        "search_limit": 4,
        "max_context_chars": 500,
        "profile_max_chars": 120,
        "memory_max_chars": 100,
        "save_message_limit": 4,
        "save_message_max_chars": 80,
    }
    config.update(overrides)
    return config


class PowerMemProviderTest(IsolatedAsyncioTestCase):
    def make_provider(self, **overrides):
        with patch("powermem.UserMemory", FakeUserMemory):
            provider = MemoryProvider(provider_config(**overrides))
        provider.init_memory("device-namespace", None)
        return provider

    async def test_query_is_bounded_for_voice_latency_and_context(self):
        provider = self.make_provider()

        result = await provider.query_memory("我之前喜欢什么？")

        self.assertLessEqual(len(result), 500)
        self.assertIn("【用户画像】", result)
        self.assertIn("【相关记忆】", result)
        self.assertEqual(provider.memory_client.search_limit, 4)

    async def test_save_excludes_system_and_tool_messages(self):
        provider = self.make_provider()
        messages = [
            SimpleNamespace(role="system", content="系统提示"),
            SimpleNamespace(role="tool", content="工具结果"),
            SimpleNamespace(role="user", content='{"content":"我喜欢猫"}'),
            SimpleNamespace(role="assistant", content="我记住了"),
            SimpleNamespace(role="assistant", content=None),
        ]

        await provider.save_memory(messages)

        saved, namespace = provider.memory_client.added
        self.assertEqual(namespace, "device-namespace")
        self.assertEqual(
            saved,
            [
                {"role": "user", "content": "我喜欢猫"},
                {"role": "assistant", "content": "我记住了"},
            ],
        )
        self.assertEqual(provider.last_profile_content, "喜欢简洁回答")

    async def test_query_timeout_fails_open(self):
        provider = self.make_provider(query_timeout_seconds=0.3)

        async def slow_query(_query):
            await asyncio.sleep(0.5)
            return "late"

        provider._query_memory = slow_query
        started = time.monotonic()
        result = await provider.query_memory("测试超时")

        self.assertEqual(result, "")
        self.assertLess(time.monotonic() - started, 0.45)


class PowerMemConfigTest(TestCase):
    def test_flat_config_forwards_embedding_dimensions(self):
        config = MemoryProvider._build_powermem_config(provider_config())

        self.assertEqual(config["embedder"]["config"]["embedding_dims"], 1024)
        self.assertEqual(config["vector_store"]["config"]["collection_name"], "test")
