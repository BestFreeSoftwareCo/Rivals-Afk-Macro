# Changelog

All notable changes to this project will be documented here.

## Unreleased

- UI/UX: Dark navy theme tuning and styling improvements.

## 2025-12-17

- UI: Migrated main window UI shell and tab system to **CustomTkinter** for fully rounded controls.
- UI: Added dark mode support and updated palette to a **dark navy** theme.
- UI: Added **Reset to Defaults** button to all tabs, wired to safe config reset.
- Config: Implemented safe reset logic with automatic backups (`config.ini.bak.YYYYMMDD_HHMMSS`).
- Stability: Fixed font compatibility issues between Tk fonts and CustomTkinter (CTkFont/tuples).
- Stability: Improved `after()` lifecycle handling and ensured pick overlay is destroyed on shutdown.
- Launch: Updated `run.bat` to auto-install dependencies (`pip install -r requirements.txt`) when missing.
