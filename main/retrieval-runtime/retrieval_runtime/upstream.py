from __future__ import annotations

import httpx

from .settings import Settings


class UpstreamError(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class CyjdataClient:
    """Typed, least-privilege client for cyjdata-v2 retrieval endpoints."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        timeout = httpx.Timeout(
            settings.timeout_seconds,
            connect=settings.connect_timeout_seconds,
        )
        self._client = httpx.AsyncClient(
            base_url=settings.api_base_url,
            headers={
                "X-API-Key": settings.api_key,
                "Accept": "application/json",
                "User-Agent": "xiaozhi-retrieval-runtime/0.1",
            },
            timeout=timeout,
            verify=True,
            transport=transport,
            limits=httpx.Limits(max_connections=32, max_keepalive_connections=16),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def search_products(self, query: str, limit: int) -> dict:
        return await self._post(
            "/api/v2/internal/ai/search",
            {"query": query, "types": ["product"], "limit": limit},
        )

    async def search_public_knowledge(
        self,
        *,
        request_id: str,
        query: str,
        include_knowledge: bool,
        include_course_catalog: bool,
        limit: int,
    ) -> dict:
        types = []
        scopes = []
        if include_knowledge:
            types.append("knowledge")
            scopes.append("publicKnowledge")
        if include_course_catalog:
            types.append("courseCatalog")
            scopes.append("courseCatalog")
        return await self._post(
            "/api/v2/internal/ai/knowledge/search",
            {
                "contractVersion": 1,
                "requestId": request_id,
                "query": query,
                "types": types,
                "scopes": scopes,
                "allowedEntitlementKeys": [],
                "limit": min(limit, 10),
                "rerank": True,
            },
        )

    async def search_pfa_exhibitors(self, keyword: str, limit: int) -> dict:
        """Search the authoritative structured PFA exhibition projection.

        Booth data is synchronized independently of the knowledge-vector
        indexes, so it stays queryable while those indexes are being rebuilt.
        """
        return await self._get(
            "/api/v2/exhibitions/pfa/companies",
            {
                "year": 2026,
                "keyword": keyword,
                "page": 1,
                "page_size": min(limit, 20),
            },
        )

    async def _get(self, path: str, params: dict) -> dict:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, payload: dict) -> dict:
        return await self._request("POST", path, payload=payload)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        try:
            response = await self._client.request(
                method,
                path,
                json=payload,
                params=params,
            )
        except httpx.TimeoutException as exc:
            raise UpstreamError("UPSTREAM_TIMEOUT") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError("UPSTREAM_UNAVAILABLE") from exc
        if response.status_code in {401, 403}:
            raise UpstreamError("UPSTREAM_AUTH_FAILED")
        if response.status_code < 200 or response.status_code >= 300:
            raise UpstreamError("UPSTREAM_HTTP_ERROR")
        try:
            result = response.json()
        except ValueError as exc:
            raise UpstreamError("UPSTREAM_INVALID_RESPONSE") from exc
        if not isinstance(result, dict):
            raise UpstreamError("UPSTREAM_INVALID_RESPONSE")
        return result
