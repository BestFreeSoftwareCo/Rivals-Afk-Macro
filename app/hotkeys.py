from collections.abc import Callable
from typing import Any

try:
    import keyboard as _keyboard

    _keyboard_import_error: BaseException | None = None
except Exception as exc:
    _keyboard = None
    _keyboard_import_error = exc


class HotkeyManager:
    def __init__(
        self,
        config: Any,
        logger: Any,
        error_handler: Any | None = None,
        schedule_ui: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self._config = config
        self._logger = logger
        self._error_handler = error_handler
        self._schedule_ui = schedule_ui

        self._active = False

        self._hotkey_ids: list[int] = []
        self._on_start: Callable[[], None] | None = None
        self._on_stop: Callable[[], None] | None = None
        self._on_confirm: Callable[[], None] | None = None
        self._on_esc: Callable[[], None] | None = None

    def set_callbacks(
        self,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
        on_confirm: Callable[[], None],
        on_esc: Callable[[], None],
    ) -> None:
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_confirm = on_confirm
        self._on_esc = on_esc

    def start(self) -> None:
        self._active = True
        self.reload()

    def stop(self) -> None:
        self._active = False
        self._unregister_all()

    def reload(self) -> None:
        self._unregister_all()

        if not self._active:
            return

        if _keyboard is None:
            msg = "Global hotkeys are unavailable (keyboard module failed to load)."
            try:
                self._logger.error("%s error=%s", msg, _keyboard_import_error)
            except Exception:
                pass
            if self._error_handler and _keyboard_import_error is not None:
                self._error_handler.report(msg, _keyboard_import_error)
            return

        start_hk = self._config.get("Hotkeys", "Start", "F6")
        stop_hk = self._config.get("Hotkeys", "Stop", "F7")
        confirm_hk = self._config.get("Hotkeys", "ConfirmLocation", "F8")

        self._logger.info("Registering hotkeys start=%s stop=%s confirm=%s", start_hk, stop_hk, confirm_hk)

        self._register_hotkey(start_hk, self._on_start)
        self._register_hotkey(stop_hk, self._on_stop)
        self._register_hotkey(confirm_hk, self._on_confirm)
        self._register_hotkey("esc", self._on_esc)

    def _register_hotkey(self, hotkey: str, callback: Callable[[], None] | None) -> None:
        if not hotkey or not callback:
            return

        if _keyboard is None:
            return

        try:
            hk = str(hotkey).strip().lower()

            def wrapped():
                if not self._active:
                    return

                def run_cb():
                    if not self._active:
                        return
                    try:
                        callback()
                    except Exception as exc:
                        if self._error_handler:
                            self._error_handler.report(f"Hotkey callback failed ({hotkey})", exc)

                if self._schedule_ui:
                    try:
                        self._schedule_ui(run_cb)
                    except Exception as exc:
                        if self._error_handler:
                            self._error_handler.report("Hotkey schedule_ui failed", exc)
                else:
                    run_cb()

            hk_id = _keyboard.add_hotkey(hk, wrapped, suppress=False, trigger_on_release=False)
            self._hotkey_ids.append(hk_id)
        except Exception as exc:
            if self._error_handler:
                self._error_handler.report(f"Hotkey register failed ({hotkey})", exc)
            else:
                raise

    def _unregister_all(self) -> None:
        if _keyboard is None:
            self._hotkey_ids = []
            return
        for hk_id in self._hotkey_ids:
            try:
                _keyboard.remove_hotkey(hk_id)
            except Exception:
                pass
        self._hotkey_ids = []
