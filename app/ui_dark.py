import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import webbrowser

from .logger import set_logger_level


_BG = "#1f2024"
_CARD = "#2b2d33"
_CARD2 = "#30323a"
_BORDER = "#3b3e46"
_TEXT = "#e9e9ea"
_MUTED = "#c9c9cb"
_ACCENT = "#1f77d0"
_ACCENT_HOVER = "#2b86e0"
_PILL = "#3a3d45"

_TOS_VERSION = "1"
_DISCORD_INVITE_URL = "https://discord.com/invite/498tyUUaBw"


def _hex_to_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _blend(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


class RoundedPanel(tk.Canvas):
    def __init__(self, master, radius=26, bg=_CARD, border=_BORDER, padding=16, **kwargs):
        super().__init__(master, highlightthickness=0, bd=0, bg=_BG, **kwargs)
        self._radius = radius
        self._panel_bg = bg
        self._border = border
        self._padding = padding

        try:
            self.configure(splinesteps=24)
        except Exception:
            pass

        self._inner = tk.Frame(self, bg=bg)
        self._win = self.create_window(padding, padding, window=self._inner, anchor="nw")
        self.bind("<Configure>", self._on_configure)

    @property
    def inner(self) -> tk.Frame:
        return self._inner

    def _on_configure(self, _e=None):
        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())
        r = int(self._radius)
        p = int(self._padding)

        inner_w = max(1, w - p * 2)
        inner_h = max(1, h - p * 2)
        self.itemconfigure(self._win, width=inner_w, height=inner_h)
        self.coords(self._win, p, p)

        self.delete("bg")
        self._draw_rounded_rect(1, 1, w - 2, h - 2, r, fill=self._panel_bg, outline=self._border, width=1)

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, fill, outline, width):
        r = max(2, min(int(r), int((x2 - x1) / 2), int((y2 - y1) / 2)))
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        r2 = float(r * 2)

        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags="bg")
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags="bg")
        self.create_arc(x1, y1, x1 + r2, y1 + r2, start=90, extent=90, fill=fill, outline="", tags="bg")
        self.create_arc(x2 - r2, y1, x2, y1 + r2, start=0, extent=90, fill=fill, outline="", tags="bg")
        self.create_arc(x2 - r2, y2 - r2, x2, y2, start=270, extent=90, fill=fill, outline="", tags="bg")
        self.create_arc(x1, y2 - r2, x1 + r2, y2, start=180, extent=90, fill=fill, outline="", tags="bg")

        if outline:
            self.create_line(x1 + r, y1, x2 - r, y1, fill=outline, width=width, capstyle="round", tags="bg")
            self.create_line(x2, y1 + r, x2, y2 - r, fill=outline, width=width, capstyle="round", tags="bg")
            self.create_line(x1 + r, y2, x2 - r, y2, fill=outline, width=width, capstyle="round", tags="bg")
            self.create_line(x1, y1 + r, x1, y2 - r, fill=outline, width=width, capstyle="round", tags="bg")
            self.create_arc(x1, y1, x1 + r2, y1 + r2, start=90, extent=90, style="arc", outline=outline, width=width, tags="bg")
            self.create_arc(x2 - r2, y1, x2, y1 + r2, start=0, extent=90, style="arc", outline=outline, width=width, tags="bg")
            self.create_arc(x2 - r2, y2 - r2, x2, y2, start=270, extent=90, style="arc", outline=outline, width=width, tags="bg")
            self.create_arc(x1, y2 - r2, x1 + r2, y2, start=180, extent=90, style="arc", outline=outline, width=width, tags="bg")


