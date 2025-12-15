from typing import Any


class ActionRunner:
    def __init__(self, config: Any, autoit: Any, logger: Any, error_handler: Any | None = None) -> None:
        self._config = config
        self._autoit = autoit
        self._logger = logger
        self._error_handler = error_handler

    def run_post_loop_action(self) -> None:
        enabled = self._config.get_int("Actions", "PostLoopEnabled", 0)
        if not enabled:
            return

        key = self._config.get("Actions", "PostLoopKey", "SPACE")
        self._logger.action("Post-loop key press: %s", key)
        self._autoit.send_key(key)
