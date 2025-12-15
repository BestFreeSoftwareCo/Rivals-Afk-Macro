import configparser
import logging
import os
import threading

from typing import Any


class ConfigManager:
    def __init__(self, path: str):
        self._path = path
        self._lock = threading.Lock()
        self._cfg = configparser.ConfigParser()
        self._cfg.optionxform = str

    @property
    def path(self) -> str:
        return self._path

    def load(self) -> None:
        try:
            with self._lock:
                self._cfg.read(self._path, encoding="utf-8")
        except Exception:
            logging.getLogger(__name__).exception("Failed to load config: %s", self._path)

    def save(self) -> None:
        try:
            dir_path = os.path.dirname(self._path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with self._lock:
                with open(self._path, "w", encoding="utf-8") as f:
                    self._cfg.write(f)
        except Exception:
            logging.getLogger(__name__).exception("Failed to save config: %s", self._path)

    def ensure_section(self, section: str) -> None:
        with self._lock:
            if not self._cfg.has_section(section):
                self._cfg.add_section(section)

    def get(self, section: str, option: str, fallback: str = "") -> str:
        with self._lock:
            if not self._cfg.has_section(section):
                return fallback
            return self._cfg.get(section, option, fallback=fallback)

    def get_int(self, section: str, option: str, fallback: int = 0) -> int:
        raw = self.get(section, option, str(fallback))
        try:
            return int(str(raw).strip())
        except Exception:
            return fallback

    def get_float(self, section: str, option: str, fallback: float = 0.0) -> float:
        raw = self.get(section, option, str(fallback))
        try:
            return float(str(raw).strip())
        except Exception:
            return fallback

    def set(self, section: str, option: str, value: Any, autosave: bool = True) -> None:
        with self._lock:
            if not self._cfg.has_section(section):
                self._cfg.add_section(section)
            self._cfg.set(section, option, str(value))
        if autosave:
            self.save()
