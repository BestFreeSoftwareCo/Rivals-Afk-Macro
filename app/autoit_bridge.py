from __future__ import annotations

import logging
import os
import queue
import shutil
import subprocess
import threading
from pathlib import Path


class AutoItBridgeError(RuntimeError):
    pass


class AutoItBridge:
    def __init__(self, runner_script_path: Path, logger: logging.Logger | None = None):
        self.runner_script_path = runner_script_path
        self._logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._proc: subprocess.Popen[str] | None = None
        self._responses: queue.Queue[str] = queue.Queue()
        self._stdout_thread: threading.Thread | None = None
        self._stderr_thread: threading.Thread | None = None

    def _find_autoit_exe(self) -> Path:
        candidates: list[Path] = []

        from_path = shutil.which("AutoIt3.exe")
        if from_path:
            candidates.append(Path(from_path))

        candidates.extend(
            [
                Path(r"C:\Program Files (x86)\AutoIt3\AutoIt3.exe"),
                Path(r"C:\Program Files\AutoIt3\AutoIt3.exe"),
            ]
        )

        for p in candidates:
            if p.exists():
                return p

        raise AutoItBridgeError("AutoIt3.exe not found. Install AutoIt v3 or add it to PATH.")

    def _read_stdout(self) -> None:
        proc = self._proc
        if not proc or not proc.stdout:
            return

        while True:
            line = proc.stdout.readline()
            if line == "" and proc.poll() is not None:
                break

            line = line.strip()
            if line:
                self._responses.put(line)

    def _read_stderr(self) -> None:
        proc = self._proc
        if not proc or not proc.stderr:
            return

        while True:
            line = proc.stderr.readline()
            if line == "" and proc.poll() is not None:
                break

            line = line.strip()
            if line:
                self._logger.warning("AutoIt STDERR: %s", line)

    def _start_locked(self) -> None:
        if self._proc and self._proc.poll() is None:
            return

        if not self.runner_script_path.exists():
            raise AutoItBridgeError(f"Runner script missing: {self.runner_script_path}")

        autoit_exe = self._find_autoit_exe()

        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW

        self._responses = queue.Queue()
        self._proc = subprocess.Popen(
            [str(autoit_exe), str(self.runner_script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=creationflags,
        )

        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stdout_thread.start()

        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stderr_thread.start()

        self.send("PING", timeout=2.0)

    def start(self) -> None:
        with self._lock:
            self._start_locked()

    def stop(self) -> None:
        with self._lock:
            proc = self._proc
            self._proc = None

        if proc and proc.poll() is None:
            try:
                if proc.stdin:
                    proc.stdin.write("EXIT\n")
                    proc.stdin.flush()
            except Exception:
                pass

            try:
                proc.terminate()
            except Exception:
                pass

    def _restart_locked(self) -> None:
        self.stop()
        self._start_locked()

    def send(self, command: str, *args: object, timeout: float = 2.0) -> str:
        with self._lock:
            last_error: Exception | None = None

            for attempt in range(2):
                try:
                    self._start_locked()

                    proc = self._proc
                    if not proc or proc.poll() is not None or not proc.stdin:
                        raise AutoItBridgeError("AutoIt process not running")

                    line = "|".join([command] + [str(a) for a in args])
                    self._logger.trace("AutoIt -> %s", line)
                    proc.stdin.write(line + "\n")
                    proc.stdin.flush()

                    try:
                        response = self._responses.get(timeout=timeout)
                    except queue.Empty as e:
                        raise AutoItBridgeError(f"AutoIt timeout waiting for response to {command}") from e

                    self._logger.trace("AutoIt <- %s", response)
                    if response.startswith("ERR"):
                        raise AutoItBridgeError(response)

                    return response
                except Exception as e:
                    last_error = e
                    if attempt == 0:
                        self._logger.warning("AutoIt bridge error, restarting: %s", e)
                        try:
                            self._restart_locked()
                            continue
                        except Exception:
                            break

            raise AutoItBridgeError(str(last_error) if last_error else "AutoIt bridge error")

    def mouse_move(self, x: int, y: int, speed: int) -> None:
        self.send("MOVE", int(x), int(y), int(speed))

    def mouse_click(
        self,
        x: int,
        y: int,
        button: str = "left",
        clicks: int = 1,
        speed: int = 0,
    ) -> None:
        self.send("CLICK", int(x), int(y), button, int(clicks), int(speed))

    def send_key(self, send_text: str) -> None:
        self.send("KEY", send_text)
