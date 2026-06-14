from time import perf_counter
from uuid import UUID, uuid4

import structlog.contextvars
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.metrics import (
    HTTP_ERRORS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach request IDs, structured access logs, and HTTP metrics."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._logger = get_logger()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = self._get_request_id(request)
        request.state.request_id = request_id
        started_at = perf_counter()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            service=self._settings.service_name,
            environment=self._settings.environment,
        )

        response = await call_next(request)
        duration_seconds = perf_counter() - started_at
        path = request.url.path
        status_code = response.status_code
        response.headers[REQUEST_ID_HEADER] = request_id

        HTTP_REQUESTS_TOTAL.labels(request.method, path, str(status_code)).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(request.method, path).observe(
            duration_seconds
        )
        if status_code >= 400:
            HTTP_ERRORS_TOTAL.labels(request.method, path, str(status_code)).inc()

        self._logger.info(
            "HTTP request completed",
            event_name="http.request.completed",
            category="SYSTEM",
            method=request.method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_seconds * 1000, 3),
        )
        structlog.contextvars.clear_contextvars()
        return response

    @staticmethod
    def _get_request_id(request: Request) -> str:
        candidate = request.headers.get(REQUEST_ID_HEADER)
        if candidate is not None:
            try:
                return str(UUID(candidate))
            except ValueError:
                pass
        return str(uuid4())
