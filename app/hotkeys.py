from __future__ import annotations

import logging
import threading
from collections.abc import Callable

try:
    import keyboard
except Exception as e:
    raise RuntimeError(
        "The 'keyboard' package is required. Install it with: pip install keyboard"
    ) from e


def normalize_hotkey(hotkey: str) -> str:
    return hotkey.strip().lower()


HOTKEY_CHOICES: list[str] = (
    [f"F{i}" for i in range(1, 13)]
    + [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    + [str(i) for i in range(0, 10)]
    + ["SPACE", "ENTER", "ESC"]
)


class HotkeyManager:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._lock = threading.RLock()
        self._handles: dict[str, int] = {}

    def register(self, name: str, hotkey: str, callback: Callable[[], None]) -> None:
        with self._lock:
            self.unregister(name)
            hk = normalize_hotkey(hotkey)
            handle = keyboard.add_hotkey(hk, callback)
            self._handles[name] = handle
            self._logger.info("Hotkey %s registered: %s", name, hotkey)

    def unregister(self, name: str) -> None:
        with self._lock:
            handle = self._handles.pop(name, None)
            if handle is not None:
                try:
                    keyboard.remove_hotkey(handle)
                except Exception:
                    pass

    def shutdown(self) -> None:
        with self._lock:
            for handle in list(self._handles.values()):
                try:
                    keyboard.remove_hotkey(handle)
                except Exception:
                    pass
            self._handles.clear()
