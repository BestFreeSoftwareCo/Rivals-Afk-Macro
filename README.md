# Rivals AFK Macro

A lightweight Windows AFK macro with a modern dark UI.

## Features

- **Pick a location** with a confirm hotkey
- **Circular mouse movement** around the picked point
- **Optional center clicking** (every N rotations and/or every N milliseconds)
- **Configurable hotkeys**
- **Safe Start/Stop lifecycle** with logging
- **Dark themed UI**

## Requirements

- **Windows**
- **Python 3.10+** (recommended **3.12**)
- **AutoIt v3** installed
  - Download: https://www.autoitscript.com/site/autoit/downloads/
  - If AutoIt is installed in a non-standard location, set:
    - `AUTOIT3_EXE` environment variable to the full path of `AutoIt3.exe`

## Quick Start

1. Download/clone this repo
2. Run `install.bat`
3. Run `Launch-Rivals-AFK.bat`

## Running

- Preferred launcher:
  - `Launch-Rivals-AFK.bat`

Notes:

- If you run the game as Administrator, you typically must run this macro as Administrator as well.
- Global hotkeys on some systems require Administrator.

## Hotkeys (defaults)

- **Start:** `F6`
- **Stop:** `F7`
- **Confirm pick:** `F8`
- **Cancel pick:** `ESC`

You can change these from inside the UI.

## Configuration

- User config file (local): `config/config.ini`
- Example template: `config/config.example.ini`

`config/config.ini` is intentionally ignored by Git so each user can keep their own settings.

## Logs

- Log file: `logs/debug.log`

The `logs/` folder is ignored by Git.

## Troubleshooting

### The app doesn’t open

- Run `Launch-Rivals-AFK.bat` and copy/paste the console output.
- Ensure Python is installed and available via `py -3` or `python`.
- Ensure `tkinter` is present (included with standard python.org installs).

### Hotkeys don’t work

- Try running the launcher **as Administrator**.
- If hotkeys work on desktop but not in-game, the game/anti-cheat may block global hooks.

### Mouse doesn’t move/click

- Install AutoIt v3.
- Ensure `autoit/runner.au3` exists.

## Repo structure

- `app/` Python application (UI + macro engine)
- `autoit/` AutoIt runner script
- `config/` configuration
- `logs/` runtime logs

