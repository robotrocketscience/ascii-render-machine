"""Nearest-neighbor matching of shape vectors to ASCII characters."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from ascii_render_machine.types import CharEntry


def match_single(
    query: npt.NDArray[np.float64],
    atlas_chars: list[CharEntry],
    atlas_mat: npt.NDArray[np.float64],
) -> str:
    """Find the character whose shape vector is closest to *query*.

    Args:
        query: A 6D shape vector.
        atlas_chars: List of CharEntry objects (parallel to atlas_mat rows).
        atlas_mat: Pre-stacked (N, 6) matrix of atlas vectors.

    Returns:
        The best-matching character.
    """
    diffs = atlas_mat - query[np.newaxis, :]  # (N, 6)
    dists = np.sum(diffs * diffs, axis=1)     # (N,)
    idx: int = int(np.argmin(dists))
    return atlas_chars[idx].char


def match_grid(
    grid_vectors: npt.NDArray[np.float64],
    atlas_chars: list[CharEntry],
    atlas_mat: npt.NDArray[np.float64],
) -> npt.NDArray[np.intp]:
    """Match an entire grid of shape vectors to atlas characters.

    Args:
        grid_vectors: Shape (rows, cols, 6) array of cell shape vectors.
        atlas_mat: Shape (N, 6) matrix of atlas vectors.
        atlas_chars: Parallel list of CharEntry (used by caller for lookup).

    Returns:
        Integer index array of shape (rows, cols) into atlas_chars.
    """
    rows, cols, _ = grid_vectors.shape
    flat = grid_vectors.reshape(-1, 6)  # (rows*cols, 6)

    # Vectorized Euclidean distance: ||a - b||^2 = ||a||^2 + ||b||^2 - 2*a.b
    query_sq = np.sum(flat * flat, axis=1, keepdims=True)   # (M, 1)
    atlas_sq = np.sum(atlas_mat * atlas_mat, axis=1, keepdims=True).T  # (1, N)
    dot = flat @ atlas_mat.T  # (M, N)
    dists = query_sq + atlas_sq - 2.0 * dot  # (M, N)

    indices = np.argmin(dists, axis=1)  # (M,)
    return indices.reshape(rows, cols)
