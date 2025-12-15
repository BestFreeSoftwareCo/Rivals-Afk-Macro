import os
import sys
import tkinter as tk

import ctypes

from .autoit_bridge import AutoItBridge
from .config_manager import ConfigManager
from .error_handler import ErrorHandler
from .hotkeys import HotkeyManager
from .logger import setup_logger
from .movement import MacroEngine
from .picker import Picker
from .ui_dark import AppUIDark


def _enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return

    try:
        # Prefer Per-Monitor v2. If this succeeds, do not fall back to older APIs.
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass

    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def main() -> None:
    _enable_dpi_awareness()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    config_path = os.path.join(base_dir, "config", "config.ini")
    log_path = os.path.join(base_dir, "logs", "debug.log")
    runner_path = os.path.join(base_dir, "autoit", "runner.au3")

    config = ConfigManager(config_path)
    config.load()

    logger = setup_logger(log_path, config.get("Debug", "Level", "INFO"))

    root = tk.Tk()

    try:
        dpi = float(root.winfo_fpixels("1i"))
        scaling = max(1.0, min(3.0, dpi / 72.0))
        root.tk.call("tk", "scaling", scaling)
    except Exception:
        pass

    error_handler = ErrorHandler(logger)

    autoit = AutoItBridge(runner_path, logger, error_handler)
    picker = Picker(config, autoit, logger, error_handler)

    macro = MacroEngine(config, autoit, logger, error_handler)

    hotkeys = HotkeyManager(config, logger, error_handler, schedule_ui=lambda fn: root.after(0, fn))

    ui = AppUIDark(
        root=root,
        config=config,
        logger=logger,
        error_handler=error_handler,
        macro_engine=macro,
        picker=picker,
        hotkeys=hotkeys,
    )

    error_handler.set_on_error(ui.set_error)

    root.mainloop()


if __name__ == "__main__":
    main()
