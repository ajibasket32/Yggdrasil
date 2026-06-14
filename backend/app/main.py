from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.combat import router as combat_router
from app.api.gameplay import router as gameplay_router
from app.api.health import router as health_router
from app.api.narrative import router as narrative_router
from app.api.save import router as save_router
from app.api.world import router as world_router
from app.core.config import get_settings
from app.core.database import dispose_database
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.services.gameplay import GameplayError
from app.services.narrative import NarrativeError
from app.services.save import (
    IdempotencyConflictError,
    RecoveryPointError,
    SaveActiveCombatError,
    SaveCompatibilityError,
    SaveError,
    SaveIntegrityError,
    SaveNotFoundError,
)
from app.services.world import WorldError


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Release database resources when the API process stops."""
    yield
    await dispose_database()


async def handle_save_error(request: Request, exception: Exception) -> JSONResponse:
    """Return stable API errors for save workflow failures."""
    if not isinstance(exception, SaveError):
        raise exception
    error = exception
    status_code = 409
    code = "SAVE_CONFLICT"
    if isinstance(error, SaveNotFoundError):
        status_code = 404
        code = "SAVE_NOT_FOUND"
    elif isinstance(error, SaveIntegrityError):
        code = "SAVE_INTEGRITY_FAILED"
    elif isinstance(error, SaveCompatibilityError):
        code = "SAVE_VERSION_UNSUPPORTED"
    elif isinstance(error, IdempotencyConflictError):
        code = "IDEMPOTENCY_KEY_REUSED"
    elif isinstance(error, RecoveryPointError):
        code = "SAVE_RECOVERY_POINT_REQUIRED"
    elif isinstance(error, SaveActiveCombatError):
        code = "SAVE_ACTIVE_COMBAT"

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": str(error),
                "details": {},
            },
            "meta": {
                "request_id": str(request.state.request_id),
                "timestamp": datetime.now(UTC).isoformat(),
                "api_version": "v1",
            },
        },
    )


async def handle_gameplay_error(request: Request, exception: Exception) -> JSONResponse:
    """Return stable API errors for deterministic gameplay rejections."""
    if not isinstance(exception, GameplayError):
        raise exception
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exception.code,
                "message": str(exception),
                "details": {},
            },
            "meta": {
                "request_id": str(request.state.request_id),
                "timestamp": datetime.now(UTC).isoformat(),
                "api_version": "v1",
            },
        },
    )


async def handle_world_error(request: Request, exception: Exception) -> JSONResponse:
    """Return stable API errors for deterministic world rejections."""
    if not isinstance(exception, WorldError):
        raise exception
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exception.code,
                "message": str(exception),
                "details": {},
            },
            "meta": {
                "request_id": str(request.state.request_id),
                "timestamp": datetime.now(UTC).isoformat(),
                "api_version": "v1",
            },
        },
    )


async def handle_narrative_error(
    request: Request, exception: Exception
) -> JSONResponse:
    """Return stable errors without leaking provider or context details."""
    if not isinstance(exception, NarrativeError):
        raise exception
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exception.code,
                "message": str(exception),
                "details": {},
            },
            "meta": {
                "request_id": str(request.state.request_id),
                "timestamp": datetime.now(UTC).isoformat(),
                "api_version": "v1",
            },
        },
    )


def create_app() -> FastAPI:
    """Create the API with persistence and narrative provider infrastructure."""
    settings = get_settings()
    configure_logging(settings)

    application = FastAPI(
        title="Yggdrasil Chronicles API",
        version="0.8.0",
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    application.add_middleware(RequestIdMiddleware, settings=settings)
    application.add_exception_handler(SaveError, handle_save_error)
    application.add_exception_handler(GameplayError, handle_gameplay_error)
    application.add_exception_handler(WorldError, handle_world_error)
    application.add_exception_handler(NarrativeError, handle_narrative_error)
    application.include_router(health_router)
    application.include_router(combat_router, prefix="/api/v1")
    application.include_router(gameplay_router, prefix="/api/v1")
    application.include_router(save_router, prefix="/api/v1")
    application.include_router(world_router, prefix="/api/v1")
    application.include_router(narrative_router, prefix="/api/v1")
    return application


app = create_app()
