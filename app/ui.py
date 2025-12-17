from __future__ import annotations

import logging
import ctypes
import os
import threading
import time
from collections.abc import Callable
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

try:
    import customtkinter as ctk

    _HAS_CTK = True
except Exception:
    ctk = None  # type: ignore[assignment]
    _HAS_CTK = False

from .actions import key_name_to_autoit_send
from .autoit_bridge import AutoItBridge, AutoItBridgeError
from .config_manager import ConfigManager
from .error_handler import ErrorManager
from .hotkeys import HOTKEY_CHOICES, HotkeyManager
from .logger import set_logging_level
from .movement import iter_circle_points
from .picker import LocationPicker, get_cursor_pos


THEME_BG = "#070D1A"
THEME_CARD = "#0B1226"
THEME_BORDER = "#14203B"
THEME_TEXT = "#E5E7EB"
THEME_MUTED = "#94A3B8"
THEME_ACCENT = "#3B82F6"
THEME_ACCENT_DARK = "#2563EB"
THEME_DANGER = "#EF4444"
THEME_DANGER_DARK = "#DC2626"
THEME_SUCCESS = "#22C55E"
THEME_WARNING = "#F59E0B"
THEME_PURPLE = "#A78BFA"


class ToggleSwitch(tk.Canvas):
    def __init__(
        self,
        parent: tk.Misc,
        variable: tk.BooleanVar,
        command: Callable[[], None] | None = None,
        on_color: str = THEME_ACCENT,
        off_color: str = THEME_BORDER,
        width: int = 46,
        height: int = 26,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=THEME_CARD,
            highlightthickness=0,
            cursor="hand2",
            takefocus=1,
        )
        self._variable = variable
        self._command = command
        self._on_color = on_color
        self._off_color = off_color

        self.bind("<Button-1>", self._toggle)
        self.bind("<Return>", self._toggle)
        self.bind("<Key-space>", self._toggle)
        self.bind("<Configure>", lambda _e: self._redraw())
        self._variable.trace_add("write", lambda *_: self._redraw())

        self._redraw()

    def _toggle(self, _event: object | None = None) -> None:
        self._variable.set(not bool(self._variable.get()))
        if self._command:
            self._command()

    def _redraw(self) -> None:
        self.delete("all")

        on = bool(self._variable.get())
        w = int(self["width"])
        h = int(self["height"])
        pad = 2
        r = h - (pad * 2)

        track = self._on_color if on else self._off_color
        thumb = "#FFFFFF"

        self.create_oval(pad, pad, pad + r, pad + r, fill=track, outline=track)
        self.create_oval(w - pad - r, pad, w - pad, pad + r, fill=track, outline=track)
        self.create_rectangle(pad + (r / 2), pad, w - pad - (r / 2), pad + r, fill=track, outline=track)

        x = w - pad - r if on else pad
        self.create_oval(x, pad, x + r, pad + r, fill=thumb, outline=thumb)


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None] | None = None,
        bg: str = THEME_ACCENT,
        fg: str = "#FFFFFF",
        bg_hover: str | None = None,
        bg_disabled: str = THEME_BORDER,
        fg_disabled: str = THEME_MUTED,
        font: tkfont.Font | None = None,
        height: int = 38,
        radius: int = 14,
    ):
        parent_bg = THEME_BG
        try:
            if isinstance(parent, tk.Widget):
                try:
                    parent_bg = str(parent.cget("bg"))
                except Exception:
                    parent_bg = str(parent.cget("background"))
        except Exception:
            parent_bg = THEME_BG
        super().__init__(
            parent,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            cursor="hand2",
            takefocus=1,
        )
        self._text = text
        self._command = command
        self._bg = bg
        self._fg = fg
        self._bg_hover = bg_hover or bg
        self._bg_disabled = bg_disabled
        self._fg_disabled = fg_disabled
        self._font = font
        self._radius = radius
        self._enabled = True
        self._hover = False

        self.bind("<Button-1>", self._on_click)
        self.bind("<Return>", lambda _e: self._invoke())
        self.bind("<space>", lambda _e: self._invoke())
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<Configure>", lambda _e: self._redraw())
        self._redraw()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        self.configure(cursor=("hand2" if self._enabled else "arrow"))
        self._redraw()

    def _set_hover(self, hover: bool) -> None:
        self._hover = bool(hover)
        self._redraw()

    def _on_click(self, _event: tk.Event) -> None:
        self._invoke()

    def _invoke(self) -> None:
        if not self._enabled:
            return
        if self._command is None:
            return
        self._command()

    def _rounded_rect(self, x1: int, y1: int, x2: int, y2: int, r: int, **kw) -> None:
        r = max(0, min(r, int((y2 - y1) / 2), int((x2 - x1) / 2)))
        points = [
            x1 + r,
            y1,
            x2 - r,
            y1,
            x2,
            y1,
            x2,
            y1 + r,
            x2,
            y2 - r,
            x2,
            y2,
            x2 - r,
            y2,
            x1 + r,
            y2,
            x1,
            y2,
            x1,
            y2 - r,
            x1,
            y1 + r,
            x1,
            y1,
        ]
        self.create_polygon(points, smooth=True, splinesteps=12, **kw)

    def _redraw(self) -> None:
        self.delete("all")
        w = max(1, int(self.winfo_width()))
        h = max(1, int(self.winfo_height()))

        bg = self._bg
        fg = self._fg
        if not self._enabled:
            bg = self._bg_disabled
            fg = self._fg_disabled
        elif self._hover:
            bg = self._bg_hover

        self._rounded_rect(0, 0, w, h, self._radius, fill=bg, outline="")
        self.create_text(int(w / 2), int(h / 2), text=self._text, fill=fg, font=self._font)


