import tkinter as tk
from tkinter import ttk

from .logger import set_logger_level


class AppUI:
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

        self._status_var = tk.StringVar(value="Idle")
        self._error_var = tk.StringVar(value="")
        self._coord_var = tk.StringVar(value="(0, 0)")

        self._debounce_jobs = {}

        self._init_window()
        self._build()
        self._load_from_config()

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

    def schedule_ui(self, fn):
        self.root.after(0, fn)

    def set_error(self, msg: str):
        self._error_var.set(msg)

    def _init_window(self):
        self.root.title("Rivals AFK Macro (GL)")
        geo = self._config.get("UI", "Geometry", "")
        if geo:
            try:
                self.root.geometry(geo)
            except Exception:
                pass

        self.root.minsize(620, 420)

        try:
            import tkinter.font as tkfont

            default_font = tkfont.nametofont("TkDefaultFont")
            default_font.configure(size=10)
            self.root.option_add("*Font", default_font)
        except Exception:
            pass

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        try:
            style.configure("TButton", padding=(14, 8))
            style.configure("TNotebook.Tab", padding=(14, 8))
            style.configure("TFrame", background="#f6f7fb")
            style.configure("TLabel", background="#f6f7fb")
            style.configure("TLabelframe", background="#f6f7fb")
            style.configure("TLabelframe.Label", background="#f6f7fb")
        except Exception:
            pass

    def _build(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")

        ttk.Label(header, text="Status:").pack(side="left")
        ttk.Label(header, textvariable=self._status_var).pack(side="left", padx=(6, 0))

        ttk.Label(header, text="Error:").pack(side="left", padx=(18, 0))
        ttk.Label(header, textvariable=self._error_var).pack(side="left", padx=(6, 0))

        self._notebook = ttk.Notebook(outer)
        self._notebook.pack(fill="both", expand=True, pady=(12, 0))
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._tab_main = ttk.Frame(self._notebook, padding=12)
        self._tab_move = ttk.Frame(self._notebook, padding=12)
        self._tab_loops = ttk.Frame(self._notebook, padding=12)
        self._tab_hotkeys = ttk.Frame(self._notebook, padding=12)
        self._tab_debug = ttk.Frame(self._notebook, padding=12)

        self._notebook.add(self._tab_main, text="Main")
        self._notebook.add(self._tab_move, text="Movement & Clicking")
        self._notebook.add(self._tab_loops, text="Loops & Actions")
        self._notebook.add(self._tab_hotkeys, text="Hotkeys")
        self._notebook.add(self._tab_debug, text="Debug / Advanced")

        self._build_tab_main()
        self._build_tab_move()
        self._build_tab_loops()
        self._build_tab_hotkeys()
        self._build_tab_debug()

        self._did_init_load = False

    def _build_tab_main(self):
        row = ttk.Frame(self._tab_main)
        row.pack(fill="x")

        self._btn_start = ttk.Button(row, text="Start", command=self.on_start)
        self._btn_stop = ttk.Button(row, text="Stop", command=self.on_stop)
        self._btn_pick = ttk.Button(row, text="Pick Location", command=self.on_pick_location)

        self._btn_start.pack(side="left", padx=(0, 8))
        self._btn_stop.pack(side="left", padx=(0, 8))
        self._btn_pick.pack(side="left")

        coords = ttk.Frame(self._tab_main)
        coords.pack(fill="x", pady=(16, 0))

        ttk.Label(coords, text="Selected Coordinates:").pack(side="left")
        ttk.Label(coords, textvariable=self._coord_var).pack(side="left", padx=(8, 0))

        hint = ttk.Frame(self._tab_main)
        hint.pack(fill="x", pady=(16, 0))

        ttk.Label(
            hint,
            text="Hotkeys: Start=F6 Stop=F7 Confirm=F8 (editable in Hotkeys tab). ESC cancels pick mode.",
        ).pack(anchor="w")

    def _build_tab_move(self):
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

        grid = ttk.Frame(self._tab_move)
        grid.pack(fill="both", expand=True)

        self._add_scale_row(grid, 0, "Circle radius", self._radius_var, 0, 250, "Movement", "Radius")
        self._add_scale_row(grid, 1, "Spin step (deg)", self._spin_var, 1, 60, "Movement", "SpinStepDeg")
        self._add_scale_row(grid, 2, "Mouse move speed", self._move_speed_var, 0, 100, "Movement", "MoveSpeed")

        self._add_scale_row(grid, 3, "Step delay (ms)", self._step_delay_var, 0, 500, "Delays", "StepDelayMs")
        self._add_scale_row(grid, 4, "Before click (ms)", self._before_click_var, 0, 2000, "Delays", "BeforeClickMs")
        self._add_scale_row(grid, 5, "After click (ms)", self._after_click_var, 0, 2000, "Delays", "AfterClickMs")

        self._add_scale_row(grid, 6, "Click center every rotations", self._click_every_rot_var, 0, 50, "Click", "CenterClickEveryRotations")
        self._add_scale_row(grid, 7, "Click center every ms", self._click_every_ms_var, 0, 30000, "Click", "CenterClickEveryMs")

        self._add_combo_row(grid, 8, "Direction", self._direction_var, ["clockwise", "counter-clockwise"], "Movement", "Direction")
        self._add_combo_row(grid, 9, "Click button", self._click_button_var, ["left", "right", "middle"], "Click", "ClickButton")
        self._add_scale_row(grid, 10, "Click count", self._click_count_var, 1, 5, "Click", "ClickCount")
        self._add_scale_row(grid, 11, "Click speed", self._click_speed_var, 0, 100, "Click", "ClickSpeed")

    def _build_tab_loops(self):
        self._loop_count_var = tk.IntVar(value=0)
        self._per_loop_delay_var = tk.DoubleVar(value=0)

        self._post_loop_enabled_var = tk.IntVar(value=0)
        self._post_loop_key_var = tk.StringVar(value="SPACE")

        grid = ttk.Frame(self._tab_loops)
        grid.pack(fill="both", expand=True)

        self._add_entry_row(grid, 0, "Loop count (0=infinite)", self._loop_count_var, "Loops", "Count")
        self._add_scale_row(grid, 1, "Per-loop delay (ms)", self._per_loop_delay_var, 0, 30000, "Delays", "PerLoopDelayMs")

        row = ttk.Frame(grid)
        row.grid(row=2, column=0, columnspan=3, sticky="w", pady=(14, 0))

        chk = ttk.Checkbutton(
            row,
            text="Post-loop key press",
            variable=self._post_loop_enabled_var,
            command=lambda: self._config.set("Actions", "PostLoopEnabled", int(self._post_loop_enabled_var.get())),
        )
        chk.pack(side="left")

        ttk.Label(row, text="Key:").pack(side="left", padx=(14, 6))

        keys = _key_choices()
        cmb = ttk.Combobox(row, textvariable=self._post_loop_key_var, values=keys, width=12, state="readonly")
        cmb.pack(side="left")
        cmb.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._config.set("Actions", "PostLoopKey", self._post_loop_key_var.get()),
        )

    def _build_tab_hotkeys(self):
        self._hk_start_var = tk.StringVar(value="F6")
        self._hk_stop_var = tk.StringVar(value="F7")
        self._hk_confirm_var = tk.StringVar(value="F8")

        keys = _hotkey_choices()

        grid = ttk.Frame(self._tab_hotkeys)
        grid.pack(fill="both", expand=True)

        self._add_combo_row(grid, 0, "Start hotkey", self._hk_start_var, keys, "Hotkeys", "Start")
        self._add_combo_row(grid, 1, "Stop hotkey", self._hk_stop_var, keys, "Hotkeys", "Stop")
        self._add_combo_row(grid, 2, "Confirm-location hotkey", self._hk_confirm_var, keys, "Hotkeys", "ConfirmLocation")
        ttk.Label(grid, text="Hotkeys apply instantly.").grid(row=3, column=0, sticky="w", pady=(14, 0))

    def _build_tab_debug(self):
        self._debug_level_var = tk.StringVar(value="INFO")

        grid = ttk.Frame(self._tab_debug)
        grid.pack(fill="both", expand=True)

        ttk.Label(grid, text="Debug level").grid(row=0, column=0, sticky="w")
        levels = ["INFO", "ACTION", "WARNING", "ERROR", "TRACE"]
        cmb = ttk.Combobox(grid, textvariable=self._debug_level_var, values=levels, width=12, state="readonly")
        cmb.grid(row=0, column=1, sticky="w", padx=(10, 0))
        cmb.bind("<<ComboboxSelected>>", self._on_debug_level_changed)

        ttk.Label(grid, text="logs/debug.log").grid(row=1, column=0, sticky="w", pady=(14, 0))

    def _load_from_config(self):
        self._did_init_load = False
        x = self._config.get_int("Click", "ClickX", 0)
        y = self._config.get_int("Click", "ClickY", 0)
        self._coord_var.set(f"({x}, {y})")

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

        self._loop_count_var.set(self._config.get_int("Loops", "Count", 0))

        self._post_loop_enabled_var.set(self._config.get_int("Actions", "PostLoopEnabled", 0))
        self._post_loop_key_var.set(self._config.get("Actions", "PostLoopKey", "SPACE"))

        self._hk_start_var.set(self._config.get("Hotkeys", "Start", "F6"))
        self._hk_stop_var.set(self._config.get("Hotkeys", "Stop", "F7"))
        self._hk_confirm_var.set(self._config.get("Hotkeys", "ConfirmLocation", "F8"))

        self._debug_level_var.set(self._config.get("Debug", "Level", "INFO"))

        last_tab = self._config.get_int("UI", "LastTab", 0)
        try:
            self._notebook.select(last_tab)
        except Exception:
            pass

        self._did_init_load = True

        self._apply_hotkeys()

    def _add_scale_row(self, parent, row, label, var, min_val, max_val, section, option):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)

        val_label = ttk.Label(parent, width=8)
        val_label.grid(row=row, column=2, sticky="w", padx=(10, 0))

        def on_var_change(*_args):
            try:
                val = int(float(var.get()))
            except Exception:
                val = 0
            val_label.config(text=str(val))
            if getattr(self, "_did_init_load", False):
                self._config.set(section, option, val)

        var.trace_add("write", on_var_change)

        scale = ttk.Scale(parent, variable=var, from_=min_val, to=max_val, orient="horizontal")
        scale.grid(row=row, column=1, sticky="ew", padx=(10, 0))
        parent.columnconfigure(1, weight=1)

        on_var_change()

    def _add_entry_row(self, parent, row, label, var, section, option):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)

        entry = ttk.Entry(parent, textvariable=var, width=12)
        entry.grid(row=row, column=1, sticky="w", padx=(10, 0))

        def on_commit(_e=None):
            try:
                self._config.set(section, option, int(var.get()))
            except Exception:
                pass

        def on_var_change(*_args):
            if not getattr(self, "_did_init_load", False):
                return

            key = (section, option)
            job = self._debounce_jobs.get(key)
            if job is not None:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass

            def apply():
                on_commit()

            self._debounce_jobs[key] = self.root.after(400, apply)

        var.trace_add("write", on_var_change)

        entry.bind("<FocusOut>", on_commit)
        entry.bind("<Return>", on_commit)

    def _add_combo_row(self, parent, row, label, var, values, section, option):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)
        cmb = ttk.Combobox(parent, textvariable=var, values=values, width=16, state="readonly")
        cmb.grid(row=row, column=1, sticky="w", padx=(10, 0))
        cmb.bind("<<ComboboxSelected>>", lambda _e: self._on_combo_change(section, option, var.get()))

    def _apply_hotkeys(self):
        self._config.set("Hotkeys", "Start", self._hk_start_var.get())
        self._config.set("Hotkeys", "Stop", self._hk_stop_var.get())
        self._config.set("Hotkeys", "ConfirmLocation", self._hk_confirm_var.get())
        self._hotkeys.reload()

    def _on_combo_change(self, section: str, option: str, value: str):
        self._config.set(section, option, value)
        if section == "Hotkeys":
            self._apply_hotkeys()

    def _on_debug_level_changed(self, _e=None):
        level = self._debug_level_var.get()
        self._config.set("Debug", "Level", level)
        try:
            set_logger_level(self._logger, level)
        except Exception:
            pass

    def _on_tab_changed(self, _e=None):
        try:
            idx = int(self._notebook.index("current"))
            self._config.set("UI", "LastTab", idx)
        except Exception:
            pass

    def _set_status(self, status: str):
        self._status_var.set(status)

    def on_start(self):
        if self._picker.is_active:
            return
        self._error_var.set("")
        self._macro.start()

    def on_stop(self):
        self._macro.stop()

    def on_pick_location(self):
        if self._macro.is_running:
            return

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

        def on_cancelled():
            pass

        self._picker.begin(on_picked=on_picked, on_cancelled=on_cancelled, on_hide_ui=on_hide, on_show_ui=on_show)

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
            self._macro.stop()
        except Exception:
            pass

        try:
            self._hotkeys.stop()
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
