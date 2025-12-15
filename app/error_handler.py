import traceback

from collections.abc import Callable
from typing import Any


class ErrorHandler:
    def __init__(self, logger: Any, on_error: Callable[[str], None] | None = None) -> None:
        self._logger = logger
        self._on_error = on_error

    def set_on_error(self, on_error: Callable[[str], None] | None) -> None:
        self._on_error = on_error

    def report(self, context: str, exc: BaseException) -> None:
        try:
            self._logger.error("%s: %s", context, exc)
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            self._logger.error(tb)
        except Exception:
            pass

        if self._on_error:
            try:
                self._on_error(f"{context}: {exc}")
            except Exception:
                pass

    def safe_call(self, context: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            self.report(context, exc)
            return None