class PillButton(tk.Canvas):
    def __init__(
        self,
        master,
        text,
        command,
        bg,
        fg=_TEXT,
        active_bg=None,
        active_fg=_TEXT,
        padx=16,
        pady=6,
        font=("Segoe UI", 10),
    ):
        self._text = str(text)
        self._command = command
        self._normal_bg = bg
        self._active_bg = active_bg or bg
        self._fg = fg
        self._active_fg = active_fg
        self._padx = int(padx)
        self._pady = int(pady)
        self._font = font
        self._is_active = False
        self._is_hover = False
        self._is_pressed = False

        try:
            canvas_bg = master.cget("bg")
        except Exception:
            canvas_bg = _BG

        super().__init__(
            master,
            highlightthickness=0,
            bd=0,
            bg=canvas_bg,
            cursor="hand2",
        )

        try:
            self.configure(splinesteps=24)
        except Exception:
            pass

        f = tkfont.Font(font=self._font)
        tw = max(1, int(f.measure(self._text)))
        th = max(1, int(f.metrics("linespace")))
        self._btn_w = tw + self._padx * 2
        self._btn_h = th + self._pady * 2
        self.configure(width=self._btn_w, height=self._btn_h)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

        self._redraw()

    def set_active(self, active: bool):
        self._is_active = bool(active)
        self._redraw()

    def _base_bg(self) -> str:
        return self._active_bg if self._is_active else self._normal_bg

    def _current_bg(self) -> str:
        c = self._base_bg()
        if self._is_hover and not self._is_pressed:
            c = _blend(c, "#ffffff", 0.08)
        if self._is_pressed:
            return _blend(c, "#000000", 0.12)
        return c

    def _current_fg(self) -> str:
        return self._active_fg if self._is_active else self._fg

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, fill, outline="", width=1, tag=None):
        r = max(2, min(int(r), int((x2 - x1) / 2), int((y2 - y1) / 2)))
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        r2 = float(r * 2)
        tag = tag or ""

        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags=tag)
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags=tag)
        self.create_arc(x1, y1, x1 + r2, y1 + r2, start=90, extent=90, fill=fill, outline="", tags=tag)
        self.create_arc(x2 - r2, y1, x2, y1 + r2, start=0, extent=90, fill=fill, outline="", tags=tag)
        self.create_arc(x2 - r2, y2 - r2, x2, y2, start=270, extent=90, fill=fill, outline="", tags=tag)
        self.create_arc(x1, y2 - r2, x1 + r2, y2, start=180, extent=90, fill=fill, outline="", tags=tag)

        if outline:
            self.create_line(x1 + r, y1, x2 - r, y1, fill=outline, width=width, capstyle="round", tags=tag)
            self.create_line(x2, y1 + r, x2, y2 - r, fill=outline, width=width, capstyle="round", tags=tag)
            self.create_line(x1 + r, y2, x2 - r, y2, fill=outline, width=width, capstyle="round", tags=tag)
            self.create_line(x1, y1 + r, x1, y2 - r, fill=outline, width=width, capstyle="round", tags=tag)
            self.create_arc(x1, y1, x1 + r2, y1 + r2, start=90, extent=90, style="arc", outline=outline, width=width, tags=tag)
            self.create_arc(x2 - r2, y1, x2, y1 + r2, start=0, extent=90, style="arc", outline=outline, width=width, tags=tag)
            self.create_arc(x2 - r2, y2 - r2, x2, y2, start=270, extent=90, style="arc", outline=outline, width=width, tags=tag)
            self.create_arc(x1, y2 - r2, x1 + r2, y2, start=180, extent=90, style="arc", outline=outline, width=width, tags=tag)

    def _redraw(self):
        self.delete("all")
        r = max(10, int(self._btn_h / 2))
        fill = self._current_bg()

        shadow = _blend(fill, "#000000", 0.35)
        self._draw_rounded_rect(2, 2, self._btn_w - 1, self._btn_h - 1, r, fill=shadow, tag="shadow")

        border = _blend(fill, "#000000", 0.28)
        if self._is_active:
            border = _blend(fill, "#ffffff", 0.22)
        self._draw_rounded_rect(1, 1, self._btn_w - 2, self._btn_h - 2, r, fill=fill, outline=border, width=1, tag="bg")

        self.create_text(
            int(self._btn_w / 2),
            int(self._btn_h / 2) + (1 if self._is_pressed else 0),
            text=self._text,
            fill=self._current_fg(),
            font=self._font,
        )

    def _on_enter(self, _e=None):
        self._is_hover = True
        self._redraw()

    def _on_leave(self, _e=None):
        self._is_pressed = False
        self._is_hover = False
        self._redraw()

    def _on_press(self, _e=None):
        self._is_pressed = True
        self._redraw()

    def _on_release(self, e=None):
        self._is_pressed = False
        self._redraw()
        if self._command is None:
            return
        try:
            x = int(getattr(e, "x", -1))
            y = int(getattr(e, "y", -1))
        except Exception:
            x, y = -1, -1
        if 0 <= x <= self._btn_w and 0 <= y <= self._btn_h:
            try:
                self._command()
            except Exception:
                pass


class PrimaryButton(PillButton):
    def __init__(self, master, text, command):
        super().__init__(master, text=text, command=command, bg=_ACCENT, active_bg=_ACCENT_HOVER, padx=18, pady=8)


class SecondaryButton(PillButton):
    def __init__(self, master, text, command):
        super().__init__(master, text=text, command=command, bg=_PILL, active_bg=_blend(_PILL, "#ffffff", 0.08), padx=18, pady=8)


class LabeledRow(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=_CARD)


