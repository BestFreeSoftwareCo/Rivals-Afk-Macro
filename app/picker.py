from collections.abc import Callable
from typing import Any


class Picker:
    def __init__(
        self,
        config: Any,
        autoit: Any,
        logger: Any,
        error_handler: Any | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        self._config = config
        self._autoit = autoit
        self._logger = logger
        self._error_handler = error_handler
        self._on_status = on_status

        self._active = False
        self._on_picked = None
        self._on_cancelled = None
        self._on_hide_ui = None
        self._on_show_ui = None

    @property
    def is_active(self) -> bool:
        return self._active

    def begin(
        self,
        on_picked: Callable[[int, int], None],
        on_cancelled: Callable[[], None],
        on_hide_ui: Callable[[], None] | None = None,
        on_show_ui: Callable[[], None] | None = None,
    ) -> None:
        if self._active:
            return
        self._active = True
        self._on_picked = on_picked
        self._on_cancelled = on_cancelled
        self._on_hide_ui = on_hide_ui
        self._on_show_ui = on_show_ui

        try:
            self._logger.info("PickMode ACTIVE")
            if self._on_status:
                self._on_status("Picking Location")
            if self._on_hide_ui:
                self._on_hide_ui()
        except Exception as exc:
            if self._error_handler:
                self._error_handler.report("Picker.begin", exc)
            else:
                raise
            self._end(restore_ui=True)

    def confirm(self) -> None:
        if not self._active:
            return
        try:
            x, y = self._autoit.get_mouse_pos()
            self._config.set("Click", "ClickX", x)
            self._config.set("Click", "ClickY", y)

            self._logger.info("Location confirmed at (%s, %s)", x, y)

            if self._on_picked:
                self._on_picked(x, y)
        except Exception as exc:
            if self._error_handler:
                self._error_handler.report("Picker.confirm", exc)
            else:
                raise
        finally:
            self._end(restore_ui=True)

    def cancel(self) -> None:
        if not self._active:
            return
        self._logger.info("PickMode CANCELLED")
        try:
            if self._on_cancelled:
                self._on_cancelled()
        finally:
            self._end(restore_ui=True)

    def _end(self, restore_ui: bool) -> None:
        self._active = False

        on_show = self._on_show_ui
        on_status = self._on_status
        self._on_picked = None
        self._on_cancelled = None
        self._on_hide_ui = None
        self._on_show_ui = None

        if restore_ui and on_show:
            try:
                on_show()
            except Exception:
                pass

        if on_status:
            try:
                on_status("Idle")
            except Exception:
                pass
