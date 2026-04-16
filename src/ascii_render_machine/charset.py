"""ASCII character atlas with pre-computed 6D shape vectors."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from PIL import Image, ImageDraw, ImageFont

from ascii_render_machine.sampler import get_circle_masks, sample_cell
from ascii_render_machine.types import CharEntry


# Printable ASCII range: space (32) through tilde (126).
PRINTABLE_START = 32
PRINTABLE_END = 127


def _render_char_bitmap(
    char: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, cell_w: int, cell_h: int
) -> npt.NDArray[np.float64]:
    """Render a single character to a grayscale bitmap, values in [0, 1]."""
    img = Image.new("L", (cell_w, cell_h), color=0)
    draw = ImageDraw.Draw(img)
    bbox = font.getbbox(char)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (cell_w - tw) // 2 - bbox[0]
    y = (cell_h - th) // 2 - bbox[1]
    draw.text((x, y), char, fill=255, font=font)
    arr: npt.NDArray[np.uint8] = np.array(img, dtype=np.uint8)
    return arr.astype(np.float64) / 255.0


def build_atlas(
    font_size: int = 16, contrast_exp: float = 1.2
) -> list[CharEntry]:
    """Build the character atlas: render every printable ASCII char and compute
    its 6D shape vector.

    Args:
        font_size: Size of the monospace font used for rendering.
        contrast_exp: Exponent applied to shape vector components for contrast
            enhancement.  Values > 1 sharpen distinctions between characters.

    Returns:
        A list of ``CharEntry`` objects, one per printable ASCII character.
    """
    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("Courier New.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    # Determine cell dimensions from a representative character.
    bbox = font.getbbox("M")
    cell_w: int = max(1, int(bbox[2] - bbox[0] + 2))
    cell_h: int = max(1, cell_w * 2)

    masks = get_circle_masks(cell_h, cell_w)

    # First pass: compute raw vectors and track max per component.
    raw_vectors: list[tuple[str, npt.NDArray[np.float64]]] = []
    max_components = np.zeros(6, dtype=np.float64)

    for code in range(PRINTABLE_START, PRINTABLE_END):
        char = chr(code)
        bitmap = _render_char_bitmap(char, font, cell_w, cell_h)
        vec = sample_cell(bitmap, masks)
        raw_vectors.append((char, vec))
        max_components = np.maximum(max_components, vec)

    # Normalize and apply contrast exponent.
    max_components = np.maximum(max_components, 1e-10)
    entries: list[CharEntry] = []
    for char, vec in raw_vectors:
        normalized = vec / max_components
        enhanced = np.power(normalized, contrast_exp) * max_components
        entries.append(CharEntry(char=char, vector=enhanced))

    return entries


def atlas_matrix(entries: list[CharEntry]) -> npt.NDArray[np.float64]:
    """Stack atlas vectors into a (N, 6) matrix for vectorized matching."""
    return np.array([e.vector for e in entries], dtype=np.float64)
