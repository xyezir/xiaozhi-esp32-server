import unittest

from core.providers.llm.openai.openai import LLMProvider
from core.providers.tts.alibl_stream import TTSProvider
from core.providers.tts.dto.dto import InterfaceType


class ProviderCanaryContractTest(unittest.TestCase):
    def test_low_latency_qwen_candidate_is_bounded_and_disables_thinking(self):
        provider = LLMProvider(
            {
                "model_name": "qwen3.7-flash",
                "api_key": "test-placeholder",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "timeout": {"connect": 3, "read": 20, "write": 5, "pool": 2},
                "max_tokens": 180,
            }
        )
        request_params = {}

        provider._apply_thinking_disabled(request_params)

        self.assertEqual(provider.model_name, "qwen3.7-flash")
        self.assertEqual(provider.max_tokens, 180)
        self.assertEqual(provider.client.timeout.connect, 3)
        self.assertEqual(provider.client.timeout.read, 20)
        self.assertEqual(
            request_params, {"extra_body": {"enable_thinking": False}}
        )

    def test_cosyvoice_candidate_uses_bounded_dual_stream_adapter(self):
        provider = TTSProvider(
            {
                "api_key": "test-placeholder",
                "model": "cosyvoice-v2",
                "voice": "longcheng_v2",
                "tts_timeout": 12,
            },
            True,
        )

        self.assertEqual(provider.model, "cosyvoice-v2")
        self.assertEqual(provider.voice, "longcheng_v2")
        self.assertEqual(provider.tts_timeout, 12)
        self.assertEqual(provider.interface_type, InterfaceType.DUAL_STREAM)


if __name__ == "__main__":
    unittest.main()
