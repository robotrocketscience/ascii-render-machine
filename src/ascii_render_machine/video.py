"""Video frame extraction and chunked binary encoding."""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import cv2
import numpy as np
import numpy.typing as npt

from ascii_render_machine.encoder import Encoder
from ascii_render_machine.types import (
    ChunkInfo,
    EncoderConfig,
    Frame,
    Manifest,
    VideoConfig,
)


def _extract_frames(
    video_path: str, target_fps: int
) -> list[npt.NDArray[np.uint8]]:
    """Extract frames from a video file at the target FPS.

    Returns a list of RGB numpy arrays (H, W, 3).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    source_fps: float = cap.get(cv2.CAP_PROP_FPS)
    if source_fps <= 0:
        source_fps = 30.0

    frame_interval = max(1.0, source_fps / target_fps)
    frames: list[npt.NDArray[np.uint8]] = []
    frame_idx = 0.0

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
        ret, bgr = cap.read()
        if not ret:
            break
        rgb = np.asarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), dtype=np.uint8)
        frames.append(rgb)
        frame_idx += frame_interval

    cap.release()
    return frames


def _frame_to_binary(frame: Frame) -> bytes:
    """Serialize a Frame to the binary chunk format (no flame mask yet)."""
    cell_bytes = frame.to_bytes()
    flame_bytes_count = math.ceil(len(frame.cells) / 8)
    flame_mask = b"\x00" * flame_bytes_count
    return cell_bytes + flame_mask


def process_video_terminal(
    video_path: str,
    config: VideoConfig,
    render_fn: object,
) -> None:
    """Process video and render each frame to terminal in sequence.

    Args:
        video_path: Path to the input video file.
        config: Video processing configuration.
        render_fn: A callable(Frame) that renders to terminal.
    """
    from ascii_render_machine.renderer import render_terminal

    raw_frames = _extract_frames(video_path, config.fps)
    if not raw_frames:
        raise RuntimeError("No frames extracted from video")

    enc_config = EncoderConfig(
        cols=config.cols,
        rows=config.rows,
        font_size=config.font_size,
        contrast_exp=config.contrast_exp,
    )
    encoder = Encoder(enc_config)

    import sys
    import time

    frame_delay = 1.0 / config.fps

    for _i, rgb in enumerate(raw_frames):
        effective_rows = enc_config.effective_rows(rgb.shape[0], rgb.shape[1])
        ascii_frame = encoder.encode_array(rgb, rows=effective_rows)
        # Clear screen.
        sys.stdout.write("\033[2J\033[H")
        render_terminal(ascii_frame)
        sys.stdout.flush()
        time.sleep(frame_delay)


def process_video_chunks(
    video_path: str,
    config: VideoConfig,
    output_dir: str,
) -> Manifest:
    """Process video and write chunked binary files plus manifest.

    Args:
        video_path: Path to the input video file.
        config: Video processing configuration.
        output_dir: Directory to write chunk files and manifest.json.

    Returns:
        The generated Manifest.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    raw_frames = _extract_frames(video_path, config.fps)
    if not raw_frames:
        raise RuntimeError("No frames extracted from video")

    # Determine effective rows from first frame.
    first = raw_frames[0]
    enc_config = EncoderConfig(
        cols=config.cols,
        rows=config.rows,
        font_size=config.font_size,
        contrast_exp=config.contrast_exp,
    )
    effective_rows = enc_config.effective_rows(first.shape[0], first.shape[1])
    # Lock in rows for consistency.
    enc_config = EncoderConfig(
        cols=config.cols,
        rows=effective_rows,
        font_size=config.font_size,
        contrast_exp=config.contrast_exp,
    )
    encoder = Encoder(enc_config)

    # Encode all frames.
    encoded_frames: list[Frame] = []
    for rgb in raw_frames:
        encoded_frames.append(encoder.encode_array(rgb, rows=effective_rows))

    # Compute sizes.
    cell_count = effective_rows * config.cols
    flame_byte_count = math.ceil(cell_count / 8)
    frame_size = cell_count * 4 + flame_byte_count

    # Target chunk size.
    frames_per_chunk = max(1, config.chunk_target_bytes // frame_size)

    # Write chunks.
    chunks: list[ChunkInfo] = []
    total = len(encoded_frames)
    chunk_idx = 0
    offset = 0

    while offset < total:
        end = min(offset + frames_per_chunk, total)
        n_frames = end - offset
        chunk_name = f"chunk_{chunk_idx:03d}.bin"

        buf = bytearray()
        buf += struct.pack("<H", n_frames)
        for frame in encoded_frames[offset:end]:
            buf += _frame_to_binary(frame)

        chunk_path = out_path / chunk_name
        chunk_path.write_bytes(bytes(buf))

        chunks.append(ChunkInfo(file=chunk_name, frames=n_frames, size=len(buf)))
        chunk_idx += 1
        offset = end

    manifest = Manifest(
        cols=config.cols,
        rows=effective_rows,
        fps=config.fps,
        total_frames=total,
        chunk_count=len(chunks),
        frame_size=frame_size,
        flame_bytes=flame_byte_count,
        chunks=chunks,
    )

    manifest_path = out_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2))

    return manifest
