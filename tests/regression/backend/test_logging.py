import json
import logging

from app.core.uvicorn_logging import JsonLogFormatter


def test_standard_log_record_is_rendered_as_required_json() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="uvicorn.error",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Application startup complete",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "info"
    assert payload["service"] == "yggdrasil-backend"
    assert payload["environment"] == "development"
    assert payload["event_name"] == "uvicorn.error.log"
    assert payload["message"] == "Application startup complete"
    assert "request_id" in payload
