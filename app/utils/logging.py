import json
import logging
import sys
from typing import Any, Dict

from app.config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    formatter = JSONFormatter()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aio_pika").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "extra_fields": {
                "log_level": settings.log_level,
                "service": "image-processing"
            }
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
