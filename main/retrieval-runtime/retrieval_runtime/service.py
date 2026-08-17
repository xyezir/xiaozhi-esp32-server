from __future__ import annotations

import asyncio
import hashlib
import json
import math
import re
import time
import uuid
from typing import Any

from .cache import AsyncTtlCache
from .models import RetrievalItem, RetrieveRequest, RetrieveResponse
from .settings import Settings
from .upstream import CyjdataClient, UpstreamError

_SAFE_METADATA_FIELDS = (
    "brand",
    "category",
    "barcode",
    "image",
    "imageUrl",
    "productId",
    "courseId",
    "resourceId",
)
_REASON_CODE = re.compile(r"^[A-Za-z0-9_:-]{1,100}$")


def _limited_text(value: Any, maximum: int) -> str:
    if value is None:
        return ""
    normalized = " ".join(str(value).split())
    return normalized[:maximum]


def _score(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _degraded_reason(value: Any) -> str:
    normalized = _limited_text(value, 100)
    return normalized if _REASON_CODE.fullmatch(normalized) else "UPSTREAM_DEGRADED"


def _source_ref(item: dict[str, Any]) -> str | None:
    for field in (
        "sourceRef",
        "source_ref",
        "chunkRef",
        "chunk_id",
        "productId",
        "product_id",
        "barcode",
        "documentId",
        "document_id",
    ):
        value = _limited_text(item.get(field), 300)
        if value:
            return value
    return None


def _metadata(item: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in _SAFE_METADATA_FIELDS:
        value = item.get(field)
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            limited = _limited_text(value, 500)
            if limited:
                result[field] = limited
    return result


def _product_item(item: Any) -> RetrievalItem | None:
    if not isinstance(item, dict):
        return None
    title = _limited_text(item.get("name") or item.get("title"), 300)
    if not title:
        return None
    summary = _limited_text(
        item.get("summary")
        or item.get("description")
        or item.get("sellingPoints")
        or " ".join(
            value
            for value in (
                _limited_text(item.get("brand"), 100),
                _limited_text(item.get("category"), 100),
            )
            if value
        ),
        1200,
    )
    return RetrievalItem(
        kind="product",
        title=title,
        summary=summary,
        score=_score(item.get("score") or item.get("_score")),
        sourceRef=_source_ref(item),
        metadata=_metadata(item),
    )


def _knowledge_item(item: Any, kind: str = "knowledge") -> RetrievalItem | None:
    if not isinstance(item, dict):
        return None
    title = _limited_text(
        item.get("title")
        or item.get("name")
        or item.get("documentTitle")
        or "知识片段",
        300,
    )
    summary = _limited_text(
        item.get("summary")
        or item.get("content")
        or item.get("text")
        or item.get("snippet"),
        1200,
    )
    if not summary and title == "知识片段":
        return None
    return RetrievalItem(
        kind="courseCatalog" if kind == "courseCatalog" else "knowledge",
        title=title,
        summary=summary,
        score=_score(item.get("score") or item.get("rerankScore")),
        sourceRef=_source_ref(item),
        metadata=_metadata(item),
    )


class RetrievalService:
    def __init__(
        self,
        settings: Settings,
        upstream: CyjdataClient,
        *,
        cache: AsyncTtlCache[RetrieveResponse] | None = None,
    ):
        self._settings = settings
        self._upstream = upstream
        self._cache = cache or AsyncTtlCache(
            settings.cache_ttl_seconds,
            settings.cache_max_entries,
        )

    async def close(self) -> None:
        await self._upstream.close()

    async def retrieve(self, request: RetrieveRequest) -> RetrieveResponse:
        cache_key = self._cache_key(request)
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached.model_copy(update={"cached": True, "latency_ms": 0})

        started = time.monotonic()
        tasks: list[tuple[str, asyncio.Task[dict]]] = []
        if "product" in request.domains:
            tasks.append(
                (
                    "product",
                    asyncio.create_task(
                        self._upstream.search_products(request.query, request.limit)
                    ),
                )
            )
        knowledge_domains = {
            domain
            for domain in request.domains
            if domain in {"publicKnowledge", "courseCatalog"}
        }
        if knowledge_domains:
            request_id = request.request_id or f"xiaozhi-{uuid.uuid4().hex}"
            tasks.append(
                (
                    "knowledge",
                    asyncio.create_task(
                        self._upstream.search_public_knowledge(
                            request_id=request_id,
                            query=request.query,
                            include_knowledge="publicKnowledge" in knowledge_domains,
                            include_course_catalog="courseCatalog" in knowledge_domains,
                            limit=request.limit,
                        )
                    ),
                )
            )

        items: list[RetrievalItem] = []
        degraded_reasons: list[str] = []
        for source, task in tasks:
            try:
                payload = await task
            except UpstreamError as exc:
                degraded_reasons.append(f"{source}:{exc.reason}")
                continue
            if payload.get("degraded") is True:
                reason = _degraded_reason(
                    payload.get("reason") or payload.get("degradedReason")
                )
                degraded_reasons.append(f"{source}:{reason}")
            if source == "product":
                for raw in _items(payload.get("items")):
                    normalized = _product_item(raw)
                    if normalized is not None:
                        items.append(normalized)
            else:
                for raw in _items(payload.get("items")):
                    normalized = _knowledge_item(raw)
                    if normalized is not None:
                        items.append(normalized)
                for raw in _items(payload.get("courseCandidates")):
                    normalized = _knowledge_item(raw, "courseCatalog")
                    if normalized is not None:
                        items.append(normalized)

        items = items[: request.limit]
        source_refs = list(
            dict.fromkeys(item.source_ref for item in items if item.source_ref)
        )
        response = RetrieveResponse(
            answerable=bool(items),
            items=items,
            sourceRefs=source_refs,
            degraded=bool(degraded_reasons),
            degradedReasons=list(dict.fromkeys(degraded_reasons)),
            latencyMs=max(0, int((time.monotonic() - started) * 1000)),
            cached=False,
        )
        await self._cache.put(cache_key, response)
        return response

    @staticmethod
    def _cache_key(request: RetrieveRequest) -> str:
        encoded = json.dumps(
            {
                "query": request.query,
                "domains": sorted(request.domains),
                "limit": request.limit,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
