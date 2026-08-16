import asyncio
import unittest

from core.handle.textHandler.listenMessageHandler import ListenTextMessageHandler


class _Logger:
    def bind(self, **_kwargs):
        return self

    def debug(self, *_args, **_kwargs):
        return None


class _Connection:
    def __init__(self, vad_resume_task):
        self.logger = _Logger()
        self.client_listen_mode = None
        self.just_woken_up = True
        self.vad_resume_task = vad_resume_task
        self.reset_count = 0

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


if __name__ == "__main__":
    unittest.main()
