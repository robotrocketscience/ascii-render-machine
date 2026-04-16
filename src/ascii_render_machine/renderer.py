"""Render ASCII grids to terminal output, JSON, or images."""

from __future__ import annotations

import json
import sys
from typing import TextIO

from ascii_render_machine.types import Frame


def render_terminal(
    frame: Frame, out: TextIO | None = None, color: bool = True
) -> None:
    """Print a frame as ANSI truecolor text to the terminal.

    Args:
        frame: The ASCII frame to render.
        out: Output stream (defaults to sys.stdout).
        color: If True, emit ANSI 24-bit color escape sequences.
    """
    stream: TextIO = out if out is not None else sys.stdout

    for r in range(frame.rows):
        parts: list[str] = []
        for c in range(frame.cols):
            cell = frame.cells[r * frame.cols + c]
            if color:
                parts.append(
                    f"\033[38;2;{cell.r};{cell.g};{cell.b}m{cell.char}\033[0m"
                )
            else:
                parts.append(cell.char)
        stream.write("".join(parts) + "\n")


def render_json(frame: Frame) -> str:
    """Serialize a frame to a JSON string.

    Format:
    {
      "cols": N, "rows": N,
      "cells": [{"char": "A", "r": 255, "g": 128, "b": 0}, ...]
    }
    """
    cells_list: list[dict[str, object]] = [
        {"char": cell.char, "r": cell.r, "g": cell.g, "b": cell.b}
        for cell in frame.cells
    ]
    data: dict[str, object] = {
        "cols": frame.cols,
        "rows": frame.rows,
        "cells": cells_list,
    }
    return json.dumps(data)


def render_plain(frame: Frame) -> str:
    """Render a frame as plain text (no color)."""
    lines: list[str] = []
    for r in range(frame.rows):
        row_chars: list[str] = []
        for c in range(frame.cols):
            row_chars.append(frame.cells[r * frame.cols + c].char)
        lines.append("".join(row_chars))
    return "\n".join(lines)
