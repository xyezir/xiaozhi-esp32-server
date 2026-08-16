import asyncio
import unittest

from core.handle.textHandler.listenMessageHandler import ListenTextMessageHandler
from core.handle.receiveAudioHandle import handleAudioMessage


class _Logger:
    def bind(self, **_kwargs):
        return self

    def debug(self, *_args, **_kwargs):
        return None


class _Vad:
    def is_vad(self, _conn, _frame):
        return True


class _Asr:
    def __init__(self):
        self.frames = []

    async def receive_audio(self, _conn, frame, have_voice):
        self.frames.append((frame, have_voice))


class _Connection:
    def __init__(self, vad_resume_task):
        self.logger = _Logger()
        self.client_listen_mode = None
        self.just_woken_up = True
        self.vad_resume_task = vad_resume_task
        self.reset_count = 0
        self.vad = _Vad()
        self.asr = _Asr()
        self.client_aec = False
        self.client_is_speaking = False
        self.last_activity_time = 0.0
        self.close_after_chat = False
        self.config = {}

    def reset_audio_states(self):
        self.reset_count += 1


class MultiturnListenResumeTest(unittest.IsolatedAsyncioTestCase):
    async def test_listen_start_ends_wakeup_suppression(self):
        resume_task = asyncio.create_task(asyncio.sleep(60))
        conn = _Connection(resume_task)

        await ListenTextMessageHandler().handle(
            conn,
            {"type": "listen", "state": "start", "mode": "auto"},
        )
        await asyncio.sleep(0)

        self.assertEqual(conn.client_listen_mode, "auto")
        self.assertFalse(conn.just_woken_up)
        self.assertTrue(resume_task.cancelled())
        self.assertEqual(conn.reset_count, 1)

        frame = b"next-turn-pcm"
        await handleAudioMessage(conn, frame)
        self.assertEqual(conn.asr.frames, [(frame, True)])


if __name__ == "__main__":
    unittest.main()
