"""Tests for the full image-to-ASCII encoder."""

import numpy as np
from PIL import Image

from ascii_render_machine.encoder import Encoder
from ascii_render_machine.types import EncoderConfig


def test_encode_gradient() -> None:
    """Encode a simple gradient image and check output shape."""
    width, height = 160, 80
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for _x in range(width):
        arr[:, :, 0] = np.arange(width, dtype=np.uint8)[np.newaxis, :]
        arr[:, :, 1] = 128
        arr[:, :, 2] = 64

    img = Image.fromarray(arr, "RGB")
    config = EncoderConfig(cols=20)
    encoder = Encoder(config)
    frame = encoder.encode_image(img)

    assert frame.cols == 20
    assert frame.rows > 0
    assert len(frame.cells) == frame.rows * frame.cols


def test_encode_white_image() -> None:
    """A white image should not crash and should produce valid cells."""
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    config = EncoderConfig(cols=10)
    encoder = Encoder(config)
    frame = encoder.encode_image(img)
    assert len(frame.cells) > 0
    for cell in frame.cells:
        assert 32 <= ord(cell.char) <= 126


def test_encode_black_image() -> None:
    """A black image should produce mostly space characters."""
    img = Image.new("RGB", (100, 100), color=(0, 0, 0))
    config = EncoderConfig(cols=10)
    encoder = Encoder(config)
    frame = encoder.encode_image(img)
    assert len(frame.cells) > 0
    # Most cells should be space since black = lowest brightness.
    space_count = sum(1 for c in frame.cells if c.char == " ")
    assert space_count > len(frame.cells) * 0.5


def test_frame_to_bytes() -> None:
    """Verify binary serialization produces correct byte count."""
    img = Image.new("RGB", (80, 40), color=(128, 64, 200))
    config = EncoderConfig(cols=10, rows=5)
    encoder = Encoder(config)
    frame = encoder.encode_image(img)
    data = frame.to_bytes()
    assert len(data) == len(frame.cells) * 4


def test_encode_array() -> None:
    """Test encoding from a raw numpy array."""
    arr = np.full((60, 120, 3), 128, dtype=np.uint8)
    config = EncoderConfig(cols=15)
    encoder = Encoder(config)
    frame = encoder.encode_array(arr, rows=8)
    assert frame.cols == 15
    assert frame.rows == 8
    assert len(frame.cells) == 15 * 8
