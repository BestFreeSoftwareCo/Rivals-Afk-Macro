from __future__ import annotations

import logging
from pathlib import Path

ACTION_LEVEL = 25
TRACE_LEVEL = 5

logging.addLevelName(ACTION_LEVEL, "ACTION")
logging.addLevelName(TRACE_LEVEL, "TRACE")


def _action(self: logging.Logger, message: str, *args, **kwargs) -> None:
    if self.isEnabledFor(ACTION_LEVEL):
        self._log(ACTION_LEVEL, message, args, **kwargs)


def _trace(self: logging.Logger, message: str, *args, **kwargs) -> None:
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kwargs)


if not hasattr(logging.Logger, "action"):
    logging.Logger.action = _action  # type: ignore[attr-defined]
if not hasattr(logging.Logger, "trace"):
    logging.Logger.trace = _trace  # type: ignore[attr-defined]


_LEVEL_NAME_TO_VALUE: dict[str, int] = {
    "TRACE": TRACE_LEVEL,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "ACTION": ACTION_LEVEL,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def parse_level(level_name: str) -> int:
    return _LEVEL_NAME_TO_VALUE.get(level_name.strip().upper(), logging.INFO)


def init_logging(log_file_path: Path, level_name: str) -> logging.Logger:
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(TRACE_LEVEL)

    formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    level_value = parse_level(level_name)

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(level_value)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level_value)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.info("Log session start")
    return logger


def set_logging_level(level_name: str) -> None:
    level_value = parse_level(level_name)
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setLevel(level_value)
