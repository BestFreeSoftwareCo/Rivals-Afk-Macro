import logging
import os
from datetime import datetime
from typing import Any

TRACE_LEVEL_NUM = 5
ACTION_LEVEL_NUM = 25

logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
logging.addLevelName(ACTION_LEVEL_NUM, "ACTION")


def _trace(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kwargs)


def _action(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
    if self.isEnabledFor(ACTION_LEVEL_NUM):
        self._log(ACTION_LEVEL_NUM, message, args, **kwargs)


logging.Logger.trace = _trace
logging.Logger.action = _action


def _level_from_name(name: str) -> int:
    value = (name or "INFO").strip().upper()
    if value == "TRACE":
        return TRACE_LEVEL_NUM
    if value == "ACTION":
        return ACTION_LEVEL_NUM
    if value == "DEBUG":
        return logging.DEBUG
    if value == "INFO":
        return logging.INFO
    if value == "WARNING":
        return logging.WARNING
    if value == "ERROR":
        return logging.ERROR
    return logging.INFO


def set_logger_level(logger: logging.Logger, level_name: str) -> None:
    level_num = _level_from_name(level_name)
    logger.setLevel(level_num)
    for h in logger.handlers:
        try:
            h.setLevel(level_num)
        except Exception:
            pass


def setup_logger(log_file_path: str, level_name: str) -> logging.Logger:
    dir_path = os.path.dirname(log_file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    logger = logging.getLogger("rivals_afk")
    logger.propagate = False

    level_num = _level_from_name(level_name)
    logger.setLevel(level_num)

    for h in list(logger.handlers):
        logger.removeHandler(h)

    handler = logging.FileHandler(log_file_path, encoding="utf-8")
    handler.setLevel(level_num)

    formatter = logging.Formatter("[%(levelname)s] %(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("---- Session start %s ----", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return logger
