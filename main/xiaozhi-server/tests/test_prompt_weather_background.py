import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.utils.prompt_manager import PromptManager


class _Cache:
    def __init__(self):
        self.values = {}

    def get(self, cache_type, key):
        return self.values.get((cache_type, key))

    def set(self, cache_type, key, value):
        self.values[(cache_type, key)] = value


class _Logger:
    def bind(self, **_kwargs):
        return self

    def debug(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass


class PromptWeatherBackgroundTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.manager = object.__new__(PromptManager)
        self.manager.logger = _Logger()
        self.manager.cache_manager = _Cache()
        self.manager.CacheType = SimpleNamespace(WEATHER="weather")
        self.manager._weather_refresh_inflight = set()
        self.conn = SimpleNamespace(loop=asyncio.get_running_loop())

    async def test_schedule_returns_without_waiting_for_provider(self):
        provider_started = asyncio.Event()
        provider_release = asyncio.Event()

        async def slow_refresh(_conn, location):
            self.manager._weather_refresh_inflight.add(location)
            provider_started.set()
            await provider_release.wait()
            self.manager._weather_refresh_inflight.discard(location)

        with patch.object(self.manager, "_refresh_weather_info", slow_refresh):
            started = self.conn.loop.time()
            self.manager._schedule_weather_refresh(self.conn, "test-city")
            elapsed = self.conn.loop.time() - started

            self.assertLess(elapsed, 0.05)
            await asyncio.wait_for(provider_started.wait(), timeout=0.2)
            provider_release.set()
            await asyncio.sleep(0)

    async def test_duplicate_refresh_is_coalesced(self):
        calls = 0
        provider_release = asyncio.Event()

        async def slow_refresh(_conn, location):
            nonlocal calls
            calls += 1
            await provider_release.wait()
            self.manager._weather_refresh_inflight.discard(location)

        with patch.object(self.manager, "_refresh_weather_info", slow_refresh):
            self.manager._schedule_weather_refresh(self.conn, "test-city")
            self.manager._schedule_weather_refresh(self.conn, "test-city")
            await asyncio.sleep(0)
            self.assertEqual(calls, 1)
            provider_release.set()
            await asyncio.sleep(0)

    def test_legacy_weather_context_requires_explicit_plugin(self):
        self.conn.config = {"plugins": {"maps_weather": {}}}
        self.assertFalse(self.manager._legacy_weather_context_enabled(self.conn))

        self.conn.config = {"plugins": {"get_weather": {}}}
        self.assertTrue(self.manager._legacy_weather_context_enabled(self.conn))

    def test_legacy_weather_context_rejects_invalid_config(self):
        self.conn.config = None
        self.assertFalse(self.manager._legacy_weather_context_enabled(self.conn))

        self.conn.config = {"plugins": []}
        self.assertFalse(self.manager._legacy_weather_context_enabled(self.conn))


if __name__ == "__main__":
    unittest.main()
