"""Tests for the 6-region circular sampler."""

import numpy as np

from ascii_render_machine.sampler import (
    get_circle_masks,
    sample_cell,
    sample_image_cells,
)


def test_circle_masks_shape() -> None:
    masks = get_circle_masks(32, 16)
    assert masks.shape == (6, 32, 16)


def test_circle_masks_values_in_range() -> None:
    masks = get_circle_masks(32, 16)
    assert masks.min() >= 0.0
    assert masks.max() <= 1.0


def test_sample_cell_white() -> None:
    """A fully white cell should produce a uniform non-zero vector."""
    cell = np.ones((32, 16), dtype=np.float64)
    masks = get_circle_masks(32, 16)
    vec = sample_cell(cell, masks)
    assert vec.shape == (6,)
    assert np.all(vec > 0.0)


def test_sample_cell_black() -> None:
    """A fully black cell should produce a zero vector."""
    cell = np.zeros((32, 16), dtype=np.float64)
    masks = get_circle_masks(32, 16)
    vec = sample_cell(cell, masks)
    assert vec.shape == (6,)
    assert np.allclose(vec, 0.0)


def test_sample_image_cells_shape() -> None:
    image = np.random.default_rng(42).random((100, 200))
    result = sample_image_cells(image, rows=5, cols=10)
    assert result.shape == (5, 10, 6)


def test_sample_half_bright() -> None:
    """Left half bright, right half dark should show asymmetry."""
    cell = np.zeros((32, 16), dtype=np.float64)
    cell[:, :8] = 1.0  # left half bright
    masks = get_circle_masks(32, 16)
    vec = sample_cell(cell, masks)
    # Left column circles (indices 0, 2, 4) should be brighter than right (1, 3, 5).
    left_mean = vec[0::2].mean()
    right_mean = vec[1::2].mean()
    assert left_mean > right_mean
