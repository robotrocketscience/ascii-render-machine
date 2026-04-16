"""Tests for the nearest-neighbor matcher."""

import numpy as np
import numpy.typing as npt

from ascii_render_machine.matcher import match_grid, match_single
from ascii_render_machine.types import CharEntry


def _make_atlas() -> tuple[list[CharEntry], npt.NDArray[np.float64]]:
    """Create a small synthetic atlas for testing."""
    entries = [
        CharEntry(char="A", vector=np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])),
        CharEntry(char="B", vector=np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0])),
        CharEntry(char="C", vector=np.array([0.0, 0.0, 1.0, 0.0, 0.0, 0.0])),
    ]
    mat = np.array([e.vector for e in entries], dtype=np.float64)
    return entries, mat


def test_match_single_exact() -> None:
    entries, mat = _make_atlas()
    query = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert match_single(query, entries, mat) == "A"


def test_match_single_nearest() -> None:
    entries, mat = _make_atlas()
    query = np.array([0.1, 0.9, 0.0, 0.0, 0.0, 0.0])
    assert match_single(query, entries, mat) == "B"


def test_match_grid_shape() -> None:
    entries, mat = _make_atlas()
    grid = np.random.default_rng(42).random((3, 4, 6))
    indices = match_grid(grid, entries, mat)
    assert indices.shape == (3, 4)
    assert indices.min() >= 0
    assert indices.max() < len(entries)


def test_match_grid_known() -> None:
    entries, mat = _make_atlas()
    grid = np.zeros((2, 2, 6))
    grid[0, 0] = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # A
    grid[0, 1] = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]  # B
    grid[1, 0] = [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]  # C
    grid[1, 1] = [0.9, 0.1, 0.0, 0.0, 0.0, 0.0]  # A
    indices = match_grid(grid, entries, mat)
    assert entries[int(indices[0, 0])].char == "A"
    assert entries[int(indices[0, 1])].char == "B"
    assert entries[int(indices[1, 0])].char == "C"
    assert entries[int(indices[1, 1])].char == "A"
