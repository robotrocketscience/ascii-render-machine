"""Core data types for ASCII Render Machine."""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import numpy.typing as npt


# A 6D shape vector: brightness samples from 6 circular regions.
ShapeVector = npt.NDArray[np.float64]  # shape (6,)

# An RGB color tuple.
RGB = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class Cell:
    """A single character cell in the ASCII grid."""

    char: str
    r: int
    g: int
    b: int


@dataclass(slots=True)
class Frame:
    """One frame of ASCII output: a grid of cells."""

    cols: int
    rows: int
    cells: list[Cell] = field(default_factory=lambda: list[Cell]())

    def to_bytes(self) -> bytes:
        """Serialize frame to binary: [char_code, R, G, B] per cell."""
        buf = bytearray(len(self.cells) * 4)
        for i, cell in enumerate(self.cells):
            offset = i * 4
            buf[offset] = ord(cell.char) & 0xFF
            buf[offset + 1] = cell.r & 0xFF
            buf[offset + 2] = cell.g & 0xFF
            buf[offset + 3] = cell.b & 0xFF
        return bytes(buf)


@dataclass(frozen=True, slots=True)
class ChunkInfo:
    """Metadata for one binary chunk file."""

    file: str
    frames: int
    size: int


@dataclass(slots=True)
class Manifest:
    """Manifest describing a set of chunked video output."""

    cols: int
    rows: int
    fps: int
    total_frames: int
    chunk_count: int
    frame_size: int
    flame_bytes: int
    chunks: list[ChunkInfo] = field(default_factory=lambda: list[ChunkInfo]())

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dict."""
        return {
            "cols": self.cols,
            "rows": self.rows,
            "fps": self.fps,
            "total_frames": self.total_frames,
            "chunk_count": self.chunk_count,
            "frame_size": self.frame_size,
            "flame_bytes": self.flame_bytes,
            "chunks": [
                {"file": c.file, "frames": c.frames, "size": c.size}
                for c in self.chunks
            ],
        }


@dataclass(frozen=True, slots=True)
class CharEntry:
    """An ASCII character and its pre-computed 6D shape vector."""

    char: str
    vector: ShapeVector


@dataclass(frozen=True, slots=True)
class EncoderConfig:
    """Configuration for the image-to-ASCII encoder."""

    cols: int
    rows: int | None = None
    font_size: int = 16
    contrast_exp: float = 1.2

    def effective_rows(self, image_height: int, image_width: int) -> int:
        """Compute row count that preserves aspect ratio."""
        if self.rows is not None:
            return self.rows
        cell_w = image_width / self.cols
        # Characters are roughly twice as tall as wide in a terminal.
        cell_h = cell_w * 2.0
        return max(1, int(image_height / cell_h))


@dataclass(frozen=True, slots=True)
class VideoConfig:
    """Configuration for video processing."""

    cols: int
    rows: int | None = None
    fps: int = 10
    font_size: int = 16
    contrast_exp: float = 1.2
    chunk_target_bytes: int = 2 * 1024 * 1024  # ~2 MB per chunk