class AppUIDark:
    def __init__(
        self,
        root: tk.Tk,
        config,
        logger,
        error_handler,
        macro_engine,
        picker,
        hotkeys,
    ):
        self.root = root
        self._config = config
        self._logger = logger
        self._error_handler = error_handler
        self._macro = macro_engine
        self._picker = picker
        self._hotkeys = hotkeys

        self._debounce_jobs = {}
        self._did_init_load = False

        self._status_var = tk.StringVar(value="STOPPED")
        self._error_var = tk.StringVar(value="")
        self._coord_var = tk.StringVar(value="(0, 0)")

        self._init_window()
        self._init_ttk_style()

        if not self._ensure_terms_accepted():
            try:
                self.root.after(0, self.root.destroy)
            except Exception:
                pass
            return

        self._build()
        self._load_from_config()

        self._maybe_prompt_discord()

        self._picker._on_status = self._set_status
        self._macro._on_status = self._set_status

        self._hotkeys.set_callbacks(
            on_start=self.on_start,
            on_stop=self.on_stop,
            on_confirm=self._on_confirm_hotkey,
            on_esc=self._on_esc_hotkey,
        )
        self._hotkeys.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _ensure_terms_accepted(self) -> bool:
        accepted = self._config.get_int("Legal", "TOSAccepted", 0)
        version = self._config.get("Legal", "TOSVersion", "")
        if accepted == 1 and version == _TOS_VERSION:
            return True

        tos_text = (
            "TERMS OF SERVICE\n\n"
            "By using this software, you agree to the following terms:\n\n"
            "1) Use at your own risk. This tool automates mouse/keyboard input.\n"
            "2) You are responsible for compliance with any game/platform rules.\n"
            "3) No warranty. The software is provided 'as is' without warranty of any kind.\n"
            "4) Ownership/Attribution: This project is owned by the author.\n"
            "   Do not redistribute or re-upload without proper credit/attribution.\n"
            "5) Unauthorized redistribution may result in DMCA takedown requests.\n\n"
            "If you do not agree, click Decline to exit.\n"
        )

        win = tk.Toplevel(self.root)
        win.title("Terms of Service")
        win.configure(bg=_BG)
        win.resizable(True, True)

        try:
            win.transient(self.root)
        except Exception:
            pass

        container = RoundedPanel(win, radius=20, bg=_CARD, border=_CARD, padding=16)
        container.pack(fill="both", expand=True, padx=18, pady=18)
        inner = container.inner
        inner.columnconfigure(0, weight=1)
        inner.rowconfigure(1, weight=1)

        title = tk.Label(inner, text="Terms of Service", bg=_CARD, fg=_TEXT, font=("Segoe UI", 12, "bold"))
        title.grid(row=0, column=0, sticky="w")

        body_frame = tk.Frame(inner, bg=_CARD)
        body_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 12))
        body_frame.columnconfigure(0, weight=1)
        body_frame.rowconfigure(0, weight=1)

        scroll = tk.Scrollbar(body_frame)
        scroll.grid(row=0, column=1, sticky="ns")

        text = tk.Text(
            body_frame,
            wrap="word",
            height=14,
            bg=_CARD2,
            fg=_TEXT,
            insertbackground=_TEXT,
            relief="flat",
            highlightthickness=0,
            yscrollcommand=scroll.set,
        )
        text.grid(row=0, column=0, sticky="nsew")
        scroll.config(command=text.yview)

        try:
            text.insert("1.0", tos_text)
            text.configure(state="disabled")
        except Exception:
            pass

        btn_row = tk.Frame(inner, bg=_CARD)
        btn_row.grid(row=2, column=0, sticky="e")

        result = {"accepted": False}

        def accept():
            result["accepted"] = True
            try:
                self._config.set("Legal", "TOSAccepted", 1)
                self._config.set("Legal", "TOSVersion", _TOS_VERSION)
            except Exception:
                pass
            try:
                win.destroy()
            except Exception:
                pass

        def decline():
            result["accepted"] = False
            try:
                win.destroy()
            except Exception:
                pass

        PrimaryButton(btn_row, "I Agree", accept).pack(side="left", padx=(0, 12))
        SecondaryButton(btn_row, "Decline", decline).pack(side="left")

        try:
            win.protocol("WM_DELETE_WINDOW", decline)
        except Exception:
            pass

        try:
            win.grab_set()
        except Exception:
            pass

        try:
            win.update_idletasks()
            w = max(640, int(self.root.winfo_width() * 0.75))
            h = max(420, int(self.root.winfo_height() * 0.70))
            win.geometry(f"{w}x{h}")
        except Exception:
            pass

        try:
            self.root.wait_window(win)
        except Exception:
            return False

        return bool(result["accepted"])

    def _maybe_prompt_discord(self) -> None:
        prompted = self._config.get_int("Legal", "DiscordPrompted", 0)
        if prompted == 1:
            return
        try:
            self._config.set("Legal", "DiscordPrompted", 1)
        except Exception:
            pass

        try:
            join = messagebox.askyesno(
                "Join our Discord?",
                "Want to join the Discord server for updates/support?\n\nOpen invite link in your browser?",
                parent=self.root,
            )
        except Exception:
            join = False

        if not join:
            return
        try:
            webbrowser.open(_DISCORD_INVITE_URL)
        except Exception:
            pass

    def set_error(self, msg: str):
        self._error_var.set(msg or "")

    def _init_window(self):
        self.root.title("Rivals AFK Macro")
        self.root.configure(bg=_BG)
        self.root.minsize(900, 560)

        geo = self._config.get("UI", "Geometry", "")
        if geo:
            try:
                self.root.geometry(geo)
            except Exception:
                pass

    def _init_ttk_style(self) -> None:
        try:
            style = ttk.Style()
            try:
                if "clam" in style.theme_names():
                    style.theme_use("clam")
            except Exception:
                pass

            style.configure(
                "Dark.TCombobox",
                fieldbackground=_CARD2,
                background=_CARD2,
                foreground=_TEXT,
                arrowcolor=_TEXT,
                bordercolor=_BORDER,
                lightcolor=_BORDER,
                darkcolor=_BORDER,
                relief="flat",
                padding=6,
            )
            style.map(
                "Dark.TCombobox",
                fieldbackground=[("readonly", _CARD2), ("disabled", _CARD)],
                foreground=[("disabled", _blend(_TEXT, _CARD2, 0.55))],
                background=[("active", _CARD2), ("readonly", _CARD2)],
            )

            style.configure(
                "Dark.Horizontal.TScale",
                background=_CARD,
                troughcolor=_CARD2,
            )

            try:
                self.root.option_add("*TCombobox*Listbox.background", _CARD2)
                self.root.option_add("*TCombobox*Listbox.foreground", _TEXT)
                self.root.option_add("*TCombobox*Listbox.selectBackground", _ACCENT)
                self.root.option_add("*TCombobox*Listbox.selectForeground", _TEXT)
            except Exception:
                pass
        except Exception:
            pass

    def _build(self):
        outer = tk.Frame(self.root, bg=_BG)
        outer.pack(fill="both", expand=True, padx=18, pady=18)

        self._header = RoundedPanel(outer, radius=28, bg=_CARD2, border=_CARD2, padding=18, height=90)
        self._header.pack(fill="x")

        header_in = self._header.inner
        header_in.columnconfigure(0, weight=1)

        self._status_label = tk.Label(
            header_in,
            textvariable=self._status_var,
            bg=_CARD2,
            fg=_TEXT,
            font=("Segoe UI", 11, "bold"),
        )
        self._status_label.grid(row=0, column=0, sticky="w")

        self._sub_label = tk.Label(
            header_in,
            textvariable=self._error_var,
            bg=_CARD2,
            fg=_blend(_TEXT, _CARD2, 0.4),
            font=("Segoe UI", 9),
        )
        self._sub_label.grid(row=1, column=0, sticky="w", pady=(6, 0))

        btn_row = tk.Frame(header_in, bg=_CARD2)
        btn_row.grid(row=0, column=1, rowspan=2, sticky="e")

        PrimaryButton(btn_row, "Start", self.on_start).pack(side="left", padx=(0, 12))
        SecondaryButton(btn_row, "Stop", self.on_stop).pack(side="left", padx=(0, 12))
        SecondaryButton(btn_row, "Pick Location", self.on_pick_location).pack(side="left")

        self._tabs_row = tk.Frame(outer, bg=_BG)
        self._tabs_row.pack(fill="x", pady=(18, 12))

        self._tabs_inner = tk.Frame(self._tabs_row, bg=_BG)
        self._tabs_inner.pack(anchor="center")

        self._content = RoundedPanel(outer, radius=28, bg=_CARD, border=_CARD, padding=18)
        self._content.pack(fill="both", expand=True)

        self._content_in = self._content.inner
        self._content_in.configure(bg=_CARD)

        self._tab_buttons = {}
        self._tab_frames = {}
        self._active_tab = None

        tab_names = [
            ("Main", "Main"),
            ("Movement", "Movement & Clicking"),
            ("Loops", "Loops & Actions"),
            ("Hotkeys", "Hotkeys"),
            ("Debug", "Debug / Advanced"),
        ]

        for key, label in tab_names:
            btn = PillButton(
                self._tabs_inner,
                text=label,
                command=lambda k=key: self._select_tab(k),
                bg=_PILL,
                active_bg=_ACCENT,
                padx=16,
                pady=7,
                font=("Segoe UI", 10),
            )
            btn.pack(side="left", padx=6)
            self._tab_buttons[key] = btn

            frame = tk.Frame(self._content_in, bg=_CARD)
            self._tab_frames[key] = frame

        self._build_main_tab(self._tab_frames["Main"])
        self._build_movement_tab(self._tab_frames["Movement"])
        self._build_loops_tab(self._tab_frames["Loops"])
        self._build_hotkeys_tab(self._tab_frames["Hotkeys"])
        self._build_debug_tab(self._tab_frames["Debug"])

        self._select_tab("Main")

    def _select_tab(self, key: str):
        if self._active_tab == key:
            return
        if self._active_tab in self._tab_frames:
            self._tab_frames[self._active_tab].pack_forget()

        self._active_tab = key
        for k, b in self._tab_buttons.items():
            b.set_active(k == key)

        frame = self._tab_frames[key]
        frame.pack(fill="both", expand=True)

        index_map = {"Main": 0, "Movement": 1, "Loops": 2, "Hotkeys": 3, "Debug": 4}
        self._config.set("UI", "LastTab", index_map.get(key, 0))

    def _build_main_tab(self, parent: tk.Frame):
        title = tk.Label(parent, text="Main", bg=_CARD, fg=_TEXT, font=("Segoe UI", 14, "bold"))
        title.pack(anchor="w")

        info = tk.Label(
            parent,
            text="Pick Location then press F8 to confirm. Start=F6 Stop=F7. ESC cancels pick mode.",
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 10),
        )
        info.pack(anchor="w", pady=(8, 0))

        row = tk.Frame(parent, bg=_CARD)
        row.pack(fill="x", pady=(18, 0))

        tk.Label(row, text="Selected Coordinates:", bg=_CARD, fg=_TEXT, font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Label(row, textvariable=self._coord_var, bg=_CARD, fg=_MUTED, font=("Segoe UI", 11)).pack(side="left", padx=(12, 0))

    def _build_movement_tab(self, parent: tk.Frame):
        title = tk.Label(parent, text="Movement & Clicking", bg=_CARD, fg=_TEXT, font=("Segoe UI", 14, "bold"))
        title.pack(anchor="w")

        self._radius_var = tk.DoubleVar(value=25)
        self._spin_var = tk.DoubleVar(value=15)
        self._move_speed_var = tk.DoubleVar(value=10)
        self._step_delay_var = tk.DoubleVar(value=20)
        self._before_click_var = tk.DoubleVar(value=0)
        self._after_click_var = tk.DoubleVar(value=0)
        self._click_every_rot_var = tk.DoubleVar(value=1)
        self._click_every_ms_var = tk.DoubleVar(value=0)
        self._direction_var = tk.StringVar(value="clockwise")
        self._click_button_var = tk.StringVar(value="left")
        self._click_count_var = tk.DoubleVar(value=1)
        self._click_speed_var = tk.DoubleVar(value=0)

        grid = tk.Frame(parent, bg=_CARD)
        grid.pack(fill="both", expand=True, pady=(14, 0))

        self._slider(grid, "Circle radius", self._radius_var, 0, 250, "Movement", "Radius")
        self._slider(grid, "Spin step (deg)", self._spin_var, 1, 60, "Movement", "SpinStepDeg")
        self._slider(grid, "Mouse move speed", self._move_speed_var, 0, 100, "Movement", "MoveSpeed")
        self._slider(grid, "Step delay (ms)", self._step_delay_var, 0, 500, "Delays", "StepDelayMs")
        self._slider(grid, "Before click (ms)", self._before_click_var, 0, 2000, "Delays", "BeforeClickMs")
        self._slider(grid, "After click (ms)", self._after_click_var, 0, 2000, "Delays", "AfterClickMs")
        self._slider(grid, "Click every rotations", self._click_every_rot_var, 0, 50, "Click", "CenterClickEveryRotations")
        self._slider(grid, "Click every ms", self._click_every_ms_var, 0, 30000, "Click", "CenterClickEveryMs")
        self._dropdown(grid, "Direction", self._direction_var, ["clockwise", "counter-clockwise"], "Movement", "Direction")
        self._dropdown(grid, "Click button", self._click_button_var, ["left", "right", "middle"], "Click", "ClickButton")
        self._slider(grid, "Click count", self._click_count_var, 1, 5, "Click", "ClickCount")
        self._slider(grid, "Click speed", self._click_speed_var, 0, 100, "Click", "ClickSpeed")

    def _build_loops_tab(self, parent: tk.Frame):
        title = tk.Label(parent, text="Loops & Actions", bg=_CARD, fg=_TEXT, font=("Segoe UI", 14, "bold"))
        title.pack(anchor="w")

        self._loop_count_var = tk.StringVar(value="0")
        self._per_loop_delay_var = tk.DoubleVar(value=0)
        self._post_loop_enabled_var = tk.IntVar(value=0)
        self._post_loop_key_var = tk.StringVar(value="SPACE")

        body = tk.Frame(parent, bg=_CARD)
        body.pack(fill="both", expand=True, pady=(14, 0))

        self._entry(body, "Loop count (0=infinite)", self._loop_count_var, "Loops", "Count", cast="int")
        self._slider(body, "Per-loop delay (ms)", self._per_loop_delay_var, 0, 30000, "Delays", "PerLoopDelayMs")

        row = tk.Frame(body, bg=_CARD)
        row.pack(fill="x", pady=(12, 0))

        chk = tk.Checkbutton(
            row,
            text="Post-loop key press",
            variable=self._post_loop_enabled_var,
            command=lambda: self._config.set("Actions", "PostLoopEnabled", int(self._post_loop_enabled_var.get())),
            bg=_CARD,
            fg=_TEXT,
            activebackground=_CARD,
            activeforeground=_TEXT,
            selectcolor=_CARD2,
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        chk.pack(side="left")

        tk.Label(row, text="Key:", bg=_CARD, fg=_MUTED, font=("Segoe UI", 10)).pack(side="left", padx=(14, 8))

        keys = _key_choices()
        self._dropdown(row, "", self._post_loop_key_var, keys, "Actions", "PostLoopKey", inline=True)

    def _build_hotkeys_tab(self, parent: tk.Frame):
        title = tk.Label(parent, text="Hotkeys", bg=_CARD, fg=_TEXT, font=("Segoe UI", 14, "bold"))
        title.pack(anchor="w")

        self._hk_start_var = tk.StringVar(value="F6")
        self._hk_stop_var = tk.StringVar(value="F7")
        self._hk_confirm_var = tk.StringVar(value="F8")

        body = tk.Frame(parent, bg=_CARD)
        body.pack(fill="both", expand=True, pady=(14, 0))

        keys = _hotkey_choices()
        self._dropdown(body, "Start hotkey", self._hk_start_var, keys, "Hotkeys", "Start")
        self._dropdown(body, "Stop hotkey", self._hk_stop_var, keys, "Hotkeys", "Stop")
        self._dropdown(body, "Confirm-location hotkey", self._hk_confirm_var, keys, "Hotkeys", "ConfirmLocation")

        tk.Label(body, text="Hotkeys apply instantly.", bg=_CARD, fg=_MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 0))

    def _build_debug_tab(self, parent: tk.Frame):
        title = tk.Label(parent, text="Debug / Advanced", bg=_CARD, fg=_TEXT, font=("Segoe UI", 14, "bold"))
        title.pack(anchor="w")

        self._debug_level_var = tk.StringVar(value="INFO")

        body = tk.Frame(parent, bg=_CARD)
        body.pack(fill="both", expand=True, pady=(14, 0))

        self._dropdown(body, "Debug level", self._debug_level_var, ["INFO", "ACTION", "WARNING", "ERROR", "TRACE"], "Debug", "Level")

        tk.Label(body, text="Logs saved to logs/debug.log", bg=_CARD, fg=_MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 0))

    def _slider(self, parent, label, var, min_val, max_val, section, option):
        row = tk.Frame(parent, bg=_CARD)
        row.pack(fill="x", pady=6)

        tk.Label(row, text=label, bg=_CARD, fg=_TEXT, width=22, anchor="w", font=("Segoe UI", 10)).pack(side="left")

        value_lbl = tk.Label(row, text="0", bg=_CARD, fg=_MUTED, width=6, anchor="e", font=("Segoe UI", 10))
        value_lbl.pack(side="right")

        scale = ttk.Scale(
            row,
            from_=min_val,
            to=max_val,
            orient="horizontal",
            variable=var,
            style="Dark.Horizontal.TScale",
        )
        scale.pack(side="left", fill="x", expand=True, padx=(12, 12))

        def commit(value: int):
            if not self._did_init_load:
                return
            try:
                self._config.set(section, option, value)
            except Exception:
                pass

        def on_change(*_args):
            try:
                v = int(float(var.get()))
            except Exception:
                v = 0
            value_lbl.configure(text=str(v))
            if self._did_init_load:
                key = ("slider", section, option)
                job = self._debounce_jobs.get(key)
                if job is not None:
                    try:
                        self.root.after_cancel(job)
                    except Exception:
                        pass
                self._debounce_jobs[key] = self.root.after(150, lambda vv=v: commit(vv))

        var.trace_add("write", on_change)
        on_change()

    def _entry(self, parent, label, var, section, option, cast="str"):
        row = tk.Frame(parent, bg=_CARD)
        row.pack(fill="x", pady=6)

        tk.Label(row, text=label, bg=_CARD, fg=_TEXT, width=22, anchor="w", font=("Segoe UI", 10)).pack(side="left")

        entry = tk.Entry(
            row,
            textvariable=var,
            bg=_CARD2,
            fg=_TEXT,
            insertbackground=_TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=_BORDER,
            highlightcolor=_ACCENT,
            width=14,
            font=("Segoe UI", 10),
        )
        entry.pack(side="left", padx=(12, 0))

        def commit():
            if not self._did_init_load:
                return
            raw = var.get()
            try:
                if cast == "int":
                    value = int(str(raw).strip())
                else:
                    value = str(raw)
                self._config.set(section, option, value)
            except Exception:
                pass

        def on_var_change(*_args):
            if not self._did_init_load:
                return
            key = (section, option)
            job = self._debounce_jobs.get(key)
            if job is not None:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
            self._debounce_jobs[key] = self.root.after(350, commit)

        var.trace_add("write", on_var_change)
        entry.bind("<FocusOut>", lambda _e: commit())
        entry.bind("<Return>", lambda _e: commit())

    def _dropdown(self, parent, label, var, values, section, option, inline=False):
        row = parent if inline else tk.Frame(parent, bg=_CARD)
        if not inline:
            row.pack(fill="x", pady=6)

        if label:
            tk.Label(row, text=label, bg=_CARD, fg=_TEXT, width=22, anchor="w", font=("Segoe UI", 10)).pack(side="left")

        opt = ttk.Combobox(
            row,
            textvariable=var,
            values=list(values),
            state="readonly",
            style="Dark.TCombobox",
            width=18,
        )

        if inline:
            opt.pack(side="left")
        else:
            opt.pack(side="left", padx=(12, 0))

        def on_change(*_args):
            if not self._did_init_load:
                return
            self._config.set(section, option, var.get())
            if section == "Hotkeys":
                self._apply_hotkeys()
            if section == "Debug" and option == "Level":
                try:
                    set_logger_level(self._logger, var.get())
                except Exception:
                    pass

        var.trace_add("write", on_change)

    def _load_from_config(self):
        self._did_init_load = False

        x = self._config.get_int("Click", "ClickX", 0)
        y = self._config.get_int("Click", "ClickY", 0)
        self._coord_var.set(f"({x}, {y})")

        last_tab = self._config.get_int("UI", "LastTab", 0)
        idx_to_key = {0: "Main", 1: "Movement", 2: "Loops", 3: "Hotkeys", 4: "Debug"}
        self._select_tab(idx_to_key.get(last_tab, "Main"))

        try:
            self._radius_var.set(self._config.get_int("Movement", "Radius", 25))
            self._spin_var.set(self._config.get_int("Movement", "SpinStepDeg", 15))
            self._move_speed_var.set(self._config.get_int("Movement", "MoveSpeed", 10))
            self._direction_var.set(self._config.get("Movement", "Direction", "clockwise"))

            self._step_delay_var.set(self._config.get_int("Delays", "StepDelayMs", 20))
            self._before_click_var.set(self._config.get_int("Delays", "BeforeClickMs", 0))
            self._after_click_var.set(self._config.get_int("Delays", "AfterClickMs", 0))
            self._per_loop_delay_var.set(self._config.get_int("Delays", "PerLoopDelayMs", 0))

            self._click_every_rot_var.set(self._config.get_int("Click", "CenterClickEveryRotations", 1))
            self._click_every_ms_var.set(self._config.get_int("Click", "CenterClickEveryMs", 0))
            self._click_button_var.set(self._config.get("Click", "ClickButton", "left"))
            self._click_count_var.set(self._config.get_int("Click", "ClickCount", 1))
            self._click_speed_var.set(self._config.get_int("Click", "ClickSpeed", 0))

            self._loop_count_var.set(str(self._config.get_int("Loops", "Count", 0)))
            self._post_loop_enabled_var.set(self._config.get_int("Actions", "PostLoopEnabled", 0))
            self._post_loop_key_var.set(self._config.get("Actions", "PostLoopKey", "SPACE"))

            self._hk_start_var.set(self._config.get("Hotkeys", "Start", "F6"))
            self._hk_stop_var.set(self._config.get("Hotkeys", "Stop", "F7"))
            self._hk_confirm_var.set(self._config.get("Hotkeys", "ConfirmLocation", "F8"))

            self._debug_level_var.set(self._config.get("Debug", "Level", "INFO"))
        except Exception:
            pass

        self._did_init_load = True
        self._apply_hotkeys()

    def _apply_hotkeys(self):
        self._config.set("Hotkeys", "Start", self._hk_start_var.get())
        self._config.set("Hotkeys", "Stop", self._hk_stop_var.get())
        self._config.set("Hotkeys", "ConfirmLocation", self._hk_confirm_var.get())
        self._hotkeys.reload()

    def _set_status(self, status: str):
        if status == "Running":
            self._status_var.set("Status: RUNNING")
        elif status == "Picking Location":
            self._status_var.set("Status: PICKING LOCATION")
        else:
            self._status_var.set("Status: STOPPED")

    def on_start(self):
        if self._picker.is_active:
            return
        x = self._config.get_int("Click", "ClickX", 0)
        y = self._config.get_int("Click", "ClickY", 0)
        if x == 0 and y == 0:
            self._error_var.set("Pick Location first (press F8 to confirm).")
            return
        self._error_var.set("")
        self._macro.start()

    def on_stop(self):
        self._macro.stop()

    def on_pick_location(self):
        if self._macro.is_running:
            self._error_var.set("Stop the macro before picking a new location.")
            return

        hint = {"win": None}

        def _close_hint():
            w = hint.get("win")
            if w is None:
                return
            try:
                w.destroy()
            except Exception:
                pass
            hint["win"] = None

        def on_hide():
            try:
                self.root.withdraw()
            except Exception:
                pass

        def on_show():
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass

        def on_picked(x, y):
            self._coord_var.set(f"({x}, {y})")
            _close_hint()

        def on_cancelled():
            _close_hint()

        if self._error_handler:
            self._error_handler.safe_call(
                "Picker.begin",
                self._picker.begin,
                on_picked,
                on_cancelled,
                on_hide,
                on_show,
            )
        else:
            self._picker.begin(on_picked=on_picked, on_cancelled=on_cancelled, on_hide_ui=on_hide, on_show_ui=on_show)

        if not self._picker.is_active:
            return

        try:
            win = tk.Toplevel(self.root)
            hint["win"] = win
            win.title("Pick Location")
            win.configure(bg=_BG)
            win.resizable(False, False)

            try:
                win.attributes("-topmost", True)
            except Exception:
                pass

            container = RoundedPanel(win, radius=20, bg=_CARD, border=_CARD, padding=16)
            container.pack(fill="both", expand=True, padx=16, pady=16)
            inner = container.inner

            tk.Label(
                inner,
                text="Pick Mode Active",
                bg=_CARD,
                fg=_TEXT,
                font=("Segoe UI", 12, "bold"),
            ).pack(anchor="w")

            tk.Label(
                inner,
                text="Move your mouse to the spot in-game.\n\nPress F8 to confirm or ESC to cancel.\n\nIf hotkeys don't work, use the buttons below.",
                bg=_CARD,
                fg=_MUTED,
                justify="left",
                font=("Segoe UI", 10),
            ).pack(anchor="w", pady=(10, 0))

            btn_row = tk.Frame(inner, bg=_CARD)
            btn_row.pack(anchor="e", pady=(14, 0), fill="x")

            PrimaryButton(btn_row, "Confirm", lambda: self._picker.confirm()).pack(side="left", padx=(0, 12))
            SecondaryButton(btn_row, "Cancel", lambda: self._picker.cancel()).pack(side="left")

            try:
                win.protocol("WM_DELETE_WINDOW", lambda: self._picker.cancel())
            except Exception:
                pass

            try:
                win.update_idletasks()
                sw = win.winfo_screenwidth()
                sh = win.winfo_screenheight()
                w = max(420, win.winfo_width())
                h = max(230, win.winfo_height())
                win.geometry(f"{w}x{h}+{int((sw - w) / 2)}+{int((sh - h) * 0.12)}")
            except Exception:
                pass
        except Exception as exc:
            if self._error_handler:
                self._error_handler.report("Pick hint window", exc)

    def _on_confirm_hotkey(self):
        if self._picker.is_active:
            self._picker.confirm()

    def _on_esc_hotkey(self):
        if self._picker.is_active:
            self._picker.cancel()
        else:
            self._macro.stop()

    def on_close(self):
        try:
            self._config.set("UI", "Geometry", self.root.geometry())
        except Exception:
            pass

        try:
            self._hotkeys.stop()
        except Exception:
            pass

        try:
            for _k, job in list(self._debounce_jobs.items()):
                if job is not None:
                    try:
                        self.root.after_cancel(job)
                    except Exception:
                        pass
            self._debounce_jobs.clear()
        except Exception:
            pass

        try:
            if self._picker.is_active:
                try:
                    self._picker.cancel()
                except Exception:
                    pass
        except Exception:
            pass

        try:
            self._macro.stop(wait=True)
        except Exception:
            pass

        self.root.destroy()


def _hotkey_choices():
    base = [f"F{i}" for i in range(1, 13)]
    base += ["ESC", "TAB", "SPACE", "ENTER"]
    return base


def _key_choices():
    letters = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    nums = [str(i) for i in range(0, 10)]
    fkeys = [f"F{i}" for i in range(1, 13)]
    special = ["SPACE", "ENTER", "SHIFT", "CTRL", "ALT", "TAB", "ESC", "UP", "DOWN", "LEFT", "RIGHT"]
    return letters + nums + fkeys + special
