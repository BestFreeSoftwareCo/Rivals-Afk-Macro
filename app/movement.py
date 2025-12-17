from __future__ import annotations

import math
from collections.abc import Iterator


def iter_circle_points(
    center_x: int,
    center_y: int,
    radius: int,
    step_degrees: int,
    clockwise: bool,
) -> Iterator[tuple[int, int, int]]:
    step = max(1, abs(int(step_degrees)))

    if clockwise:
        angles = range(0, 360, step)
    else:
        angles = range(0, -360, -step)

    for angle in angles:
        rad = math.radians(angle)
        x = int(round(center_x + math.cos(rad) * radius))
        y = int(round(center_y + math.sin(rad) * radius))
        yield angle, x, y
