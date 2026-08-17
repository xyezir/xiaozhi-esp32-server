from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from .models import RetrieveRequest, RetrieveResponse
from .service import RetrievalService
from .settings import Settings, SettingsError
from .upstream import CyjdataClient

LOG = logging.getLogger("retrieval-runtime")


def create_app(service: RetrievalService | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active_service = service
        if active_service is None:
            try:
                settings = Settings.from_env()
            except SettingsError:
                LOG.error("retrieval runtime configuration is invalid")
                raise
            active_service = RetrievalService(settings, CyjdataClient(settings))
        app.state.retrieval_service = active_service
        try:
            yield
        finally:
            await active_service.close()

    app = FastAPI(
        title="Xiaozhi Retrieval Runtime",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz(request: Request) -> dict[str, str]:
        if getattr(request.app.state, "retrieval_service", None) is None:
            raise HTTPException(status_code=503, detail="not ready")
        return {"status": "ready"}

    @app.post("/v1/retrieve", response_model=RetrieveResponse)
    async def retrieve(body: RetrieveRequest, request: Request) -> RetrieveResponse:
        active_service = getattr(request.app.state, "retrieval_service", None)
        if active_service is None:
            raise HTTPException(status_code=503, detail="not ready")
        return await active_service.retrieve(body)

    return app


app = create_app()
