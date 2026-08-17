import asyncio
import json
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from core.connection import ConnectionHandler
from core.handle.receiveAudioHandle import check_bind_device
from config.config_loader import get_private_config_from_api


class _Logger:
    def bind(self, **_kwargs):
        return self

    def debug(self, *_args, **_kwargs):
        return None

    def info(self, *_args, **_kwargs):
        return None

    def warning(self, *_args, **_kwargs):
        return None

    def error(self, *_args, **_kwargs):
        return None


class BindInitializationRaceTest(unittest.IsolatedAsyncioTestCase):
    def _make_closable_connection(self):
        conn = ConnectionHandler.__new__(ConnectionHandler)
        conn.logger = _Logger()
        conn.stop_event = threading.Event()
        conn.background_init_task = None
        conn.component_init_future = None
        conn.vad = None
        conn.audio_buffer = []
        conn.timeout_task = None
        conn._aec_cache_cleanup_task = None
        conn.func_handler = None
        conn.websocket = SimpleNamespace(close=AsyncMock(), closed=False)
        conn.tts = None
        conn.asr = None
        conn.executor = None
        conn.clear_queues = lambda: None
        return conn

    async def test_real_hello_bypasses_manager_and_sends_welcome(self):
        conn = ConnectionHandler.__new__(ConnectionHandler)
        conn.logger = _Logger()
        conn.components_ready_event = asyncio.Event()
        conn.websocket = SimpleNamespace(send=AsyncMock())
        conn.welcome_msg = {
            "session_id": "test-session",
            "audio_params": {"sample_rate": 24000},
        }

        await ConnectionHandler._route_message(
            conn,
            json.dumps({"type": "hello"}),
        )

        conn.websocket.send.assert_awaited_once_with(json.dumps(conn.welcome_msg))

    async def test_control_message_waits_for_components_above_one_second(self):
        conn = ConnectionHandler.__new__(ConnectionHandler)
        conn.components_ready_event = asyncio.Event()
        conn.initialization_failed = False
        conn.need_bind = False

        async def finish_initialization():
            await asyncio.sleep(1.1)
            conn.components_ready_event.set()

        initialization = asyncio.create_task(finish_initialization())
        with patch("core.connection.handleTextMessage", new=AsyncMock()) as route:
            await ConnectionHandler._route_message(
                conn,
                json.dumps({"type": "listen", "state": "start"}),
            )
        await initialization

        route.assert_awaited_once()

    async def test_pending_lookup_never_schedules_false_bind_prompt(self):
        conn = SimpleNamespace(
            bind_completed_event=asyncio.Event(),
            need_bind=False,
            last_bind_prompt_time=0,
            bind_prompt_interval=60,
        )

        with patch(
            "core.handle.receiveAudioHandle.check_bind_device",
            new=AsyncMock(return_value=True),
        ) as prompt:
            await ConnectionHandler._discard_message_with_bind_prompt(conn)
            await asyncio.sleep(0)

        prompt.assert_not_awaited()
        self.assertEqual(conn.last_bind_prompt_time, 0)

    async def test_confirmed_unbound_device_is_still_prompted(self):
        ready = asyncio.Event()
        ready.set()
        conn = SimpleNamespace(
            bind_completed_event=ready,
            need_bind=True,
            last_bind_prompt_time=0,
            bind_prompt_interval=60,
        )

        with patch(
            "core.handle.receiveAudioHandle.check_bind_device",
            new=AsyncMock(),
        ) as prompt:
            await ConnectionHandler._discard_message_with_bind_prompt(conn)
            await asyncio.sleep(0)

        prompt.assert_awaited_once_with(conn)
        self.assertGreater(conn.last_bind_prompt_time, time.time() - 1)

    async def test_bind_prompt_waits_for_tts_queue(self):
        conn = SimpleNamespace(tts=None, logger=_Logger())

        with patch(
            "core.handle.receiveAudioHandle.send_stt_message",
            new=AsyncMock(),
        ) as send_stt, patch(
            "core.handle.receiveAudioHandle.audio_to_data",
            new=AsyncMock(),
        ) as audio_to_data:
            queued = await check_bind_device(conn)

        self.assertFalse(queued)
        send_stt.assert_not_awaited()
        audio_to_data.assert_not_awaited()

    async def test_failed_prompt_does_not_consume_rate_limit(self):
        ready = asyncio.Event()
        ready.set()
        conn = SimpleNamespace(
            bind_completed_event=ready,
            need_bind=True,
            last_bind_prompt_time=0,
            bind_prompt_interval=60,
        )

        with patch(
            "core.handle.receiveAudioHandle.check_bind_device",
            new=AsyncMock(return_value=False),
        ):
            await ConnectionHandler._discard_message_with_bind_prompt(conn)

        self.assertEqual(conn.last_bind_prompt_time, 0)

    async def test_manager_failure_is_not_converted_to_empty_bound_config(self):
        with patch(
            "config.config_loader.get_agent_models",
            new=AsyncMock(side_effect=RuntimeError("manager unavailable")),
        ), patch(
            "config.config_loader.get_correct_words",
            new=AsyncMock(return_value=None),
        ):
            with self.assertRaisesRegex(RuntimeError, "manager unavailable"):
                await get_private_config_from_api(
                    {"selected_module": {}},
                    "device",
                    "client",
                )

    async def test_channel_failure_sets_terminal_state_and_closes(self):
        conn = ConnectionHandler.__new__(ConnectionHandler)
        conn.loop = asyncio.get_running_loop()
        conn.executor = None
        conn.component_init_future = None
        conn.initialization_timeout_seconds = 1
        conn.components_ready_event = asyncio.Event()
        conn.initialization_failed = False
        conn.need_bind = False
        conn.stop_event = threading.Event()
        conn.logger = _Logger()
        conn.websocket = SimpleNamespace(close=AsyncMock())
        conn.tts = SimpleNamespace(
            open_audio_channels=AsyncMock(side_effect=RuntimeError("tts failed"))
        )
        conn.asr = SimpleNamespace(open_audio_channels=AsyncMock())
        conn._initialize_private_config_async = AsyncMock()
        conn._prepare_components = lambda: {
            "tts": conn.tts,
            "vad": None,
            "asr": conn.asr,
        }
        conn._activate_components = lambda _components: None

        await ConnectionHandler._background_initialize(conn)

        self.assertTrue(conn.initialization_failed)
        self.assertTrue(conn.components_ready_event.is_set())
        conn.websocket.close.assert_awaited_once_with(
            code=1011,
            reason="device initialization failed",
        )

    async def test_initialization_deadline_wakes_waiters_and_closes(self):
        conn = ConnectionHandler.__new__(ConnectionHandler)
        conn.initialization_timeout_seconds = 0.01
        conn.initialization_failed = False
        conn.components_ready_event = asyncio.Event()
        conn.logger = _Logger()
        conn.websocket = SimpleNamespace(close=AsyncMock())

        async def never_ready():
            await asyncio.Event().wait()

        conn._initialize_until_ready = never_ready

        await ConnectionHandler._background_initialize(conn)

        self.assertTrue(conn.initialization_failed)
        self.assertTrue(conn.components_ready_event.is_set())
        conn.websocket.close.assert_awaited_once_with(
            code=1011,
            reason="device initialization timed out",
        )

    async def test_cancelling_initialization_wakes_waiters(self):
        conn = ConnectionHandler.__new__(ConnectionHandler)
        conn.initialization_timeout_seconds = 30
        conn.initialization_failed = False
        conn.components_ready_event = asyncio.Event()
        conn.logger = _Logger()
        conn.websocket = SimpleNamespace(close=AsyncMock())

        async def never_ready():
            await asyncio.Event().wait()

        conn._initialize_until_ready = never_ready
        task = asyncio.create_task(ConnectionHandler._background_initialize(conn))
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        self.assertTrue(conn.initialization_failed)
        self.assertTrue(conn.components_ready_event.is_set())

    async def test_close_from_timeout_task_never_awaits_itself(self):
        conn = self._make_closable_connection()

        async def close_from_timeout_task():
            conn.timeout_task = asyncio.current_task()
            await ConnectionHandler.close(conn, conn.websocket)

        await asyncio.wait_for(
            asyncio.create_task(close_from_timeout_task()),
            timeout=0.5,
        )

        self.assertGreaterEqual(conn.websocket.close.await_count, 1)

    async def test_close_does_not_wait_for_isolated_component_candidate(self):
        conn = self._make_closable_connection()
        conn.component_init_future = asyncio.get_running_loop().create_future()
        pending_candidate = conn.component_init_future

        await asyncio.wait_for(
            ConnectionHandler.close(conn, conn.websocket),
            timeout=0.5,
        )

        self.assertFalse(pending_candidate.done())
        pending_candidate.set_result({"tts": object()})
        await asyncio.sleep(0)

if __name__ == "__main__":
    unittest.main()
