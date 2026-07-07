"""FastAPI application entry point for the Forge agent layer."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from forge import __version__
from forge.api.generation import router as generation_router
from forge.api.workflows import router as workflows_router
from forge.config import Settings, get_settings
from forge.db.base import create_db_engine, create_session_factory
from forge.engine_adapter import N8nAdapter


def create_app(settings: Settings | None = None) -> FastAPI:
    """App factory so tests can inject their own settings/database."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings.database_url)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        # Tests replace this with a fake; nothing outside engine_adapter
        # may know the engine is n8n.
        app.state.engine_adapter = N8nAdapter(settings.n8n_base_url, settings.n8n_api_key)
        # Shared connection pool for the generation job queue.
        app.state.redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        yield
        engine.dispose()
        app.state.redis.close()

    app = FastAPI(title="Forge Agent Layer", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.include_router(workflows_router)
    app.include_router(generation_router)

    @app.get("/health")
    def health(request: Request) -> JSONResponse:
        """Liveness + dependency check; 503 when Postgres or Redis is down.

        Used as the compose healthcheck, so it must not require an API key
        or any state beyond the two datastores.
        """
        checks: dict[str, Any] = {
            "database": _check_database(request),
            "redis": _check_redis(settings),
        }
        ok = all(checks.values())
        return JSONResponse(
            status_code=200 if ok else 503,
            content={"status": "ok" if ok else "degraded", "version": __version__, **checks},
        )

    return app


def _check_database(request: Request) -> bool:
    try:
        with request.app.state.session_factory() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _check_redis(settings: Settings) -> bool:
    try:
        client: redis.Redis = redis.Redis.from_url(
            settings.redis_url, socket_connect_timeout=2, socket_timeout=2
        )
        try:
            return bool(client.ping())
        finally:
            client.close()
    except Exception:
        return False


app = create_app()
