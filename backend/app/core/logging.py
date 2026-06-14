import logging
from typing import cast

import structlog
from structlog.typing import FilteringBoundLogger

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure structured JSON logs for application and access events."""
    log_level = logging.getLevelNamesMapping().get(
        settings.log_level.upper(), logging.INFO
    )
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger() -> FilteringBoundLogger:
    """Return the configured structured logger."""
    return cast(FilteringBoundLogger, structlog.get_logger())
