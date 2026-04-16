"""Command-line interface for ASCII Render Machine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from ascii_render_machine.encoder import Encoder
from ascii_render_machine.renderer import render_json, render_terminal
from ascii_render_machine.types import EncoderConfig, VideoConfig


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ascii-render-machine",
        description="Convert images and videos to ASCII art using 6D shape-vector matching.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- photo sub-command --
    photo = sub.add_parser("photo", help="Convert a single image to ASCII art.")
    photo.add_argument("input", help="Path to the input image file.")
    photo.add_argument("--cols", type=int, default=80, help="Number of character columns (default: 80).")
    photo.add_argument("--rows", type=int, default=None, help="Number of character rows (auto if omitted).")
    photo.add_argument("--terminal", action="store_true", help="Render to terminal with ANSI truecolor.")
    photo.add_argument("--no-color", action="store_true", help="Disable color in terminal output.")
    photo.add_argument("--output", type=str, default=None, help="Output file path (.png, .jpg, or .json).")
    photo.add_argument("--font-size", type=int, default=16, help="Font size for character atlas (default: 16).")
    photo.add_argument("--contrast", type=float, default=1.2, help="Contrast exponent (default: 1.2).")

    # -- video sub-command --
    video = sub.add_parser("video", help="Convert a video to ASCII art.")
    video.add_argument("input", help="Path to the input video file.")
    video.add_argument("--cols", type=int, default=80, help="Number of character columns (default: 80).")
    video.add_argument("--rows", type=int, default=None, help="Number of character rows (auto if omitted).")
    video.add_argument("--fps", type=int, default=10, help="Target frames per second (default: 10).")
    video.add_argument("--terminal", action="store_true", help="Play ASCII video in the terminal.")
    video.add_argument("--output", type=str, default=None, help="Output video file path (.mp4, .gif, or .webm).")
    video.add_argument("--font-size", type=int, default=16, help="Font size for character atlas (default: 16).")
    video.add_argument("--contrast", type=float, default=1.2, help="Contrast exponent (default: 1.2).")

    return parser


def _run_photo(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    config = EncoderConfig(
        cols=args.cols,
        rows=args.rows,
        font_size=args.font_size,
        contrast_exp=args.contrast,
    )
    encoder = Encoder(config)
    img = Image.open(input_path)
    frame = encoder.encode_image(img)

    if args.output:
        from ascii_render_machine.renderer import render_frame_image

        out_path = Path(args.output)
        suffix = out_path.suffix.lower()
        if suffix == ".json":
            out_path.write_text(render_json(frame))
            print(f"Wrote JSON to {out_path}")
        else:
            img_out = render_frame_image(frame, font_size=args.font_size)
            img_out.save(str(out_path))
            print(f"Wrote {img_out.size[0]}x{img_out.size[1]} image to {out_path}")
    elif args.terminal:
        render_terminal(frame, color=not args.no_color)
    else:
        # Default to terminal output.
        render_terminal(frame, color=not args.no_color)


def _run_video(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    config = VideoConfig(
        cols=args.cols,
        rows=args.rows,
        fps=args.fps,
        font_size=args.font_size,
        contrast_exp=args.contrast,
    )

    if args.output:
        from ascii_render_machine.video import process_video_file

        process_video_file(str(input_path), config, args.output)
    elif args.terminal:
        from ascii_render_machine.video import process_video_terminal

        process_video_terminal(str(input_path), config)
    else:
        print("Error: specify --terminal or --output for video mode.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "photo":
        _run_photo(args)
    elif args.command == "video":
        _run_video(args)


if __name__ == "__main__":
    main()
