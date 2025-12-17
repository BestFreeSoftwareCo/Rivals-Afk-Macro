from __future__ import annotations

import logging
import traceback
from collections.abc import Callable
from threading import RLock


class ErrorManager:
    def __init__(
        self,
        logger: logging.Logger,
        on_status: Callable[[str], None] | None = None,
    ):
        self._logger = logger
        self._on_status = on_status
        self._lock = RLock()
        self._last_error = ""

    @property
    def last_error(self) -> str:
        with self._lock:
            return self._last_error

    def clear(self) -> None:
        with self._lock:
            self._last_error = ""

        if self._on_status:
            self._on_status("")

    def report(self, message: str, exc: BaseException | None = None, critical: bool = False) -> None:
        with self._lock:
            details = message
            if exc is not None:
                details = f"{message}: {exc}"
            self._last_error = details

        if exc is not None:
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            if critical:
                self._logger.error(details)
                self._logger.error(tb)
            else:
                self._logger.warning(details)
                self._logger.warning(tb)
        else:
            if critical:
                self._logger.error(details)
            else:
                self._logger.warning(details)

        if self._on_status:
            self._on_status(details)
