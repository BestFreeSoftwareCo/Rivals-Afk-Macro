import math
import threading
import time

from collections.abc import Callable
from typing import Any

from .actions import ActionRunner


class MacroEngine:
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

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running_lock = threading.Lock()
        self._actions = ActionRunner(config, autoit, logger, error_handler)

    @property
    def is_running(self) -> bool:
        t = self._thread
        return t is not None and t.is_alive()

    def start(self) -> None:
        with self._running_lock:
            if self.is_running:
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, name="MacroEngine", daemon=True)
            self._thread.start()

    def stop(self, wait: bool = False, timeout: float = 2.0) -> None:
        self._stop_event.set()
        if not wait:
            return

        t = self._thread
        if t is None:
            return
        try:
            t.join(timeout=timeout)
        except Exception:
            pass

    def _sleep_ms(self, ms: int) -> bool:
        if ms <= 0:
            return True
        return not self._stop_event.wait(ms / 1000.0)

    def _set_status(self, status: str) -> None:
        if self._on_status:
            try:
                self._on_status(status)
            except Exception:
                pass

    def _run(self) -> None:
        try:
            self._set_status("Running")
            self._logger.info("Macro started")

            center_x = self._config.get_int("Click", "ClickX", 0)
            center_y = self._config.get_int("Click", "ClickY", 0)
            if center_x == 0 and center_y == 0:
                self._logger.warning("No click position set")
                self._set_status("Idle")
                return

            rotations_done = 0
            last_center_click = 0.0

            while not self._stop_event.is_set():
                loop_count = self._config.get_int("Loops", "Count", 0)
                if loop_count > 0 and rotations_done >= loop_count:
                    break

                radius = self._config.get_int("Movement", "Radius", 25)
                spin_step_deg = max(1, self._config.get_int("Movement", "SpinStepDeg", 15))
                move_speed = max(0, self._config.get_int("Movement", "MoveSpeed", 10))
                direction = self._config.get("Movement", "Direction", "clockwise").strip().lower()

                step_delay_ms = max(0, self._config.get_int("Delays", "StepDelayMs", 20))
                before_click_ms = max(0, self._config.get_int("Delays", "BeforeClickMs", 0))
                after_click_ms = max(0, self._config.get_int("Delays", "AfterClickMs", 0))
                per_loop_delay_ms = max(0, self._config.get_int("Delays", "PerLoopDelayMs", 0))

                click_button = self._config.get("Click", "ClickButton", "left")
                click_count = max(1, self._config.get_int("Click", "ClickCount", 1))
                click_speed = max(0, self._config.get_int("Click", "ClickSpeed", 0))

                click_every_rot = max(0, self._config.get_int("Click", "CenterClickEveryRotations", 1))
                click_every_ms = max(0, self._config.get_int("Click", "CenterClickEveryMs", 0))

                step_sign = -1 if direction == "counter-clockwise" else 1

                angle = 0
                while (angle < 360 if step_sign == 1 else angle > -360) and not self._stop_event.is_set():
                    radians = math.radians(angle)
                    x = int(center_x + math.cos(radians) * radius)
                    y = int(center_y + math.sin(radians) * radius)

                    self._logger.trace("Circle step angle=%s radius=%s pos=(%s,%s)", angle, radius, x, y)
                    self._autoit.move(x, y, move_speed)

                    now = time.monotonic()
                    should_click = False
                    if click_every_ms > 0 and (now - last_center_click) * 1000.0 >= click_every_ms:
                        should_click = True
                    if click_every_rot > 0 and angle == 0 and ((rotations_done + 1) % click_every_rot) == 0:
                        should_click = True

                    if should_click:
                        if before_click_ms and not self._sleep_ms(before_click_ms):
                            break
                        self._logger.action("Click center at (%s,%s)", center_x, center_y)
                        self._autoit.click(click_button, center_x, center_y, clicks=click_count, speed=click_speed)
                        last_center_click = now
                        if after_click_ms and not self._sleep_ms(after_click_ms):
                            break

                    if step_delay_ms and not self._sleep_ms(step_delay_ms):
                        break

                    angle += (spin_step_deg * step_sign)

                if self._stop_event.is_set():
                    break

                rotations_done += 1
                self._actions.run_post_loop_action()

                if per_loop_delay_ms and not self._sleep_ms(per_loop_delay_ms):
                    break

            self._logger.info("Macro stopped")
        except Exception as exc:
            if self._error_handler:
                self._error_handler.report("MacroEngine", exc)
            else:
                raise
        finally:
            self._set_status("Idle")
            self._thread = None
