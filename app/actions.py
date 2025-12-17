from __future__ import annotations


def key_name_to_autoit_send(key_name: str) -> str:
    name = key_name.strip().upper()

    if len(name) == 1 and name.isalpha():
        return name.lower()

    if len(name) == 1 and name.isdigit():
        return name

    if name.startswith("F") and name[1:].isdigit():
        return "{" + name + "}"

    if name in {"SPACE", "ENTER", "TAB", "ESC"}:
        return "{" + name + "}"

    if name == "SHIFT":
        return "{SHIFTDOWN}{SHIFTUP}"

    if name == "CTRL":
        return "{CTRLDOWN}{CTRLUP}"

    return name
