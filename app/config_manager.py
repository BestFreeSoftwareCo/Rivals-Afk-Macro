from __future__ import annotations

from configparser import ConfigParser
import shutil
from datetime import datetime
from pathlib import Path
from threading import RLock


class ConfigManager:
    def __init__(self, path: Path):
        self.path = path
        self._lock = RLock()
        self._config = ConfigParser()
        self.load()

    def load(self) -> None:
        with self._lock:
            self._config.read(self.path, encoding="utf-8")

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as f:
                self._config.write(f)

    def has_option(self, section: str, option: str) -> bool:
        with self._lock:
            return self._config.has_option(section, option)

    def ensure_section(self, section: str) -> None:
        if not self._config.has_section(section):
            self._config.add_section(section)

    def get(self, section: str, option: str, fallback: str | None = None) -> str:
        with self._lock:
            return self._config.get(section, option, fallback=fallback)

    def getint(self, section: str, option: str, fallback: int = 0) -> int:
        with self._lock:
            return self._config.getint(section, option, fallback=fallback)

    def getfloat(self, section: str, option: str, fallback: float = 0.0) -> float:
        with self._lock:
            return self._config.getfloat(section, option, fallback=fallback)

    def getboolean(self, section: str, option: str, fallback: bool = False) -> bool:
        with self._lock:
            return self._config.getboolean(section, option, fallback=fallback)

    def set(self, section: str, option: str, value: object) -> None:
        with self._lock:
            self.ensure_section(section)
            self._config.set(section, option, str(value))
            self.save()

    def reset_to_defaults(self) -> None:
        with self._lock:
            try:
                if self.path.exists():
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup = self.path.with_suffix(self.path.suffix + f".bak.{ts}")
                    shutil.copy2(self.path, backup)
            except Exception:
                pass

            self._config = ConfigParser()

            def _set(section: str, option: str, value: object) -> None:
                if not self._config.has_section(section):
                    self._config.add_section(section)
                self._config.set(section, option, str(value))

            _set("Location", "ClickX", 0)
            _set("Location", "ClickY", 0)

            _set("Hotkeys", "Start", "F6")
            _set("Hotkeys", "Stop", "F7")
            _set("Hotkeys", "ConfirmLocation", "F8")

            _set("Movement", "Radius", 25)
            _set("Movement", "SpinSpeed", 10)
            _set("Movement", "MoveSpeed", 10)
            _set("Movement", "StepDelayMs", 20)
            _set("Movement", "Clockwise", 1)

            _set("Clicking", "CenterClickEveryRotations", 1)
            _set("Clicking", "BeforeClickDelayMs", 0)
            _set("Clicking", "AfterClickDelayMs", 0)

            _set("Loops", "LoopCount", 0)
            _set("Loops", "PerLoopDelayMs", 0)
            _set("Loops", "PostLoopKeyEnabled", 0)
            _set("Loops", "PostLoopKey", "SPACE")

            _set("UI", "LastTab", 0)
            _set("UI", "Geometry", "900x692+477+142")

            _set("Debug", "Level", "INFO")
            self.save()
