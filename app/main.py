from __future__ import annotations

import logging
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

try:
    from .autoit_bridge import AutoItBridge
    from .config_manager import ConfigManager
    from .error_handler import ErrorManager
    from .hotkeys import HotkeyManager
    from .logger import init_logging, parse_level, set_logging_level
    from .ui import AppUI
except ImportError:
    root_dir = Path(__file__).resolve().parents[1]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    from app.autoit_bridge import AutoItBridge
    from app.config_manager import ConfigManager
    from app.error_handler import ErrorManager
    from app.hotkeys import HotkeyManager
    from app.logger import init_logging, parse_level, set_logging_level
    from app.ui import AppUI


def main() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    config_path = root_dir / "config" / "config.ini"
    log_path = root_dir / "logs" / "debug.log"
    runner_path = root_dir / "autoit" / "runner.au3"

    config = ConfigManager(config_path)

    logger = init_logging(log_path, config.get("Debug", "Level", fallback="INFO"))
    set_logging_level(config.get("Debug", "Level", fallback="INFO"))

    try:
        import customtkinter as ctk

        root: tk.Tk = ctk.CTk()
        try:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
        except Exception:
            pass
    except Exception:
        root = tk.Tk()
        try:
            messagebox.showerror(
                "Missing dependency",
                "customtkinter is not installed.\n\nInstall it with:\n  pip install -r requirements.txt",
            )
        except Exception:
            pass
        return

    error_manager = ErrorManager(logger=logger)
    autoit = AutoItBridge(runner_script_path=runner_path, logger=logger)
    hotkeys = HotkeyManager(logger=logger)

    ui = AppUI(
        root=root,
        config=config,
        autoit=autoit,
        hotkeys=hotkeys,
        error_manager=error_manager,
        logger=logger,
    )

    def _on_uncaught(exc: BaseException) -> None:
        error_manager.report("Unhandled exception", exc, critical=True)

    def _report_callback_exception(
        _self: tk.Tk,
        exc: type[BaseException],
        val: BaseException,
        tb: object,
    ) -> None:
        _on_uncaught(val)

    try:
        root.report_callback_exception = _report_callback_exception  # type: ignore[assignment]
    except Exception:
        pass

    root.mainloop()


if __name__ == "__main__":
    main()
