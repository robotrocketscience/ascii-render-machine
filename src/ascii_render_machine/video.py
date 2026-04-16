"""Video frame extraction and MP4/GIF encoding via ffmpeg."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import numpy.typing as npt

from ascii_render_machine.encoder import Encoder
from ascii_render_machine.renderer import render_terminal, render_frame_image
from ascii_render_machine.types import EncoderConfig, VideoConfig


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


def process_video_terminal(
    video_path: str,
    config: VideoConfig,
) -> None:
    """Process video and render each frame to terminal in real time."""
    import time

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
    frame_delay = 1.0 / config.fps

    for _i, rgb in enumerate(raw_frames):
        effective_rows = enc_config.effective_rows(rgb.shape[0], rgb.shape[1])
        ascii_frame = encoder.encode_array(rgb, rows=effective_rows)
        sys.stdout.write("\033[2J\033[H")
        render_terminal(ascii_frame)
        sys.stdout.flush()
        time.sleep(frame_delay)


def process_video_file(
    video_path: str,
    config: VideoConfig,
    output_path: str,
) -> None:
    """Process video and encode to MP4 or GIF via ffmpeg.

    Each frame is converted to ASCII art, rendered as an image
    (black background with colored monospace characters), then
    piped to ffmpeg for encoding.

    Output format is determined by the file extension (.mp4, .gif, .webm).
    """
    out = Path(output_path)
    suffix = out.suffix.lower()

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

    # Encode first frame to determine output image dimensions.
    first_rgb = raw_frames[0]
    effective_rows = enc_config.effective_rows(first_rgb.shape[0], first_rgb.shape[1])
    enc_config = EncoderConfig(
        cols=config.cols,
        rows=effective_rows,
        font_size=config.font_size,
        contrast_exp=config.contrast_exp,
    )
    encoder = Encoder(enc_config)

    first_ascii = encoder.encode_array(first_rgb, rows=effective_rows)
    first_img = render_frame_image(first_ascii, font_size=config.font_size)
    img_w, img_h = first_img.size

    # Ensure even dimensions for video codecs.
    img_w = img_w if img_w % 2 == 0 else img_w + 1
    img_h = img_h if img_h % 2 == 0 else img_h + 1

    # Build ffmpeg command.
    ffmpeg_cmd: list[str] = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pixel_format", "rgb24",
        "-video_size", f"{img_w}x{img_h}",
        "-framerate", str(config.fps),
        "-i", "pipe:0",
    ]

    if suffix == ".gif":
        ffmpeg_cmd += ["-vf", f"scale={img_w}:{img_h}:flags=lanczos", str(out)]
    elif suffix == ".webm":
        ffmpeg_cmd += ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", str(out)]
    else:
        # Default: MP4 with H.264
        ffmpeg_cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(out)]

    proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    total = len(raw_frames)
    for i, rgb in enumerate(raw_frames):
        ascii_frame = encoder.encode_array(rgb, rows=effective_rows)
        img = render_frame_image(ascii_frame, font_size=config.font_size)
        # Resize to exact target dimensions (handles odd pixel counts).
        if img.size != (img_w, img_h):
            img = img.resize((img_w, img_h))
        raw_bytes = np.array(img).tobytes()
        assert proc.stdin is not None
        proc.stdin.write(raw_bytes)
        if (i + 1) % 10 == 0 or i == total - 1:
            print(f"\r  Encoding frame {i + 1}/{total}", end="", flush=True)

    assert proc.stdin is not None
    proc.stdin.close()
    proc.wait()
    print()

    if proc.returncode != 0:
        assert proc.stderr is not None
        stderr_out = proc.stderr.read().decode(errors="replace")
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}): {stderr_out[:500]}")

    print(f"Wrote {total} frames to {out}")
