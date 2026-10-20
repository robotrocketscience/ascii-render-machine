# ASCII Render Machine

ascii-render-machine converts images and videos to full-color ASCII art using the method from [ASCII Rendering](https://alexharri.com/blog/ascii-rendering) by Alex Harri.

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:robotrocketscience/ascii-render-machine.git
cd ascii-render-machine
uv sync
```

Video output also requires [ffmpeg](https://ffmpeg.org/) installed on your system.

## Quick start

```bash
# Render an image to a PNG
uv run ascii-render-machine photo examples/sample.jpg --cols 120 --output result.png

# Render an image to the terminal
uv run ascii-render-machine photo examples/sample.jpg --cols 80 --terminal

# Convert video to MP4
uv run ascii-render-machine video input.mp4 --cols 120 --fps 10 --output result.mp4

# Convert video to GIF
uv run ascii-render-machine video input.mp4 --cols 60 --fps 8 --output result.gif

# Play video as ASCII in the terminal
uv run ascii-render-machine video input.mp4 --cols 80 --terminal --fps 10
```

## Algorithm

A 6D shape vector holds the average grayscale brightness of 6 vertically staggered circular regions in 2 columns and 3 rows.

The character atlas holds the shape vector of each printable ASCII character (32-126), rendered to a bitmap at a fixed font size. The atlas vectors are normalized and raised to a contrast exponent to sharpen character differences.

Each cell of the input grid gets a shape vector and an average RGB color. A vectorized search by expanded Euclidean distance finds the nearest atlas character for each cell. The output draws that character in the cell's color.

## CLI reference

### `photo` command

```
ascii-render-machine photo INPUT [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--cols N` | 80 | Number of character columns |
| `--rows N` | auto | Number of character rows (auto-calculated from aspect ratio if omitted) |
| `--terminal` | off | Render to terminal with ANSI truecolor |
| `--no-color` | off | Disable color in terminal output |
| `--output PATH` | none | Output file (.png, .jpg, or .json) |
| `--font-size N` | 16 | Font size used for the character atlas and image rendering |
| `--contrast F` | 1.2 | Contrast exponent for shape vector enhancement |

### `video` command

```
ascii-render-machine video INPUT [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--cols N` | 80 | Number of character columns |
| `--rows N` | auto | Number of character rows |
| `--fps N` | 10 | Target frames per second |
| `--terminal` | off | Play ASCII video in the terminal |
| `--output PATH` | none | Output video file (.mp4, .gif, or .webm). Requires ffmpeg. |
| `--font-size N` | 16 | Font size used for the character atlas |
| `--contrast F` | 1.2 | Contrast exponent |

## Output formats

### Image (photo --output result.png)

Colored monospace characters are drawn on a black background and saved in any format Pillow writes (PNG, JPG, BMP, TIFF, etc.).

### Video (video --output result.mp4)

Each frame is rendered as an ASCII image, and ffmpeg encodes the frames as MP4 (H.264), GIF, or WebM (VP9).

### Terminal (--terminal)

Terminal output is ANSI truecolor (24-bit) text. For video, the screen clears between frames for real-time playback.

### JSON (photo --output result.json)

```json
{
  "cols": 80,
  "rows": 40,
  "cells": [
    {"char": "@", "r": 200, "g": 150, "b": 50},
    ...
  ]
}
```

## Development

The project type-checks with pyright in strict mode:

```bash
uv run pyright
```

Run the tests:

```bash
uv run pytest
```

Regenerate the sample image:

```bash
uv run python examples/generate_sample.py
```

## Dependencies

- [Pillow](https://pillow.readthedocs.io/) for image I/O and character bitmaps
- [opencv-python-headless](https://github.com/opencv/opencv-python) for video frame extraction
- [NumPy](https://numpy.org/) for vectorized math and matching
- [ffmpeg](https://ffmpeg.org/) for video encoding (system dependency, needed only for video output)

## License

MIT. See [LICENSE](LICENSE).
