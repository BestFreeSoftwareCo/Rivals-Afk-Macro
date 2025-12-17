# Rivals AFK Macro Rework v4

A Windows-focused AFK macro utility with a modern **dark navy** UI built on **CustomTkinter**.

## Features

- **Modern UI** (CustomTkinter): rounded tabs, buttons, inputs, switches, and dropdowns
- **Pick Location** mode with a lightweight overlay showing live cursor coordinates
- **Global hotkeys** for start/stop/confirm/cancel
- **Config persistence** via `config/config.ini`
- **Reset to Defaults** button available on all tabs (backs up config before resetting)

## Requirements

- Python 3.12+ (recommended)
- Windows 10/11

Python dependencies are in `requirements.txt`.

## Install / Run

### Option A: Run via `run.bat` (recommended)

1. Double-click `run.bat`
2. If dependencies are missing, it will auto-install them using `pip install -r requirements.txt`

### Option B: Run via Python

From the project folder:

```bash
python -m pip install -r requirements.txt
python -m app.main
```

## Hotkeys

Defaults (editable in the UI):

- Start: `F6`
- Stop: `F7`
- Confirm Location: `F8`
- Cancel Pick Mode: `ESC`

## Reset to Defaults

Every tab includes a **Reset to Defaults** button.

Behavior:

- The app will refuse to reset while the macro is running or pick mode is active.
- `config/config.ini` is backed up to a timestamped file before resetting.

## Files / Folders

- `app/` — application code
- `config/config.ini` — persistent settings
- `config/config.ini.bak.*` — config backups created during reset
- `logs/debug.log` — runtime log output

## Privacy / Sharing

- The source code does **not** hardcode your Windows username or file paths.
- Logs and config may contain **timestamps**, **window geometry**, and **screen coordinates**.

Before sharing the project publicly, consider deleting:

- `logs/debug.log`
- `config/config.ini`
- `config/config.ini.bak.*`

## Changelog

See `CHANGELOG.md` for notable changes.
