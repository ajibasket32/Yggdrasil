import json
import logging
import os
from datetime import UTC, datetime

import structlog.contextvars


class JsonLogFormatter(logging.Formatter):
    """Render standard-library and Uvicorn records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if message.startswith("{"):
            try:
                json.loads(message)
            except json.JSONDecodeError:
                pass
            else:
                return message

        context = structlog.contextvars.get_contextvars()
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "service": context.get("service", "yggdrasil-backend"),
            "environment": context.get("environment", os.getenv("ENVIRONMENT", "development")),
            "request_id": context.get("request_id"),
            "event_name": f"{record.name}.log",
            "message": message,
        }
        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))