POST_ACTION_KEY_CHOICES: list[str] = (
    [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    + [str(i) for i in range(0, 10)]
    + [f"F{i}" for i in range(1, 13)]
    + ["SPACE", "ENTER", "SHIFT", "CTRL", "ESC"]
)


class AppUI:
    def __init__(
        self,
        root: tk.Tk,
        config: ConfigManager,
        autoit: AutoItBridge,
        hotkeys: HotkeyManager,
        error_manager: ErrorManager,
        logger: logging.Logger,
    ):
        self.root = root
        self.config = config
        self.autoit = autoit
        self.hotkeys = hotkeys
        self.error_manager = error_manager
        self.logger = logger

        self._macro_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._rotation_counter = 0

        self.status_var = tk.StringVar(value="Idle")
        self.coord_var = tk.StringVar(value="(0, 0)")
        self.error_var = tk.StringVar(value="")

        self.radius_var = tk.IntVar()
        self.spin_speed_var = tk.IntVar()
        self.move_speed_var = tk.IntVar()
        self.step_delay_var = tk.IntVar()
        self.clockwise_var = tk.BooleanVar()

        self.radius_text_var = tk.StringVar()
        self.spin_speed_text_var = tk.StringVar()
        self.move_speed_text_var = tk.StringVar()
        self.step_delay_text_var = tk.StringVar()

        self.center_click_every_var = tk.IntVar()
        self.before_click_delay_var = tk.IntVar()
        self.after_click_delay_var = tk.IntVar()

        self.center_click_every_text_var = tk.StringVar()
        self.before_click_delay_text_var = tk.StringVar()
        self.after_click_delay_text_var = tk.StringVar()

        self.loop_count_var = tk.IntVar()
        self.per_loop_delay_var = tk.IntVar()
        self.post_loop_key_enabled_var = tk.BooleanVar()
        self.post_loop_key_var = tk.StringVar()

        self.loop_count_text_var = tk.StringVar()
        self.per_loop_delay_text_var = tk.StringVar()

        self.start_hotkey_var = tk.StringVar()
        self.stop_hotkey_var = tk.StringVar()
        self.confirm_hotkey_var = tk.StringVar()

        self.debug_level_var = tk.StringVar()

        self._font_title: tkfont.Font | None = None
        self._font_subtitle: tkfont.Font | None = None
        self._font_section: tkfont.Font | None = None
        self._font_badge: tkfont.Font | None = None
        self._font_mono: tkfont.Font | None = None

        self._ctk_font_title: object | None = None
        self._ctk_font_subtitle: object | None = None
        self._ctk_font_section: object | None = None
        self._ctk_font_badge: object | None = None
        self._ctk_font_mono: object | None = None

        self.loop_progress_var = tk.StringVar(value="0")
        self.estimate_var = tk.StringVar(value="-")

        self._pick_cursor_var = tk.StringVar(value="")

        self.notebook: ttk.Notebook | None = None
        self.tabview: object | None = None

        self._header_status_badge: tk.Label | None = None
        self._header_location_badge: tk.Label | None = None
        self._header_progress_badge: tk.Label | None = None
        self._footer_error_label: tk.Label | None = None
        self._footer_hotkeys_label: tk.Label | None = None
        self._pick_overlay: tk.Toplevel | None = None

        self._closing = False
        self._after_chrome_id: str | None = None
        self._after_error_id: str | None = None
        self._after_pick_id: str | None = None

        self._loop_progressbar: ttk.Progressbar | None = None

        self._btn_start: object | None = None
        self._btn_stop: object | None = None
        self._btn_pick: object | None = None

        self.picker = LocationPicker(
            logger=self.logger,
            on_confirm=self._on_location_confirmed,
            on_cancel=self._on_location_cancelled,
        )

        self._load_from_config()
        self._sync_text_vars_from_ints()
        self._bind_text_var_to_int(self.radius_text_var, self.radius_var)
        self._bind_text_var_to_int(self.spin_speed_text_var, self.spin_speed_var)
        self._bind_text_var_to_int(self.move_speed_text_var, self.move_speed_var)
        self._bind_text_var_to_int(self.step_delay_text_var, self.step_delay_var)
        self._bind_text_var_to_int(self.center_click_every_text_var, self.center_click_every_var)
        self._bind_text_var_to_int(self.before_click_delay_text_var, self.before_click_delay_var)
        self._bind_text_var_to_int(self.after_click_delay_text_var, self.after_click_delay_var)
        self._bind_text_var_to_int(self.loop_count_text_var, self.loop_count_var)
        self._bind_text_var_to_int(self.per_loop_delay_text_var, self.per_loop_delay_var)
        self._bind_autosave_vars()

        self._build_ui()
        self._register_hotkeys()

        self.error_manager.clear()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    @property
    def macro_running(self) -> bool:
        t = self._macro_thread
        return t is not None and t.is_alive()

    def _load_from_config(self) -> None:
        x = self.config.getint("Location", "ClickX", fallback=0)
        y = self.config.getint("Location", "ClickY", fallback=0)
        self.coord_var.set(f"({x}, {y})")

        self.radius_var.set(self.config.getint("Movement", "Radius", fallback=25))
        self.spin_speed_var.set(self.config.getint("Movement", "SpinSpeed", fallback=10))
        self.move_speed_var.set(self.config.getint("Movement", "MoveSpeed", fallback=10))
        self.step_delay_var.set(self.config.getint("Movement", "StepDelayMs", fallback=20))
        self.clockwise_var.set(self.config.getboolean("Movement", "Clockwise", fallback=True))

        self.center_click_every_var.set(
            self.config.getint("Clicking", "CenterClickEveryRotations", fallback=1)
        )
        self.before_click_delay_var.set(self.config.getint("Clicking", "BeforeClickDelayMs", fallback=0))
        self.after_click_delay_var.set(self.config.getint("Clicking", "AfterClickDelayMs", fallback=0))

        self.loop_count_var.set(self.config.getint("Loops", "LoopCount", fallback=0))
        self.per_loop_delay_var.set(self.config.getint("Loops", "PerLoopDelayMs", fallback=0))
        self.post_loop_key_enabled_var.set(
            self.config.getboolean("Loops", "PostLoopKeyEnabled", fallback=False)
        )
        self.post_loop_key_var.set(self.config.get("Loops", "PostLoopKey", fallback="SPACE"))

        self.start_hotkey_var.set(self.config.get("Hotkeys", "Start", fallback="F6"))
        self.stop_hotkey_var.set(self.config.get("Hotkeys", "Stop", fallback="F7"))
        self.confirm_hotkey_var.set(self.config.get("Hotkeys", "ConfirmLocation", fallback="F8"))

        self.debug_level_var.set(self.config.get("Debug", "Level", fallback="INFO"))

    def _sync_text_vars_from_ints(self) -> None:
        self.radius_text_var.set(str(self.radius_var.get()))
        self.spin_speed_text_var.set(str(self.spin_speed_var.get()))
        self.move_speed_text_var.set(str(self.move_speed_var.get()))
        self.step_delay_text_var.set(str(self.step_delay_var.get()))

        self.center_click_every_text_var.set(str(self.center_click_every_var.get()))
        self.before_click_delay_text_var.set(str(self.before_click_delay_var.get()))
        self.after_click_delay_text_var.set(str(self.after_click_delay_var.get()))

        self.loop_count_text_var.set(str(self.loop_count_var.get()))
        self.per_loop_delay_text_var.set(str(self.per_loop_delay_var.get()))

    def _bind_text_var_to_int(self, text_var: tk.StringVar, int_var: tk.IntVar) -> None:
        def _cb(*_):
            s = text_var.get().strip()
            if s in ("", "-", "+"):
                return
            try:
                v = int(s)
            except Exception:
                return
            try:
                int_var.set(v)
            except Exception:
                return

        text_var.trace_add("write", _cb)

    def _bind_autosave_vars(self) -> None:
        def save_int(var: tk.IntVar, section: str, option: str) -> None:
            def _cb(*_):
                try:
                    self.config.set(section, option, int(var.get()))
                except Exception:
                    return

            var.trace_add("write", _cb)

        def save_bool(var: tk.BooleanVar, section: str, option: str) -> None:
            def _cb(*_):
                try:
                    self.config.set(section, option, 1 if var.get() else 0)
                except Exception:
                    return

            var.trace_add("write", _cb)

        def save_str(var: tk.StringVar, section: str, option: str) -> None:
            def _cb(*_):
                try:
                    self.config.set(section, option, var.get())
                except Exception:
                    return

            var.trace_add("write", _cb)

        save_int(self.radius_var, "Movement", "Radius")
        save_int(self.spin_speed_var, "Movement", "SpinSpeed")
        save_int(self.move_speed_var, "Movement", "MoveSpeed")
        save_int(self.step_delay_var, "Movement", "StepDelayMs")
        save_bool(self.clockwise_var, "Movement", "Clockwise")

        save_int(self.center_click_every_var, "Clicking", "CenterClickEveryRotations")
        save_int(self.before_click_delay_var, "Clicking", "BeforeClickDelayMs")
        save_int(self.after_click_delay_var, "Clicking", "AfterClickDelayMs")

        save_int(self.loop_count_var, "Loops", "LoopCount")
        save_int(self.per_loop_delay_var, "Loops", "PerLoopDelayMs")
        save_bool(self.post_loop_key_enabled_var, "Loops", "PostLoopKeyEnabled")
        save_str(self.post_loop_key_var, "Loops", "PostLoopKey")

    def _apply_theme(self) -> None:
        try:
            self.root.configure(bg=THEME_BG)
        except Exception:
            pass

        default_font = tkfont.nametofont("TkDefaultFont")
        default_family = default_font.actual().get("family", "Segoe UI")
        default_font.configure(family=default_family, size=10)
        try:
            tkfont.nametofont("TkTextFont").configure(family=default_family, size=10)
        except Exception:
            pass

        mono_family = "Cascadia Mono" if os.name == "nt" else "Courier New"
        self._font_title = tkfont.Font(family=default_family, size=18, weight="bold")
        self._font_subtitle = tkfont.Font(family=default_family, size=10)
        self._font_section = tkfont.Font(family=default_family, size=11, weight="bold")
        self._font_badge = tkfont.Font(family=default_family, size=9, weight="bold")
        self._font_mono = tkfont.Font(family=mono_family, size=10)

        if _HAS_CTK and ctk is not None:
            try:
                self._ctk_font_title = ctk.CTkFont(family=default_family, size=18, weight="bold")
                self._ctk_font_subtitle = ctk.CTkFont(family=default_family, size=10)
                self._ctk_font_section = ctk.CTkFont(family=default_family, size=11, weight="bold")
                self._ctk_font_badge = ctk.CTkFont(family=default_family, size=9, weight="bold")
                self._ctk_font_mono = ctk.CTkFont(family=mono_family, size=10)
            except Exception:
                self._ctk_font_title = (default_family, 18, "bold")
                self._ctk_font_subtitle = (default_family, 10)
                self._ctk_font_section = (default_family, 11, "bold")
                self._ctk_font_badge = (default_family, 9, "bold")
                self._ctk_font_mono = (mono_family, 10)

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background=THEME_BG)
        style.configure("Page.TFrame", background=THEME_BG)
        style.configure("TLabel", background=THEME_BG, foreground=THEME_TEXT)
        style.configure("Muted.TLabel", background=THEME_BG, foreground=THEME_MUTED)
        style.configure("Card.TFrame", background=THEME_CARD)
        style.configure("Card.TLabel", background=THEME_CARD, foreground=THEME_TEXT)
        style.configure("Card.Muted.TLabel", background=THEME_CARD, foreground=THEME_MUTED)

        style.configure("TNotebook", background=THEME_BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=THEME_BG,
            foreground=THEME_MUTED,
            padding=[14, 10],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME_CARD), ("active", THEME_BG)],
            foreground=[("selected", THEME_TEXT), ("active", THEME_TEXT)],
        )

        style.configure(
            "Primary.TButton",
            background=THEME_ACCENT,
            foreground="#FFFFFF",
            padding=[14, 10],
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", THEME_ACCENT_DARK), ("disabled", THEME_BORDER)],
            foreground=[("disabled", THEME_MUTED)],
        )

        style.configure(
            "Danger.TButton",
            background=THEME_DANGER,
            foreground="#FFFFFF",
            padding=[14, 10],
            borderwidth=0,
        )
        style.map(
            "Danger.TButton",
            background=[("active", THEME_DANGER_DARK), ("disabled", THEME_BORDER)],
            foreground=[("disabled", THEME_MUTED)],
        )

        style.configure(
            "Secondary.TButton",
            background=THEME_CARD,
            foreground=THEME_TEXT,
            padding=[14, 10],
        )
        style.map(
            "Secondary.TButton",
            background=[("active", THEME_BG), ("disabled", THEME_CARD)],
            foreground=[("disabled", THEME_MUTED)],
        )
        style.configure("TSpinbox", padding=[6, 6])
        style.configure("TCombobox", padding=[6, 6])
        style.configure("TEntry", padding=[6, 6])

    def _set_rounded_corners(self, window: tk.Tk | tk.Toplevel) -> None:
        if os.name != "nt":
            return
        try:
            window.update_idletasks()
        except Exception:
            pass

        try:
            hwnd = int(window.winfo_id())
        except Exception:
            return

        try:
            # DWMWA_WINDOW_CORNER_PREFERENCE = 33
            # DWMWCP_ROUND = 2
            pref = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                ctypes.c_int(33),
                ctypes.byref(pref),
                ctypes.sizeof(pref),
            )
        except Exception:
            return

    def _create_card(
        self,
        parent: tk.Misc,
        title: str,
        subtitle: str | None = None,
    ) -> tuple[tk.Frame, tk.Frame]:
        if _HAS_CTK and ctk is not None and isinstance(parent, ctk.CTkBaseClass):
            card = ctk.CTkFrame(parent, corner_radius=16, fg_color=THEME_CARD)

            header = ctk.CTkFrame(card, fg_color=THEME_CARD)
            header.pack(fill="x", padx=16, pady=(14, 8))

            ctk.CTkLabel(
                header,
                text=title,
                text_color=THEME_TEXT,
                font=self._ctk_font_section,
            ).pack(anchor="w")

            if subtitle:
                ctk.CTkLabel(
                    header,
                    text=subtitle,
                    text_color=THEME_MUTED,
                    font=self._ctk_font_subtitle,
                ).pack(anchor="w", pady=(2, 0))

            body = ctk.CTkFrame(card, fg_color=THEME_CARD)
            body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
            return card, body  # type: ignore[return-value]

        card = tk.Frame(
            parent,
            bg=THEME_CARD,
            highlightbackground=THEME_BORDER,
            highlightthickness=1,
        )

        header = tk.Frame(card, bg=THEME_CARD)
        header.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(
            header,
            text=title,
            bg=THEME_CARD,
            fg=THEME_TEXT,
            font=self._font_section,
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                header,
                text=subtitle,
                bg=THEME_CARD,
                fg=THEME_MUTED,
                font=self._font_subtitle,
            ).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(card, bg=THEME_CARD)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        return card, body

    def _create_badge_label(self, parent: tk.Misc) -> tk.Label:
        if _HAS_CTK and ctk is not None:
            lbl = ctk.CTkLabel(
                parent,
                text="",
                corner_radius=999,
                fg_color=THEME_BORDER,
                text_color=THEME_TEXT,
                font=self._ctk_font_badge,
                padx=10,
                pady=6,
            )
            lbl.pack(side="left", padx=(0, 8))
            return lbl  # type: ignore[return-value]

        lbl = tk.Label(
            parent,
            text="",
            bg=THEME_BORDER,
            fg=THEME_TEXT,
            font=self._font_badge,
            padx=10,
            pady=6,
        )
        lbl.pack(side="left", padx=(0, 8))
        return lbl

    def _status_badge_colors(self, status: str) -> tuple[str, str]:
        s = status.strip().lower()
        if "running" in s:
            return THEME_SUCCESS, "#FFFFFF"
        if "stop" in s:
            return THEME_WARNING, "#111827"
        if "pick" in s:
            return THEME_PURPLE, "#FFFFFF"
        if "error" in s:
            return THEME_DANGER, "#FFFFFF"
        return THEME_BORDER, THEME_TEXT

    def _show_pick_overlay(self) -> None:
        overlay = tk.Toplevel(self.root)
        self._pick_overlay = overlay
        self._set_rounded_corners(overlay)
        overlay.overrideredirect(True)
        try:
            overlay.attributes("-topmost", True)
        except Exception:
            pass
        try:
            overlay.attributes("-alpha", 0.95)
        except Exception:
            pass

        overlay.configure(bg=THEME_BG)

        w = 560
        h = 190
        try:
            sw = overlay.winfo_screenwidth()
            sh = overlay.winfo_screenheight()
            x = max(0, int((sw - w) / 2))
            y = max(0, int(sh * 0.04))
            overlay.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            overlay.geometry(f"{w}x{h}+0+0")

        card = tk.Frame(
            overlay,
            bg=THEME_CARD,
            highlightbackground=THEME_BORDER,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=10, pady=10)

        header = tk.Frame(card, bg=THEME_CARD)
        header.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(
            header,
            text="Pick Location",
            bg=THEME_CARD,
            fg=THEME_TEXT,
            font=self._font_section,
        ).pack(anchor="w")

        body = tk.Frame(card, bg=THEME_CARD)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        hk = self.confirm_hotkey_var.get().strip() or "F8"
        tk.Label(
            body,
            text=f"Move your cursor to the target spot and press {hk} to confirm.",
            bg=THEME_CARD,
            fg=THEME_TEXT,
            font=self._font_subtitle,
        ).pack(anchor="w")

        tk.Label(
            body,
            text="Press ESC to cancel.",
            bg=THEME_CARD,
            fg=THEME_MUTED,
            font=self._font_subtitle,
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            body,
            textvariable=self._pick_cursor_var,
            bg=THEME_CARD,
            fg=THEME_TEXT,
            font=self._font_mono,
        ).pack(anchor="w", pady=(10, 0))

        def _poll_cursor() -> None:
            if not self.picker.active:
                return
            try:
                x2, y2 = get_cursor_pos()
                self._pick_cursor_var.set(f"Cursor: {x2}, {y2}")
            except Exception:
                pass
            try:
                self._after_pick_id = overlay.after(50, _poll_cursor)
            except Exception:
                self._after_pick_id = None

        _poll_cursor()

    def _hide_pick_overlay(self) -> None:
        overlay = self._pick_overlay
        self._pick_overlay = None
        after_id = self._after_pick_id
        self._after_pick_id = None
        if overlay is None:
            return

        if after_id is not None:
            try:
                overlay.after_cancel(after_id)
            except Exception:
                pass
        try:
            if overlay.winfo_exists():
                overlay.destroy()
        except Exception:
            pass

    def _build_ui(self) -> None:
        self._apply_theme()
        self._set_rounded_corners(self.root)

        self.root.title("Rivals AFK Macro")
        try:
            self.root.minsize(900, 620)
        except Exception:
            pass

        header = (ctk.CTkFrame(self.root, fg_color=THEME_BG) if _HAS_CTK and ctk is not None else tk.Frame(self.root, bg=THEME_BG))
        header.pack(fill="x", padx=16, pady=(16, 10))

        header_left = (ctk.CTkFrame(header, fg_color=THEME_BG) if _HAS_CTK and ctk is not None else tk.Frame(header, bg=THEME_BG))
        header_left.pack(side="left", fill="x", expand=True)

        if _HAS_CTK and ctk is not None:
            ctk.CTkLabel(
                header_left,
                text="Rivals AFK Macro",
                text_color=THEME_TEXT,
                font=self._ctk_font_title,
            ).pack(anchor="w")
        else:
            tk.Label(
                header_left,
                text="Rivals AFK Macro",
                bg=THEME_BG,
                fg=THEME_TEXT,
                font=self._font_title,
            ).pack(anchor="w")

        if _HAS_CTK and ctk is not None:
            ctk.CTkLabel(
                header_left,
                text="Advanced session automation · AutoIt input · Hotkeys",
                text_color=THEME_MUTED,
                font=self._ctk_font_subtitle,
            ).pack(anchor="w", pady=(4, 0))
        else:
            tk.Label(
                header_left,
                text="Advanced session automation · AutoIt input · Hotkeys",
                bg=THEME_BG,
                fg=THEME_MUTED,
                font=self._font_subtitle,
            ).pack(anchor="w", pady=(4, 0))

        header_right = (ctk.CTkFrame(header, fg_color=THEME_BG) if _HAS_CTK and ctk is not None else tk.Frame(header, bg=THEME_BG))
        header_right.pack(side="right", anchor="e")

        self._header_status_badge = self._create_badge_label(header_right)
        self._header_location_badge = self._create_badge_label(header_right)
        self._header_progress_badge = self._create_badge_label(header_right)

        if _HAS_CTK and ctk is not None:
            content = ctk.CTkFrame(self.root, fg_color=THEME_BG)
            content.pack(fill="both", expand=True, padx=16, pady=(0, 12))

            tabview = ctk.CTkTabview(
                content,
                corner_radius=16,
                fg_color=THEME_BG,
                segmented_button_fg_color=THEME_CARD,
                segmented_button_selected_color=THEME_BORDER,
                segmented_button_selected_hover_color=THEME_BORDER,
                segmented_button_unselected_color=THEME_CARD,
                segmented_button_unselected_hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
                text_color_disabled=THEME_MUTED,
            )
            tabview.pack(fill="both", expand=True)
            self.tabview = tabview

            tabview.add("Dashboard")
            tabview.add("Movement")
            tabview.add("Loops")
            tabview.add("Hotkeys")
            tabview.add("Debug")

            main_tab = tabview.tab("Dashboard")
            move_tab = tabview.tab("Movement")
            loops_tab = tabview.tab("Loops")
            hotkeys_tab = tabview.tab("Hotkeys")
            debug_tab = tabview.tab("Debug")
        else:
            content = ttk.Frame(self.root, style="Page.TFrame")
            content.pack(fill="both", expand=True, padx=16, pady=(0, 12))

            notebook = ttk.Notebook(content)
            notebook.pack(fill="both", expand=True)
            self.notebook = notebook

            main_tab = ttk.Frame(notebook, style="Page.TFrame")
            move_tab = ttk.Frame(notebook, style="Page.TFrame")
            loops_tab = ttk.Frame(notebook, style="Page.TFrame")
            hotkeys_tab = ttk.Frame(notebook, style="Page.TFrame")
            debug_tab = ttk.Frame(notebook, style="Page.TFrame")

            notebook.add(main_tab, text="Dashboard")
            notebook.add(move_tab, text="Movement")
            notebook.add(loops_tab, text="Loops")
            notebook.add(hotkeys_tab, text="Hotkeys")
            notebook.add(debug_tab, text="Debug")

        self._build_main_tab(main_tab)
        self._build_movement_tab(move_tab)
        self._build_loops_tab(loops_tab)
        self._build_hotkeys_tab(hotkeys_tab)
        self._build_debug_tab(debug_tab)

        footer = (ctk.CTkFrame(self.root, fg_color=THEME_BG) if _HAS_CTK and ctk is not None else tk.Frame(self.root, bg=THEME_BG))
        footer.pack(fill="x", padx=16, pady=(0, 16))

        left = (ctk.CTkFrame(footer, fg_color=THEME_BG) if _HAS_CTK and ctk is not None else tk.Frame(footer, bg=THEME_BG))
        left.pack(side="left", fill="x", expand=True)

        if _HAS_CTK and ctk is not None:
            self._footer_error_label = ctk.CTkLabel(
                left,
                textvariable=self.error_var,
                text_color=THEME_MUTED,
                font=self._ctk_font_subtitle,
            )
            self._footer_error_label.pack(anchor="w")

            self._loop_progressbar = ctk.CTkProgressBar(left)
            self._loop_progressbar.set(0)
            self._loop_progressbar.pack(fill="x", pady=(8, 0))
        else:
            self._footer_error_label = tk.Label(
                left,
                textvariable=self.error_var,
                bg=THEME_BG,
                fg=THEME_MUTED,
                font=self._font_subtitle,
            )
            self._footer_error_label.pack(anchor="w")

            self._loop_progressbar = ttk.Progressbar(
                left,
                mode="determinate",
                maximum=100,
            )
            self._loop_progressbar.pack(fill="x", pady=(6, 0))

        right = (ctk.CTkFrame(footer, fg_color=THEME_BG) if _HAS_CTK and ctk is not None else tk.Frame(footer, bg=THEME_BG))
        right.pack(side="right")

        if _HAS_CTK and ctk is not None:
            self._footer_hotkeys_label = ctk.CTkLabel(
                right,
                text="",
                text_color=THEME_MUTED,
                font=self._ctk_font_subtitle,
            )
            self._footer_hotkeys_label.pack(anchor="e")
        else:
            self._footer_hotkeys_label = tk.Label(
                right,
                text="",
                bg=THEME_BG,
                fg=THEME_MUTED,
                font=self._font_subtitle,
            )
            self._footer_hotkeys_label.pack(anchor="e")

            self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._poll_chrome()

    def _on_tab_changed(self, _event: object) -> None:
        if self.notebook is not None:
            try:
                idx = int(self.notebook.index("current"))
                self.config.set("UI", "LastTab", idx)
            except Exception:
                return
            return

        if self.tabview is not None and _HAS_CTK and ctk is not None:
            try:
                current = self.tabview.get()
                names = ["Dashboard", "Movement", "Loops", "Hotkeys", "Debug"]
                idx = names.index(current) if current in names else 0
                self.config.set("UI", "LastTab", idx)
            except Exception:
                return

    def _refresh_chrome(self) -> None:
        status = self.status_var.get()
        status_bg, status_fg = self._status_badge_colors(status)
        if self._header_status_badge is not None:
            try:
                self._header_status_badge.configure(text=status, bg=status_bg, fg=status_fg)
            except Exception:
                try:
                    self._header_status_badge.configure(text=status, fg_color=status_bg, text_color=status_fg)
                except Exception:
                    pass

        if self._header_location_badge is not None:
            try:
                self._header_location_badge.configure(text=f"Location: {self.coord_var.get()}")
            except Exception:
                pass

        if self._header_progress_badge is not None:
            try:
                self._header_progress_badge.configure(text=f"Loops: {self.loop_progress_var.get()}")
            except Exception:
                pass

        if self._footer_hotkeys_label is not None:
            start_hk = self.start_hotkey_var.get().strip()
            stop_hk = self.stop_hotkey_var.get().strip()
            confirm_hk = self.confirm_hotkey_var.get().strip() or "F8"
            self._footer_hotkeys_label.configure(
                text=f"Start: {start_hk}   Stop: {stop_hk}   Confirm: {confirm_hk}   Cancel: ESC"
            )

        running = bool(self.macro_running)
        picking = bool(self.picker.active)

        if self._btn_start is not None:
            try:
                self._btn_start.set_enabled(not (running or picking))
            except Exception:
                try:
                    self._btn_start.configure(state=("disabled" if (running or picking) else "normal"))
                except Exception:
                    pass
        if self._btn_stop is not None:
            try:
                self._btn_stop.set_enabled(running)
            except Exception:
                try:
                    self._btn_stop.configure(state=("normal" if running else "disabled"))
                except Exception:
                    pass
        if self._btn_pick is not None:
            try:
                self._btn_pick.set_enabled(not (running or picking))
            except Exception:
                try:
                    self._btn_pick.configure(state=("disabled" if (running or picking) else "normal"))
                except Exception:
                    pass

        if self._loop_progressbar is not None:
            try:
                target = int(self.loop_count_var.get())
            except Exception:
                target = 0
            try:
                current = int(self.loop_progress_var.get())
            except Exception:
                current = 0
            if target > 0:
                ratio = max(0.0, min(1.0, float(current) / float(target)))
            else:
                ratio = 0.0

            try:
                # ttk.Progressbar
                self._loop_progressbar.configure(value=int(ratio * 100))
            except Exception:
                try:
                    # CTkProgressBar
                    self._loop_progressbar.set(ratio)
                except Exception:
                    pass

    def _poll_chrome(self) -> None:
        if self._closing:
            return
        try:
            self._refresh_chrome()
        except Exception:
            pass
        try:
            self._after_chrome_id = self.root.after(250, self._poll_chrome)
        except Exception:
            self._after_chrome_id = None

    def _build_main_tab(self, tab: ttk.Frame) -> None:
        if _HAS_CTK and ctk is not None and isinstance(tab, ctk.CTkFrame):
            tab.grid_columnconfigure(0, weight=1)

            card, body = self._create_card(
                tab,
                title="Controls",
                subtitle="Start/Stop the macro and manage the target location",
            )
            card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

            top = ctk.CTkFrame(body, fg_color=THEME_CARD)
            top.pack(fill="x")

            self._btn_start = ctk.CTkButton(
                top,
                text="Start",
                command=self.request_start,
                corner_radius=14,
                fg_color=THEME_ACCENT,
                hover_color=THEME_ACCENT_DARK,
                text_color="#FFFFFF",
            )
            self._btn_start.pack(side="left")

            self._btn_stop = ctk.CTkButton(
                top,
                text="Stop",
                command=self.request_stop,
                corner_radius=14,
                fg_color=THEME_DANGER,
                hover_color=THEME_DANGER_DARK,
                text_color="#FFFFFF",
            )
            self._btn_stop.pack(side="left", padx=(10, 0))

            self._btn_pick = ctk.CTkButton(
                top,
                text="Pick Location",
                command=self.request_pick_location,
                corner_radius=14,
                fg_color=THEME_BG,
                hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
            )
            self._btn_pick.pack(side="left", padx=(10, 0))

            ctk.CTkButton(
                top,
                text="Reset to Defaults",
                command=self.reset_config,
                corner_radius=14,
                fg_color=THEME_BG,
                hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
            ).pack(side="left", padx=(10, 0))

            info = ctk.CTkFrame(body, fg_color=THEME_CARD)
            info.pack(fill="x", pady=(14, 0))

            ctk.CTkLabel(
                info,
                text="Selected location:",
                text_color=THEME_MUTED,
                font=self._ctk_font_subtitle,
            ).pack(side="left")

            ctk.CTkLabel(
                info,
                textvariable=self.coord_var,
                text_color=THEME_TEXT,
                font=self._ctk_font_subtitle,
            ).pack(side="left", padx=(8, 0))
            return

        tab.columnconfigure(0, weight=1)

        card, body = self._create_card(
            tab,
            title="Controls",
            subtitle="Start/Stop the macro and manage the target location",
        )
        card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        top = tk.Frame(body, bg=THEME_CARD)
        top.pack(fill="x")

        self._btn_start = RoundedButton(
            top,
            text="Start",
            command=self.request_start,
            bg=THEME_ACCENT,
            bg_hover=THEME_ACCENT_DARK,
            fg="#FFFFFF",
            font=self._font_subtitle,
        )
        self._btn_start.pack(side="left")

        self._btn_stop = RoundedButton(
            top,
            text="Stop",
            command=self.request_stop,
            bg=THEME_DANGER,
            bg_hover=THEME_DANGER_DARK,
            fg="#FFFFFF",
            font=self._font_subtitle,
        )
        self._btn_stop.pack(side="left", padx=(10, 0))

        self._btn_pick = RoundedButton(
            top,
            text="Pick Location",
            command=self.request_pick_location,
            bg=THEME_CARD,
            bg_hover=THEME_BG,
            fg=THEME_TEXT,
            bg_disabled=THEME_BORDER,
            fg_disabled=THEME_MUTED,
            font=self._font_subtitle,
        )
        self._btn_pick.pack(side="left", padx=(10, 0))

        reset_btn = RoundedButton(
            top,
            text="Reset to Defaults",
            command=self.reset_config,
            bg=THEME_CARD,
            bg_hover=THEME_BG,
            fg=THEME_TEXT,
            bg_disabled=THEME_BORDER,
            fg_disabled=THEME_MUTED,
            font=self._font_subtitle,
        )
        reset_btn.pack(side="left", padx=(10, 0))

        info = tk.Frame(body, bg=THEME_CARD)
        info.pack(fill="x", pady=(14, 0))

        tk.Label(
            info,
            text="Selected location:",
            bg=THEME_CARD,
            fg=THEME_MUTED,
            font=self._font_subtitle,
        ).pack(side="left")

        tk.Label(
            info,
            textvariable=self.coord_var,
            bg=THEME_CARD,
            fg=THEME_TEXT,
            font=self._font_subtitle,
        ).pack(side="left", padx=(8, 0))

    def _build_movement_tab(self, tab: ttk.Frame) -> None:
        if _HAS_CTK and ctk is not None and isinstance(tab, ctk.CTkFrame):
            tab.grid_columnconfigure(0, weight=1)

            card, body = self._create_card(
                tab,
                title="Movement Settings",
                subtitle="Configure circular movement behavior",
            )
            card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

            body.grid_columnconfigure(1, weight=1)

            def add_entry(row: int, label: str, text_var: tk.StringVar) -> None:
                ctk.CTkLabel(body, text=label, text_color=THEME_TEXT).grid(
                    row=row, column=0, sticky="w", pady=6
                )
                ctk.CTkEntry(
                    body,
                    textvariable=text_var,
                    corner_radius=10,
                    width=160,
                    fg_color=THEME_BG,
                    border_color=THEME_BORDER,
                    text_color=THEME_TEXT,
                ).grid(
                    row=row, column=1, sticky="w", pady=6
                )

            add_entry(0, "Circle radius (px)", self.radius_text_var)
            add_entry(1, "Spin speed (degrees step)", self.spin_speed_text_var)
            add_entry(2, "Mouse move speed", self.move_speed_text_var)
            add_entry(3, "Step delay (ms)", self.step_delay_text_var)

            ctk.CTkSwitch(body, text="Clockwise", variable=self.clockwise_var).grid(
                row=4, column=0, columnspan=2, sticky="w", pady=(10, 0)
            )

            ctk.CTkLabel(body, text="", height=1).grid(row=5, column=0, columnspan=2, pady=6)

            add_entry(6, "Center click every rotations", self.center_click_every_text_var)
            add_entry(7, "Before click delay (ms)", self.before_click_delay_text_var)
            add_entry(8, "After click delay (ms)", self.after_click_delay_text_var)

            ctk.CTkButton(
                body,
                text="Reset to Defaults",
                command=self.reset_config,
                corner_radius=14,
                fg_color=THEME_BG,
                hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
            ).grid(row=9, column=0, columnspan=2, sticky="w", pady=(14, 0))
            return

        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)

        card, body = self._create_card(
            tab,
            title="Movement Settings",
            subtitle="Configure circular movement behavior",
        )
        card.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        body.columnconfigure(1, weight=1)

        def add_spin(row: int, label: str, var: tk.IntVar, frm: int, to: int) -> None:
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Spinbox(body, from_=frm, to=to, textvariable=var, width=12).grid(
                row=row,
                column=1,
                sticky="w",
                pady=6,
            )

        add_spin(0, "Circle radius (px)", self.radius_var, 0, 1000)
        add_spin(1, "Spin speed (degrees step)", self.spin_speed_var, 1, 90)
        add_spin(2, "Mouse move speed", self.move_speed_var, 0, 100)
        add_spin(3, "Step delay (ms)", self.step_delay_var, 0, 1000)

        ttk.Checkbutton(body, text="Clockwise", variable=self.clockwise_var).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(6, 0),
        )

        ttk.Separator(body).grid(row=5, column=0, columnspan=2, sticky="ew", pady=12)

        add_spin(6, "Center click every rotations", self.center_click_every_var, 1, 1000)
        add_spin(7, "Before click delay (ms)", self.before_click_delay_var, 0, 10000)
        add_spin(8, "After click delay (ms)", self.after_click_delay_var, 0, 10000)

        reset_btn = RoundedButton(
            body,
            text="Reset to Defaults",
            command=self.reset_config,
            bg=THEME_CARD,
            bg_hover=THEME_BG,
            fg=THEME_TEXT,
            bg_disabled=THEME_BORDER,
            fg_disabled=THEME_MUTED,
            font=self._font_subtitle,
        )
        reset_btn.grid(row=9, column=0, columnspan=2, sticky="w", pady=(14, 0))

    def _build_loops_tab(self, tab: ttk.Frame) -> None:
        if _HAS_CTK and ctk is not None and isinstance(tab, ctk.CTkFrame):
            tab.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(tab, text="Loop count (0 = infinite)", text_color=THEME_TEXT).grid(
                row=0, column=0, sticky="w", padx=12, pady=6
            )
            ctk.CTkEntry(
                tab,
                textvariable=self.loop_count_text_var,
                corner_radius=10,
                width=200,
                fg_color=THEME_BG,
                border_color=THEME_BORDER,
                text_color=THEME_TEXT,
            ).grid(
                row=0, column=1, sticky="w", padx=12, pady=6
            )

            ctk.CTkLabel(tab, text="Per-loop delay (ms)", text_color=THEME_TEXT).grid(
                row=1, column=0, sticky="w", padx=12, pady=6
            )
            ctk.CTkEntry(
                tab,
                textvariable=self.per_loop_delay_text_var,
                corner_radius=10,
                width=200,
                fg_color=THEME_BG,
                border_color=THEME_BORDER,
                text_color=THEME_TEXT,
            ).grid(
                row=1, column=1, sticky="w", padx=12, pady=6
            )

            ctk.CTkSwitch(tab, text="Post-loop key press", variable=self.post_loop_key_enabled_var).grid(
                row=2, column=0, columnspan=2, sticky="w", padx=12, pady=10
            )

            ctk.CTkLabel(tab, text="Key after each loop", text_color=THEME_TEXT).grid(
                row=3, column=0, sticky="w", padx=12, pady=6
            )
            ctk.CTkOptionMenu(
                tab,
                variable=self.post_loop_key_var,
                values=POST_ACTION_KEY_CHOICES,
                corner_radius=10,
                fg_color=THEME_BG,
                button_color=THEME_BORDER,
                button_hover_color=THEME_ACCENT,
                dropdown_fg_color=THEME_CARD,
                dropdown_hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
                dropdown_text_color=THEME_TEXT,
            ).grid(row=3, column=1, sticky="w", padx=12, pady=6)

            ctk.CTkButton(
                tab,
                text="Reset to Defaults",
                command=self.reset_config,
                corner_radius=14,
                fg_color=THEME_BG,
                hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
            ).grid(row=4, column=0, columnspan=2, sticky="w", padx=12, pady=(14, 6))
            return

        tab.columnconfigure(1, weight=1)

        def add_spin(row: int, label: str, var: tk.IntVar, frm: int, to: int):
            ttk.Label(tab, text=label).grid(row=row, column=0, sticky="w", padx=12, pady=6)
            ttk.Spinbox(tab, from_=frm, to=to, textvariable=var, width=10).grid(
                row=row, column=1, sticky="w", padx=12, pady=6
            )

        add_spin(0, "Loop count (0 = infinite)", self.loop_count_var, 0, 1000000)
        add_spin(1, "Per-loop delay (ms)", self.per_loop_delay_var, 0, 600000)

        ttk.Checkbutton(tab, text="Post-loop key press", variable=self.post_loop_key_enabled_var).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=12, pady=6
        )

        ttk.Label(tab, text="Key after each loop").grid(row=3, column=0, sticky="w", padx=12, pady=6)
        key_box = ttk.Combobox(
            tab,
            textvariable=self.post_loop_key_var,
            values=POST_ACTION_KEY_CHOICES,
            state="readonly",
            width=15,
        )
        key_box.grid(row=3, column=1, sticky="w", padx=12, pady=6)

        reset_btn = RoundedButton(
            tab,
            text="Reset to Defaults",
            command=self.reset_config,
            bg=THEME_CARD,
            bg_hover=THEME_BG,
            fg=THEME_TEXT,
            bg_disabled=THEME_BORDER,
            fg_disabled=THEME_MUTED,
            font=self._font_subtitle,
        )
        reset_btn.grid(row=4, column=0, columnspan=2, sticky="w", padx=12, pady=(14, 6))

    def _build_hotkeys_tab(self, tab: ttk.Frame) -> None:
        if _HAS_CTK and ctk is not None and isinstance(tab, ctk.CTkFrame):
            tab.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(tab, text="Start hotkey", text_color=THEME_TEXT).grid(
                row=0, column=0, sticky="w", padx=12, pady=6
            )
            start_menu = ctk.CTkOptionMenu(
                tab,
                variable=self.start_hotkey_var,
                values=HOTKEY_CHOICES,
                corner_radius=10,
                fg_color=THEME_BG,
                button_color=THEME_BORDER,
                button_hover_color=THEME_ACCENT,
                dropdown_fg_color=THEME_CARD,
                dropdown_hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
                dropdown_text_color=THEME_TEXT,
            )
            start_menu.grid(row=0, column=1, sticky="w", padx=12, pady=6)

            ctk.CTkLabel(tab, text="Stop hotkey", text_color=THEME_TEXT).grid(
                row=1, column=0, sticky="w", padx=12, pady=6
            )
            stop_menu = ctk.CTkOptionMenu(
                tab,
                variable=self.stop_hotkey_var,
                values=HOTKEY_CHOICES,
                corner_radius=10,
                fg_color=THEME_BG,
                button_color=THEME_BORDER,
                button_hover_color=THEME_ACCENT,
                dropdown_fg_color=THEME_CARD,
                dropdown_hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
                dropdown_text_color=THEME_TEXT,
            )
            stop_menu.grid(row=1, column=1, sticky="w", padx=12, pady=6)

            ctk.CTkLabel(tab, text="Confirm-location hotkey", text_color=THEME_TEXT).grid(
                row=2, column=0, sticky="w", padx=12, pady=6
            )
            confirm_menu = ctk.CTkOptionMenu(
                tab,
                variable=self.confirm_hotkey_var,
                values=HOTKEY_CHOICES,
                corner_radius=10,
                fg_color=THEME_BG,
                button_color=THEME_BORDER,
                button_hover_color=THEME_ACCENT,
                dropdown_fg_color=THEME_CARD,
                dropdown_hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
                dropdown_text_color=THEME_TEXT,
            )
            confirm_menu.grid(row=2, column=1, sticky="w", padx=12, pady=6)

            def _save_hotkeys() -> None:
                self.config.set("Hotkeys", "Start", self.start_hotkey_var.get())
                self.config.set("Hotkeys", "Stop", self.stop_hotkey_var.get())
                self.config.set("Hotkeys", "ConfirmLocation", self.confirm_hotkey_var.get())
                self._register_hotkeys()

            start_menu.configure(command=lambda _v=None: _save_hotkeys())
            stop_menu.configure(command=lambda _v=None: _save_hotkeys())
            confirm_menu.configure(command=lambda _v=None: _save_hotkeys())

            ctk.CTkButton(
                tab,
                text="Reset to Defaults",
                command=self.reset_config,
                corner_radius=14,
                fg_color=THEME_BG,
                hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
            ).grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(14, 6))
            return

        tab.columnconfigure(1, weight=1)

        ttk.Label(tab, text="Start hotkey").grid(row=0, column=0, sticky="w", padx=12, pady=6)
        start_box = ttk.Combobox(
            tab,
            textvariable=self.start_hotkey_var,
            values=HOTKEY_CHOICES,
            state="readonly",
            width=12,
        )
        start_box.grid(row=0, column=1, sticky="w", padx=12, pady=6)

        ttk.Label(tab, text="Stop hotkey").grid(row=1, column=0, sticky="w", padx=12, pady=6)
        stop_box = ttk.Combobox(
            tab,
            textvariable=self.stop_hotkey_var,
            values=HOTKEY_CHOICES,
            state="readonly",
            width=12,
        )
        stop_box.grid(row=1, column=1, sticky="w", padx=12, pady=6)

        ttk.Label(tab, text="Confirm-location hotkey").grid(row=2, column=0, sticky="w", padx=12, pady=6)
        confirm_box = ttk.Combobox(
            tab,
            textvariable=self.confirm_hotkey_var,
            values=HOTKEY_CHOICES,
            state="readonly",
            width=12,
        )
        confirm_box.grid(row=2, column=1, sticky="w", padx=12, pady=6)

        def _on_changed(_event: object) -> None:
            self.config.set("Hotkeys", "Start", self.start_hotkey_var.get())
            self.config.set("Hotkeys", "Stop", self.stop_hotkey_var.get())
            self.config.set("Hotkeys", "ConfirmLocation", self.confirm_hotkey_var.get())
            self._register_hotkeys()

        start_box.bind("<<ComboboxSelected>>", _on_changed)
        stop_box.bind("<<ComboboxSelected>>", _on_changed)
        confirm_box.bind("<<ComboboxSelected>>", _on_changed)

        reset_btn = RoundedButton(
            tab,
            text="Reset to Defaults",
            command=self.reset_config,
            bg=THEME_CARD,
            bg_hover=THEME_BG,
            fg=THEME_TEXT,
            bg_disabled=THEME_BORDER,
            fg_disabled=THEME_MUTED,
            font=self._font_subtitle,
        )
        reset_btn.grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(14, 6))

    def _build_debug_tab(self, tab: ttk.Frame) -> None:
        if _HAS_CTK and ctk is not None and isinstance(tab, ctk.CTkFrame):
            tab.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(tab, text="Debug level", text_color=THEME_TEXT).grid(
                row=0, column=0, sticky="w", padx=12, pady=6
            )
            level_menu = ctk.CTkOptionMenu(
                tab,
                variable=self.debug_level_var,
                values=["INFO", "ACTION", "WARNING", "ERROR", "TRACE"],
                corner_radius=10,
                fg_color=THEME_BG,
                button_color=THEME_BORDER,
                button_hover_color=THEME_ACCENT,
                dropdown_fg_color=THEME_CARD,
                dropdown_hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
                dropdown_text_color=THEME_TEXT,
            )
            level_menu.grid(row=0, column=1, sticky="w", padx=12, pady=6)

            def _on_level(_v: str) -> None:
                lvl = self.debug_level_var.get()
                self.config.set("Debug", "Level", lvl)
                set_logging_level(lvl)

            level_menu.configure(command=_on_level)

            ctk.CTkLabel(tab, text="Error status", text_color=THEME_TEXT).grid(
                row=1, column=0, sticky="w", padx=12, pady=6
            )
            ctk.CTkLabel(tab, textvariable=self.error_var, text_color=THEME_MUTED).grid(
                row=1, column=1, sticky="w", padx=12, pady=6
            )

            ctk.CTkButton(
                tab,
                text="Reset Config",
                command=self.reset_config,
                corner_radius=14,
                fg_color=THEME_BG,
                hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
            ).grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 6))

            ctk.CTkButton(
                tab,
                text="Reset to Defaults",
                command=self.reset_config,
                corner_radius=14,
                fg_color=THEME_BG,
                hover_color=THEME_BORDER,
                text_color=THEME_TEXT,
            ).grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 6))

            def _poll_error() -> None:
                if self._closing:
                    return
                self.error_var.set(self.error_manager.last_error)
                try:
                    self._after_error_id = self.root.after(250, _poll_error)
                except Exception:
                    self._after_error_id = None

            _poll_error()
            return

        tab.columnconfigure(1, weight=1)

        ttk.Label(tab, text="Debug level").grid(row=0, column=0, sticky="w", padx=12, pady=6)
        level_box = ttk.Combobox(
            tab,
            textvariable=self.debug_level_var,
            values=["INFO", "ACTION", "WARNING", "ERROR", "TRACE"],
            state="readonly",
            width=12,
        )
        level_box.grid(row=0, column=1, sticky="w", padx=12, pady=6)

        ttk.Label(tab, text="Error status").grid(row=1, column=0, sticky="w", padx=12, pady=6)
        ttk.Label(tab, textvariable=self.error_var).grid(row=1, column=1, sticky="w", padx=12, pady=6)

        reset_btn = RoundedButton(
            tab,
            text="Reset Config",
            command=self.reset_config,
            bg=THEME_CARD,
            bg_hover=THEME_BG,
            fg=THEME_TEXT,
            bg_disabled=THEME_BORDER,
            fg_disabled=THEME_MUTED,
            font=self._font_subtitle,
        )
        reset_btn.grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 6))

        reset_all_btn = RoundedButton(
            tab,
            text="Reset to Defaults",
            command=self.reset_config,
            bg=THEME_CARD,
            bg_hover=THEME_BG,
            fg=THEME_TEXT,
            bg_disabled=THEME_BORDER,
            fg_disabled=THEME_MUTED,
            font=self._font_subtitle,
        )
        reset_all_btn.grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 6))

        def _on_level(_event: object) -> None:
            lvl = self.debug_level_var.get()
            self.config.set("Debug", "Level", lvl)
            set_logging_level(lvl)

        level_box.bind("<<ComboboxSelected>>", _on_level)

        def _poll_error() -> None:
            if self._closing:
                return
            self.error_var.set(self.error_manager.last_error)
            try:
                self._after_error_id = self.root.after(250, _poll_error)
            except Exception:
                self._after_error_id = None

        _poll_error()

    def _register_hotkeys(self) -> None:
        try:
            self.hotkeys.register("start", self.start_hotkey_var.get(), self._hotkey_start)
            self.hotkeys.register("stop", self.stop_hotkey_var.get(), self._hotkey_stop)
            self.hotkeys.register("confirm", self.confirm_hotkey_var.get(), self._hotkey_confirm)
            self.hotkeys.register("cancel", "ESC", self._hotkey_cancel)
        except Exception as e:
            self.error_manager.report("Hotkey registration failed", e, critical=True)

    def _hotkey_start(self) -> None:
        self.root.after(0, self.request_start)

    def _hotkey_stop(self) -> None:
        self.root.after(0, self.request_stop)

    def _hotkey_confirm(self) -> None:
        self.root.after(0, self._confirm_location_hotkey)

    def _hotkey_cancel(self) -> None:
        self.root.after(0, self._cancel_pick_mode)

    def _confirm_location_hotkey(self) -> None:
        if self.picker.active:
            self.picker.confirm()

    def _cancel_pick_mode(self) -> None:
        if self.picker.active:
            self.picker.cancel()

    def request_pick_location(self) -> None:
        if self.macro_running:
            self.error_manager.report("Stop the macro before picking a location")
            return
        if self.picker.active:
            return

        self.status_var.set("Picking Location")
        try:
            self.root.withdraw()
        except Exception:
            pass
        try:
            self._show_pick_overlay()
        except Exception:
            pass
        self.picker.enter()

    def _on_location_confirmed(self, x: int, y: int) -> None:
        self.config.set("Location", "ClickX", x)
        self.config.set("Location", "ClickY", y)
        self.coord_var.set(f"({x}, {y})")
        self.status_var.set("Idle")
        self._hide_pick_overlay()
        try:
            self.root.deiconify()
            self.root.lift()
        except Exception:
            pass

    def _on_location_cancelled(self) -> None:
        self.status_var.set("Idle")
        self._hide_pick_overlay()
        try:
            self.root.deiconify()
            self.root.lift()
        except Exception:
            pass

    def request_start(self) -> None:
        if self.picker.active:
            return
        if self.macro_running:
            return

        cx = self.config.getint("Location", "ClickX", fallback=0)
        cy = self.config.getint("Location", "ClickY", fallback=0)
        if cx == 0 and cy == 0:
            self.error_manager.report("No location selected. Use Pick Location first.")
            return

        self.error_manager.clear()
        self._stop_event = threading.Event()
        self._rotation_counter = 0
        self._macro_thread = threading.Thread(target=self._run_macro, daemon=True)
        self._macro_thread.start()
        self.status_var.set("Running")
        self.logger.info("Macro start")

    def request_stop(self) -> None:
        if self.picker.active:
            self._hide_pick_overlay()
            self.picker.cancel()
        self._stop_event.set()
        if self.macro_running:
            self.status_var.set("Stopping")
        else:
            self.status_var.set("Idle")
        self.logger.info("Macro stop requested")

    def reset_config(self) -> None:
        if self.macro_running or self.picker.active:
            self.error_manager.report("Stop the macro and exit pick mode before resetting config")
            return
        try:
            self.config.reset_to_defaults()
        except Exception as e:
            self.error_manager.report("Failed to reset config", e, critical=True)
            return

        self._load_from_config()
        self._register_hotkeys()
        self.status_var.set("Idle")
        self.error_var.set("Config reset")
        try:
            self._refresh_chrome()
        except Exception:
            pass

    def _sleep(self, seconds: float) -> None:
        end = time.monotonic() + max(0.0, seconds)
        while time.monotonic() < end:
            if self._stop_event.is_set():
                return
            time.sleep(0.01)

    def _run_macro(self) -> None:
        try:
            target_loops = int(self.loop_count_var.get())
            while not self._stop_event.is_set():
                if target_loops > 0 and self._rotation_counter >= target_loops:
                    break

                cx = self.config.getint("Location", "ClickX", fallback=0)
                cy = self.config.getint("Location", "ClickY", fallback=0)

                radius = int(self.radius_var.get())
                spin_speed = int(self.spin_speed_var.get())
                move_speed = int(self.move_speed_var.get())
                step_delay = int(self.step_delay_var.get())
                clockwise = bool(self.clockwise_var.get())

                for angle, x, y in iter_circle_points(cx, cy, radius, spin_speed, clockwise):
                    if self._stop_event.is_set():
                        break
                    self.logger.trace(
                        "Circle step angle=%s radius=%s x=%s y=%s", angle, radius, x, y
                    )
                    self.autoit.mouse_move(x, y, move_speed)
                    self._sleep(step_delay / 1000.0)

                if self._stop_event.is_set():
                    break

                self._rotation_counter += 1

                click_every = max(1, int(self.center_click_every_var.get()))
                if self._rotation_counter % click_every == 0:
                    self._sleep(int(self.before_click_delay_var.get()) / 1000.0)
                    self.logger.action("Click center at (%s, %s)", cx, cy)
                    self.autoit.mouse_click(cx, cy)
                    self._sleep(int(self.after_click_delay_var.get()) / 1000.0)

                if self._stop_event.is_set():
                    break

                if bool(self.post_loop_key_enabled_var.get()):
                    key_send = key_name_to_autoit_send(self.post_loop_key_var.get())
                    self.logger.action("Post-loop key: %s", self.post_loop_key_var.get())
                    self.autoit.send_key(key_send)

                self._sleep(int(self.per_loop_delay_var.get()) / 1000.0)

        except AutoItBridgeError as e:
            self.error_manager.report("AutoIt error", e, critical=True)
        except Exception as e:
            self.error_manager.report("Macro error", e, critical=True)
        finally:
            self.root.after(0, self._macro_finished)

    def _macro_finished(self) -> None:
        self._stop_event.set()
        self.status_var.set("Idle")
        self.logger.info("Macro stopped")

    def _on_close(self) -> None:
        self._closing = True

        try:
            self._hide_pick_overlay()
        except Exception:
            pass

        after_ids: list[str] = []
        if self._after_chrome_id is not None:
            after_ids.append(self._after_chrome_id)
        if self._after_error_id is not None:
            after_ids.append(self._after_error_id)
        self._after_chrome_id = None
        self._after_error_id = None
        for aid in after_ids:
            try:
                self.root.after_cancel(aid)
            except Exception:
                pass

        try:
            if self.notebook is not None:
                idx = self.notebook.index(self.notebook.select())
                self.config.set("UI", "LastTab", idx)
        except Exception:
            pass

        try:
            if self.tabview is not None and _HAS_CTK and ctk is not None:
                current = self.tabview.get()
                names = ["Dashboard", "Movement", "Loops", "Hotkeys", "Debug"]
                idx = names.index(current) if current in names else 0
                self.config.set("UI", "LastTab", idx)
        except Exception:
            pass

        try:
            self.config.set("UI", "Geometry", self.root.geometry())
        except Exception:
            pass

        try:
            self.request_stop()
        except Exception:
            pass

        try:
            self.hotkeys.shutdown()
        except Exception:
            pass

        try:
            self.autoit.stop()
        except Exception:
            pass

        self.root.destroy()
