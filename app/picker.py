from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes
from collections.abc import Callable


class _POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def get_cursor_pos() -> tuple[int, int]:
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


class LocationPicker:
    def __init__(
        self,
        logger: logging.Logger,
        on_confirm: Callable[[int, int], None],
        on_cancel: Callable[[], None],
    ):
        self._logger = logger
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self.active = False

    def enter(self) -> None:
        self.active = True
        self._logger.trace("PickMode ACTIVE")

    def confirm(self) -> None:
        if not self.active:
            return

        x, y = get_cursor_pos()
        self.active = False
        self._logger.info("Location confirmed at (%s, %s)", x, y)
        self._on_confirm(x, y)

    def cancel(self) -> None:
        if not self.active:
            return

        self.active = False
        self._logger.info("PickMode CANCELLED")
        self._on_cancel()
