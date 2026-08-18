#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Bounded PowerMem provider for latency-sensitive voice conversations."""

import asyncio
import json
import math
import traceback
from typing import Any, Dict, Optional

from ..base import MemoryProviderBase, logger

TAG = __name__


def _bounded_int(config, key, default, minimum, maximum):
    try:
        value = int(config.get(key, default))
    except (TypeError, ValueError):
        return default
    return min(maximum, max(minimum, value))


def _bounded_float(config, key, default, minimum, maximum):
    try:
        value = float(config.get(key, default))
    except (TypeError, ValueError):
        return default
    if not math.isfinite(value):
        return default
    return min(maximum, max(minimum, value))


def _message_content(content):
    if content is None:
        return ""
    text = str(content)
    try:
        if text.strip().startswith("{") and text.strip().endswith("}"):
            data = json.loads(text)
            if "content" in data:
                text = str(data["content"] or "")
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return " ".join(text.split())


class MemoryProvider(MemoryProviderBase):
    """PowerMem with persistent-provider support and bounded voice latency."""

    def __init__(self, config: Dict[str, Any], summary_memory: Optional[str] = None):
        super().__init__(config)
        self.use_powermem = False
        self.memory_client = None
        self.enable_user_profile = False
        self.last_profile_content = ""
        self.search_limit = _bounded_int(config, "search_limit", 6, 1, 12)
        self.query_timeout_seconds = _bounded_float(
            config, "query_timeout_seconds", 1.5, 0.3, 5.0
        )
        self.save_timeout_seconds = _bounded_float(
            config, "save_timeout_seconds", 15.0, 2.0, 60.0
        )
        self.max_context_chars = _bounded_int(
            config, "max_context_chars", 1800, 400, 5000
        )
        self.profile_max_chars = _bounded_int(
            config, "profile_max_chars", 700, 100, 2000
        )
        self.memory_max_chars = _bounded_int(config, "memory_max_chars", 360, 80, 1200)
        self.save_message_limit = _bounded_int(config, "save_message_limit", 12, 2, 40)
        self.save_message_max_chars = _bounded_int(
            config, "save_message_max_chars", 1200, 200, 4000
        )

        try:
            self.enable_user_profile = (
                str(config.get("enable_user_profile", False)).lower() == "true"
            )
            powermem_config = self._build_powermem_config(config)

            if self.enable_user_profile:
                from powermem import UserMemory

                self.memory_client = UserMemory(config=powermem_config)
                memory_mode = "UserMemory"
            else:
                from powermem import AsyncMemory

                self.memory_client = AsyncMemory(config=powermem_config)
                memory_mode = "AsyncMemory"

            self.use_powermem = True
            storage = powermem_config.get(
                "vector_store", powermem_config.get("database", {})
            )
            logger.bind(tag=TAG).info(
                f"PowerMem initialized: mode={memory_mode}, "
                f"database={storage.get('provider', 'unknown')}, "
                f"llm={powermem_config['llm']['provider']}, "
                f"embedding={powermem_config['embedder']['provider']}, "
                f"search_limit={self.search_limit}, "
                f"query_timeout={self.query_timeout_seconds:.1f}s"
            )
        except ImportError as exc:
            logger.bind(tag=TAG).error(f"PowerMem is not installed: {exc}")
        except Exception as exc:
            logger.bind(tag=TAG).error(f"Failed to initialize PowerMem: {exc}")
            logger.bind(tag=TAG).debug(f"Detailed error: {traceback.format_exc()}")

    @staticmethod
    def _build_powermem_config(config):
        database_provider = config.get("database_provider", "sqlite")
        llm_provider = config.get("llm_provider", "qwen")
        embedding_provider = config.get("embedding_provider", "qwen")
        result = {}

        if "vector_store" in config:
            result["vector_store"] = config["vector_store"]
        elif "database" in config:
            result["database"] = config["database"]
        else:
            result["vector_store"] = {
                "provider": database_provider,
                "config": {},
            }

        if "llm" in config:
            result["llm"] = config["llm"]
        else:
            llm_config = {}
            if config.get("llm_api_key"):
                llm_config["api_key"] = config["llm_api_key"]
            if config.get("llm_model"):
                llm_config["model"] = config["llm_model"]
            if llm_provider == "qwen":
                base_url = config.get("dashscope_base_url") or config.get(
                    "llm_base_url"
                )
                if base_url:
                    llm_config["dashscope_base_url"] = base_url
            else:
                base_url = config.get("openai_base_url") or config.get("llm_base_url")
                if base_url:
                    llm_config["openai_base_url"] = base_url
            result["llm"] = {"provider": llm_provider, "config": llm_config}

        if "embedder" in config:
            result["embedder"] = config["embedder"]
        else:
            embedder_config = {}
            if config.get("embedding_api_key"):
                embedder_config["api_key"] = config["embedding_api_key"]
            if config.get("embedding_model"):
                embedder_config["model"] = config["embedding_model"]
            if config.get("embedding_dims"):
                embedder_config["embedding_dims"] = int(config["embedding_dims"])
            if embedding_provider == "qwen":
                base_url = config.get("embedding_dashscope_base_url") or config.get(
                    "embedding_base_url"
                )
                if base_url:
                    embedder_config["dashscope_base_url"] = base_url
            else:
                base_url = config.get("embedding_openai_base_url") or config.get(
                    "embedding_base_url"
                )
                if base_url:
                    embedder_config["openai_base_url"] = base_url
            result["embedder"] = {
                "provider": embedding_provider,
                "config": embedder_config,
            }
        return result

    async def save_memory(self, msgs, session_id=None):
        if not self.use_powermem or self.memory_client is None:
            logger.bind(tag=TAG).warning(
                "PowerMem is unavailable; memory was not saved"
            )
            return None

        messages = []
        for message in msgs[-self.save_message_limit :]:
            role = getattr(message, "role", "")
            if role not in {"user", "assistant"}:
                continue
            content = _message_content(getattr(message, "content", None))
            if content:
                messages.append(
                    {
                        "role": role,
                        "content": content[: self.save_message_max_chars],
                    }
                )
        if len(messages) < 2:
            logger.bind(tag=TAG).debug("Not enough user/assistant messages to save")
            return None

        try:
            if self.enable_user_profile:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.memory_client.add,
                        messages=messages,
                        user_id=self.role_id,
                    ),
                    timeout=self.save_timeout_seconds,
                )
            else:
                result = await asyncio.wait_for(
                    self.memory_client.add(messages=messages, user_id=self.role_id),
                    timeout=self.save_timeout_seconds,
                )
            logger.bind(tag=TAG).debug(
                f"Saved PowerMem batch with {len(messages)} messages"
            )
            if (
                self.enable_user_profile
                and isinstance(result, dict)
                and result.get("profile_extracted")
            ):
                self.last_profile_content = str(
                    result.get("profile_content", "") or ""
                )[: self.profile_max_chars]
                logger.bind(tag=TAG).debug("PowerMem user profile cache refreshed")
        except asyncio.TimeoutError:
            logger.bind(tag=TAG).warning("PowerMem save exceeded its time budget")
        except Exception as exc:
            logger.bind(tag=TAG).error(f"Error saving memory: {exc}")
            logger.bind(tag=TAG).debug(f"Detailed error: {traceback.format_exc()}")
        return None

    async def query_memory(self, query: str) -> str:
        if not self.use_powermem or self.memory_client is None:
            logger.bind(tag=TAG).warning("PowerMem is unavailable; recall was skipped")
            return ""
        if not getattr(self, "role_id", None):
            return ""
        search_query = _message_content(query)
        if not search_query:
            return ""
        try:
            return await asyncio.wait_for(
                self._query_memory(search_query),
                timeout=self.query_timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.bind(tag=TAG).warning(
                "PowerMem query exceeded the voice interaction time budget"
            )
        except Exception as exc:
            logger.bind(tag=TAG).error(f"Error querying memory: {exc}")
            logger.bind(tag=TAG).debug(f"Detailed error: {traceback.format_exc()}")
        return ""

    async def _query_memory(self, search_query: str) -> str:
        parts = []
        if self.enable_user_profile:
            profile = await self.get_user_profile()
            if profile:
                parts.append(f"【用户画像】\n{profile[: self.profile_max_chars]}")

        if self.enable_user_profile:
            results = await asyncio.to_thread(
                self.memory_client.search,
                query=search_query,
                user_id=self.role_id,
                limit=self.search_limit,
            )
        else:
            results = await self.memory_client.search(
                query=search_query,
                user_id=self.role_id,
                limit=self.search_limit,
            )

        memories = []
        if isinstance(results, dict):
            for entry in results.get("results", [])[: self.search_limit]:
                if not isinstance(entry, dict):
                    continue
                timestamp = str(
                    entry.get("updated_at") or entry.get("created_at") or ""
                )
                formatted_time = timestamp.split(".")[0].replace("T", " ")
                memory = _message_content(
                    entry.get("memory", "") or entry.get("content", "")
                )[: self.memory_max_chars]
                if not memory:
                    continue
                formatted = f"[{formatted_time}] {memory}" if timestamp else memory
                memories.append((timestamp, formatted))
        memories.sort(key=lambda item: item[0], reverse=True)
        if memories:
            memory_text = "\n".join(f"- {item[1]}" for item in memories)
            parts.append(f"【相关记忆】\n{memory_text}")

        result = "\n\n".join(parts)[: self.max_context_chars]
        logger.bind(tag=TAG).debug(
            f"PowerMem query returned {len(result)} context characters"
        )
        return result

    async def get_user_profile(self) -> str:
        if (
            not self.use_powermem
            or self.memory_client is None
            or not self.enable_user_profile
        ):
            return ""
        if self.last_profile_content:
            return self.last_profile_content[: self.profile_max_chars]

        try:
            profile_data = await asyncio.to_thread(
                self.memory_client.profile, self.role_id
            )
            if not isinstance(profile_data, dict):
                return ""
            profile_content = profile_data.get("profile_content")
            if profile_content:
                self.last_profile_content = str(profile_content)[
                    : self.profile_max_chars
                ]
            elif profile_data.get("topics"):
                self.last_profile_content = json.dumps(
                    profile_data["topics"],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )[: self.profile_max_chars]
            if self.last_profile_content:
                logger.bind(tag=TAG).info("PowerMem user profile cache populated")
            return self.last_profile_content
        except Exception as exc:
            logger.bind(tag=TAG).error(f"Failed to fetch PowerMem profile: {exc}")
            logger.bind(tag=TAG).debug(f"Detailed error: {traceback.format_exc()}")
            return ""
