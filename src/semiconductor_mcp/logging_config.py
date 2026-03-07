"""Structured JSON logging for semiconductor-mcp.

All modules should use:
    import logging
    logger = logging.getLogger(__name__)

Call setup_logging() once at server startup. All log output will be JSON
lines on stdout/stderr, suitable for Railway's log aggregation.
"""

import json
import logging
import time
from typing import Any

_SKIP_ATTRS = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "id", "levelname", "levelno", "lineno", "module",
    "msecs", "message", "msg", "name", "pathname", "process",
    "processName", "relativeCreated", "stack_info", "thread", "threadName",
})


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Attach extra fields passed via the `extra=` kwarg
        for key, val in record.__dict__.items():
            if key not in _SKIP_ATTRS and not key.startswith("_"):
                log[key] = val
        if record.exc_info:
            log["exc"] = self.formatException(record.exc_info)
        return json.dumps(log, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with structured JSON output. Call once at startup."""
    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Reduce noise from third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
