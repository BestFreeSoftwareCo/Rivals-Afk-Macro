from __future__ import annotations

import logging
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import webbrowser

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

    ctk_mod = None
    try:
        import customtkinter as ctk

        ctk_mod = ctk
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

    def _is_activated() -> bool:
        try:
            return config.getboolean("License", "Activated", fallback=False)
        except Exception:
            return False

    def _set_activated() -> None:
        try:
            config.set("License", "Activated", 1)
        except Exception:
            pass

    def _require_key_blocking() -> bool:
        discord_url = "https://discord.gg/498tyUUaBw"
        expected_key = "Snoopy's Hangout + Macros"

        try:
            root.withdraw()
        except Exception:
            pass

        ok = {"value": False}

        if ctk_mod is not None:
            win = ctk_mod.CTkToplevel(root)
            win.title("Key Required")
            win.resizable(False, False)

            frame = ctk_mod.CTkFrame(win, corner_radius=16)
            frame.pack(fill="both", expand=True, padx=16, pady=16)

            ctk_mod.CTkLabel(
                frame,
                text="You need a key to use this macro.\nJoin the Discord server to get a key.",
                justify="left",
            ).pack(anchor="w", pady=(0, 12))

            def _join() -> None:
                try:
                    webbrowser.open(discord_url)
                except Exception:
                    pass

            ctk_mod.CTkButton(frame, text="Join Discord Server", command=_join, corner_radius=14).pack(
                anchor="w", pady=(0, 12)
            )

            key_var = tk.StringVar()
            entry = ctk_mod.CTkEntry(frame, textvariable=key_var, corner_radius=10, width=340)
            entry.pack(anchor="w", pady=(0, 12))

            err = tk.StringVar(value="")
            err_lbl = ctk_mod.CTkLabel(frame, textvariable=err, text_color="#EF4444")
            err_lbl.pack(anchor="w", pady=(0, 12))

            btn_row = ctk_mod.CTkFrame(frame, fg_color="transparent")
            btn_row.pack(fill="x")

            def _submit() -> None:
                entered = key_var.get().strip()
                if entered != expected_key:
                    err.set("Invalid key.")
                    return
                ok["value"] = True
                _set_activated()
                try:
                    win.destroy()
                except Exception:
                    pass

            def _quit() -> None:
                ok["value"] = False
                try:
                    win.destroy()
                except Exception:
                    pass

            def _on_close() -> None:
                _quit()

            ctk_mod.CTkButton(btn_row, text="Submit", command=_submit, corner_radius=14).pack(
                side="left"
            )
            ctk_mod.CTkButton(
                btn_row,
                text="Quit",
                command=_quit,
                corner_radius=14,
                fg_color="#111827",
                hover_color="#1F2937",
            ).pack(side="left", padx=(10, 0))

            try:
                win.protocol("WM_DELETE_WINDOW", _on_close)
                win.grab_set()
                win.focus_force()
                entry.focus_set()
            except Exception:
                pass

            try:
                win.wait_window()
            except Exception:
                pass
        else:
            win = tk.Toplevel(root)
            win.title("Key Required")
            win.resizable(False, False)
            win.configure(bg="#0B1226")

            tk.Label(
                win,
                text="You need a key to use this macro.\nJoin the Discord server to get a key.",
                bg="#0B1226",
                fg="#E5E7EB",
                justify="left",
            ).pack(anchor="w", padx=16, pady=(16, 10))

            def _join() -> None:
                try:
                    webbrowser.open(discord_url)
                except Exception:
                    pass

            tk.Button(win, text="Join Discord Server", command=_join).pack(
                anchor="w", padx=16, pady=(0, 10)
            )

            key_var = tk.StringVar()
            entry = tk.Entry(win, textvariable=key_var, width=46)
            entry.pack(anchor="w", padx=16, pady=(0, 8))

            err = tk.StringVar(value="")
            tk.Label(win, textvariable=err, bg="#0B1226", fg="#EF4444").pack(
                anchor="w", padx=16, pady=(0, 10)
            )

            btn_row = tk.Frame(win, bg="#0B1226")
            btn_row.pack(fill="x", padx=16, pady=(0, 16))

            def _submit() -> None:
                entered = key_var.get().strip()
                if entered != expected_key:
                    err.set("Invalid key.")
                    return
                ok["value"] = True
                _set_activated()
                try:
                    win.destroy()
                except Exception:
                    pass

            def _quit() -> None:
                ok["value"] = False
                try:
                    win.destroy()
                except Exception:
                    pass

            def _on_close() -> None:
                _quit()

            tk.Button(btn_row, text="Submit", command=_submit).pack(side="left")
            tk.Button(btn_row, text="Quit", command=_quit).pack(side="left", padx=(10, 0))

            try:
                win.protocol("WM_DELETE_WINDOW", _on_close)
                win.grab_set()
                win.focus_force()
                entry.focus_set()
                win.wait_window()
            except Exception:
                pass

        return bool(ok["value"])

    error_manager = ErrorManager(logger=logger)
    autoit = AutoItBridge(runner_script_path=runner_path, logger=logger)
    hotkeys = HotkeyManager(logger=logger)

    if not _is_activated():
        if not _require_key_blocking():
            try:
                root.destroy()
            except Exception:
                pass
            return

    def _show_root() -> None:
        try:
            root.deiconify()
        except Exception as e:
            try:
                logger.exception("Failed to deiconify root", exc_info=e)
            except Exception:
                pass
        try:
            root.update_idletasks()
        except Exception:
            pass
        try:
            root.lift()
            root.focus_force()
        except Exception:
            pass
        try:
            root.attributes("-topmost", True)
            root.after(10, lambda: root.attributes("-topmost", False))
        except Exception:
            pass

    try:
        ui = AppUI(
            root=root,
            config=config,
            autoit=autoit,
            hotkeys=hotkeys,
            error_manager=error_manager,
            logger=logger,
        )
    except Exception as e:
        try:
            logger.exception("Failed to initialize UI", exc_info=e)
        except Exception:
            pass
        try:
            messagebox.showerror("Startup Error", f"Failed to initialize UI:\n\n{e}")
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass
        return

    _show_root()
    try:
        root.after(50, _show_root)
    except Exception:
        pass

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
