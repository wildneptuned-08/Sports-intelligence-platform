from __future__ import annotations

import logging
import sys
from typing import Any

import orjson


class JSONFormatter(logging.Formatter):
    """Emits structured JSON log lines — one JSON object per line."""

    EXCLUDED_FIELDS = frozenset({
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "message", "module",
        "msecs", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName",
    })

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include any extra= fields the caller passed
        for key, value in record.__dict__.items():
            if key not in self.EXCLUDED_FIELDS:
                log_data[key] = value

        return orjson.dumps(log_data).decode()


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger with JSON output. Call once at startup."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    # Silence noisy third-party loggers unless DEBUG is requested
    if level > logging.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
