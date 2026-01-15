import logging
from typing import Any, Dict

DEFAULT_LOG_LEVEL = logging.DEBUG
EXTRA_CONTEXT_ATTR = "extra_context"
LOG_FORMAT = f"%(asctime)s - %(name)s - %(levelname)s - %(message)s%({EXTRA_CONTEXT_ATTR})s"
FAKEREDIS_LOGGER_NAME = "fakeredis"
FAKEREDIS_LOG_LEVEL = logging.WARNING
DOCKET_WORKER_LOGGER_NAME = "docket.worker"
DOCKET_WORKER_LOG_LEVEL = logging.WARNING

BASE_LOG_RECORD_KEYS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())
BASE_LOG_RECORD_KEYS.update({"message", "asctime", EXTRA_CONTEXT_ATTR})


def format_extra_context(extra_fields: Dict[str, Any]) -> str:
    if not extra_fields:
        return ""
    parts = [f"{key}={value}" for key, value in sorted(extra_fields.items())]
    return " " + " ".join(parts)


class ExtraContextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in BASE_LOG_RECORD_KEYS
        }
        setattr(record, EXTRA_CONTEXT_ATTR, format_extra_context(extra_fields))
        return super().format(record)


def configure_logging(level: int = DEFAULT_LOG_LEVEL) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(ExtraContextFormatter(LOG_FORMAT))
    logging.basicConfig(level=level, handlers=[handler])
    fakeredis_logger = logging.getLogger(FAKEREDIS_LOGGER_NAME)
    fakeredis_logger.setLevel(FAKEREDIS_LOG_LEVEL)
    fakeredis_logger.propagate = False
    docket_worker_logger = logging.getLogger(DOCKET_WORKER_LOGGER_NAME)
    docket_worker_logger.setLevel(DOCKET_WORKER_LOG_LEVEL)
    docket_worker_logger.propagate = False
