import asyncio
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import dashscope

from core.providers.asr.base import ASRProviderBase
from core.providers.asr.qwen3_asr_flash import ASRProvider


class _Message:
    def __init__(self, text):
        self.content = [{"text": text}]


def _chunk(text):
    return {"output": {"choices": [{"message": _Message(text)}]}}


class Qwen3ASRFlashTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.output_dir = tempfile.TemporaryDirectory()
        self.provider = ASRProvider(
            {
                "api_key": "test-per-call-key",
                "output_dir": self.output_dir.name,
                "request_timeout": 1,
            },
            True,
        )
        self.artifacts = ASRProviderBase.AudioArtifacts(
            pcm_frames=[b"audio"],
            pcm_bytes=b"audio",
            file_path="saved.wav",
            temp_path="temporary.wav",
        )

    def tearDown(self):
        self.output_dir.cleanup()

    async def test_transcription_runs_off_event_loop_and_uses_per_call_key(self):
        worker_started = threading.Event()
        release_worker = threading.Event()
        original_global_key = getattr(dashscope, "api_key", None)

        def blocking_call(**kwargs):
            self.assertEqual(kwargs["api_key"], "test-per-call-key")
            self.assertEqual(kwargs["request_timeout"], 1)
            worker_started.set()
            release_worker.wait(timeout=1)
            return iter([_chunk("第一版"), _chunk(" 最终文本 ")])

        async def observe_event_loop():
            observed = await asyncio.to_thread(worker_started.wait, 1)
            self.assertTrue(observed)
            await asyncio.sleep(0)
            release_worker.set()

        with patch(
            "core.providers.asr.qwen3_asr_flash.dashscope.MultiModalConversation.call",
            side_effect=blocking_call,
        ):
            transcription, _ = await asyncio.gather(
                self.provider.speech_to_text([], "session", self.artifacts),
                observe_event_loop(),
            )

        self.assertEqual(transcription, ("最终文本", "saved.wav"))
        self.assertEqual(getattr(dashscope, "api_key", None), original_global_key)

    async def test_timeout_is_bounded_and_returns_empty_text(self):
        self.provider.request_timeout = 0.01

        def slow_call(**kwargs):
            time.sleep(0.05)
            return iter([_chunk("too late")])

        with patch(
            "core.providers.asr.qwen3_asr_flash.dashscope.MultiModalConversation.call",
            side_effect=slow_call,
        ):
            text, file_path = await self.provider.speech_to_text(
                [], "session", self.artifacts
            )

        self.assertEqual(text, "")
        self.assertEqual(file_path, "saved.wav")

    async def test_missing_artifacts_or_temp_file_returns_empty_text(self):
        self.assertEqual(
            await self.provider.speech_to_text([], "session", None),
            ("", None),
        )
        artifacts = ASRProviderBase.AudioArtifacts(
            pcm_frames=[b"audio"],
            pcm_bytes=b"audio",
            file_path="saved.wav",
            temp_path=None,
        )
        self.assertEqual(
            await self.provider.speech_to_text([], "session", artifacts),
            ("", "saved.wav"),
        )

    def test_request_timeout_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "request_timeout"):
            ASRProvider(
                {
                    "api_key": "test",
                    "output_dir": self.output_dir.name,
                    "request_timeout": 0,
                },
                True,
            )


if __name__ == "__main__":
    unittest.main()
