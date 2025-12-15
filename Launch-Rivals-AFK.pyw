import os
import sys
import traceback
from pathlib import Path


def _show_error(title: str, message: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, title, 0x00000010)
    except Exception:
        pass


def main() -> None:
    base_dir = Path(__file__).resolve().parent

    os.chdir(base_dir)
    sys.path.insert(0, str(base_dir))

    try:
        from app.main import main as app_main

        app_main()
    except Exception:
        tb = traceback.format_exc()

        try:
            logs_dir = base_dir / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            (logs_dir / "launcher_error.log").write_text(tb, encoding="utf-8")
        except Exception:
            pass

        _show_error(
            "Rivals AFK Macro - Launch Error",
            "The app failed to start. Details were saved to logs/launcher_error.log\n\n" + tb,
        )


if __name__ == "__main__":
    main()
