"""6-region circular sampling to produce 6D shape vectors."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from ascii_render_machine.types import ShapeVector


def _build_circle_masks(
    cell_h: int, cell_w: int, n_samples: int = 64
) -> npt.NDArray[np.float64]:
    """Build 6 circle masks over a cell of size (cell_h, cell_w).

    Returns an array of shape (6, cell_h, cell_w) where each slice is a soft
    mask with values in [0, 1] indicating membership in that circle.

    The 6 circles are arranged in a 2-column x 3-row layout with vertical
    staggering: left circles shift down, right circles shift up -- matching the
    technique from alexharri.com/blog/ascii-rendering.
    """
    mask = np.zeros((6, cell_h, cell_w), dtype=np.float64)

    col_centers_x = [cell_w * 0.25, cell_w * 0.75]
    row_centers_y = [cell_h * (1 / 6), cell_h * 0.5, cell_h * (5 / 6)]

    # Stagger: left column shifts down by 8% of cell_h, right shifts up.
    stagger = cell_h * 0.08
    offsets = [-stagger, stagger]

    radius_x = cell_w * 0.30
    radius_y = cell_h * 0.20

    ys = np.arange(cell_h, dtype=np.float64)
    xs = np.arange(cell_w, dtype=np.float64)
    yy, xx = np.meshgrid(ys, xs, indexing="ij")

    idx = 0
    for row_i in range(3):
        for col_i in range(2):
            cy = row_centers_y[row_i] + offsets[col_i]
            cx = col_centers_x[col_i]
            dist_sq = ((yy - cy) / radius_y) ** 2 + ((xx - cx) / radius_x) ** 2
            mask[idx] = (dist_sq <= 1.0).astype(np.float64)
            idx += 1

    return mask


# Module-level cache so we only compute masks once per cell size.
_mask_cache: dict[tuple[int, int], npt.NDArray[np.float64]] = {}


def get_circle_masks(cell_h: int, cell_w: int) -> npt.NDArray[np.float64]:
    """Return cached circle masks for the given cell dimensions."""
    key = (cell_h, cell_w)
    if key not in _mask_cache:
        _mask_cache[key] = _build_circle_masks(cell_h, cell_w)
    return _mask_cache[key]


def sample_cell(
    gray: npt.NDArray[np.float64], masks: npt.NDArray[np.float64]
) -> ShapeVector:
    """Compute the 6D shape vector for a single grayscale cell.

    Args:
        gray: Grayscale cell pixels, shape (cell_h, cell_w), values in [0, 1].
        masks: Circle masks from ``get_circle_masks``, shape (6, cell_h, cell_w).

    Returns:
        A 6-element float64 array with the average brightness inside each circle.
    """
    # Weighted mean per circle: sum(gray * mask) / sum(mask).
    weighted = masks * gray[np.newaxis, :, :]  # (6, h, w)
    sums = weighted.sum(axis=(1, 2))
    counts = masks.sum(axis=(1, 2))
    # Avoid division by zero for degenerate tiny cells.
    counts = np.maximum(counts, 1.0)
    return (sums / counts).astype(np.float64)


def sample_image_cells(
    gray: npt.NDArray[np.float64], rows: int, cols: int
) -> npt.NDArray[np.float64]:
    """Sample an entire image into a grid of 6D shape vectors.

    Args:
        gray: Full grayscale image, shape (H, W), values in [0, 1].
        rows: Number of cell rows.
        cols: Number of cell columns.

    Returns:
        Array of shape (rows, cols, 6) with per-cell shape vectors.
    """
    h, w = gray.shape
    cell_h = max(1, h // rows)
    cell_w = max(1, w // cols)
    masks = get_circle_masks(cell_h, cell_w)

    result = np.zeros((rows, cols, 6), dtype=np.float64)
    for r in range(rows):
        y0 = r * cell_h
        y1 = min(y0 + cell_h, h)
        for c in range(cols):
            x0 = c * cell_w
            x1 = min(x0 + cell_w, w)
            cell_gray = gray[y0:y1, x0:x1]
            ch, cw = cell_gray.shape
            if ch < cell_h or cw < cell_w:
                padded = np.zeros((cell_h, cell_w), dtype=np.float64)
                padded[:ch, :cw] = cell_gray
                cell_gray = padded
            result[r, c] = sample_cell(cell_gray, masks)
    return result
