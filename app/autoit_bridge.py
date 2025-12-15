import os
import subprocess
from typing import Any, Sequence, Tuple


class AutoItBridge:
    def __init__(self, runner_au3_path: str, logger, error_handler=None):
        self._runner_au3_path = runner_au3_path
        self._logger = logger
        self._error_handler = error_handler
        self._init_error: BaseException | None = None
        self._autoit_exe = self._find_autoit_exe()

        if not os.path.isfile(self._runner_au3_path):
            self._init_error = FileNotFoundError(f"AutoIt runner script not found: {self._runner_au3_path}")
            try:
                self._logger.error("%s", self._init_error)
            except Exception:
                pass

    @property
    def is_available(self) -> bool:
        return self._init_error is None

    def _find_autoit_exe(self) -> str:
        env_path = os.environ.get("AUTOIT3_EXE", "").strip()
        if env_path and os.path.isfile(env_path):
            return env_path

        candidates = [
            r"C:\Program Files (x86)\AutoIt3\AutoIt3.exe",
            r"C:\Program Files\AutoIt3\AutoIt3.exe",
            "AutoIt3.exe",
        ]
        for candidate in candidates:
            if candidate == "AutoIt3.exe":
                return candidate
            if os.path.isfile(candidate):
                return candidate

        return "AutoIt3.exe"

    def _run(self, args: Sequence[Any], timeout_seconds: float = 5.0) -> subprocess.CompletedProcess:
        if self._init_error is not None:
            raise RuntimeError(str(self._init_error))
        cmd = [self._autoit_exe, self._runner_au3_path, *[str(a) for a in args]]
        self._logger.trace("AutoIt cmd=%s", cmd)
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "AutoIt3.exe was not found. Install AutoIt v3 or set AUTOIT3_EXE to the full path of AutoIt3.exe."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"AutoIt timed out after {timeout_seconds:.1f}s while running: {' '.join(str(x) for x in cmd)}"
            ) from exc

    def _raise_for_result(self, action: str, result: subprocess.CompletedProcess) -> None:
        if result.returncode == 0:
            return

        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        details = (err or out or "").strip()
        if not details:
            details = f"AutoIt returned code {result.returncode}"
        raise RuntimeError(f"AutoIt {action} failed: {details}")

    def move(self, x: int, y: int, speed: int) -> None:
        result = self._run(["move", int(x), int(y), int(speed)])
        self._raise_for_result("move", result)

    def click(self, button: str, x: int, y: int, clicks: int = 1, speed: int = 0) -> None:
        result = self._run(["click", button, int(x), int(y), int(clicks), int(speed)])
        self._raise_for_result("click", result)

    def get_mouse_pos(self) -> Tuple[int, int]:
        result = self._run(["getpos"])
        self._raise_for_result("getpos", result)
        raw = (result.stdout or "").strip()
        parts = raw.split(",")
        if len(parts) != 2:
            raise RuntimeError(f"Unexpected AutoIt getpos output: {raw}")
        return int(parts[0]), int(parts[1])

    def send_key(self, key_name: str):
        send_str = self._key_to_send_string(key_name)
        result = self._run(["send", send_str])
        self._raise_for_result("send", result)

    def _key_to_send_string(self, key_name: str) -> str:
        k = (key_name or "").strip().upper()
        if not k:
            return ""

        if len(k) == 1 and (k.isalpha() or k.isdigit()):
            return k

        if k.startswith("F") and k[1:].isdigit():
            return "{" + k + "}"

        mapping = {
            "SPACE": "{SPACE}",
            "ENTER": "{ENTER}",
            "RETURN": "{ENTER}",
            "TAB": "{TAB}",
            "ESC": "{ESC}",
            "ESCAPE": "{ESC}",
            "UP": "{UP}",
            "DOWN": "{DOWN}",
            "LEFT": "{LEFT}",
            "RIGHT": "{RIGHT}",
        }
        if k in mapping:
            return mapping[k]

        if k in ("SHIFT", "CTRL", "CONTROL", "ALT"):
            if k == "SHIFT":
                return "{SHIFTDOWN}{SHIFTUP}"
            if k in ("CTRL", "CONTROL"):
                return "{CTRLDOWN}{CTRLUP}"
            if k == "ALT":
                return "{ALTDOWN}{ALTUP}"

        return "{" + k + "}"
