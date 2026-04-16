# ASCII Render Machine

Convert images and videos to ASCII art using shape-vector 6D matching, based on the technique described in [ASCII Rendering](https://alexharri.com/blog/ascii-rendering) by Alex Harri.

## How It Works

The algorithm divides each image into a grid of cells. For each cell, it computes a 6-dimensional "shape vector" by measuring average brightness within 6 circular sampling regions arranged in a 2x3 pattern (2 columns, 3 rows, vertically staggered for better coverage).

Every printable ASCII character (32-126) is pre-rendered to a bitmap and sampled identically, producing a lookup table of 6D vectors. For each image cell, the algorithm finds the character whose vector has the minimum Euclidean distance to the cell's vector. The average RGB color of the cell is preserved, enabling full-color ANSI terminal output.

### Pipeline

1. **Character Atlas** -- Render all printable ASCII characters at a fixed font size. Compute 6D shape vectors. Normalize and apply a contrast exponent to sharpen distinctions.
2. **Image Sampling** -- Divide the input image into a grid. For each cell, compute the 6D shape vector from the grayscale channel and the average RGB from the color channels.
3. **Matching** -- Vectorized nearest-neighbor search in 6D space using expanded Euclidean distance.
4. **Output** -- Emit as ANSI truecolor terminal text, JSON, or binary chunks for video playback.

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:robotrocketscience/ascii-render-machine.git
cd ascii-render-machine
uv sync
```

## Quick Start

```bash
# Render an image to the terminal
uv run ascii-render-machine photo examples/sample.jpg --cols 80 --terminal

# Save as JSON
uv run ascii-render-machine photo examples/sample.jpg --cols 120 --output result.json

# Convert video to chunked binary files
uv run ascii-render-machine video input.mp4 --cols 120 --rows 33 --fps 10 --output-dir ./frames/

# Play video as ASCII in the terminal
uv run ascii-render-machine video input.mp4 --cols 80 --terminal --fps 10
```

## CLI Reference

### `photo` -- Convert a single image

```
ascii-render-machine photo INPUT [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--cols N` | 80 | Number of character columns |
| `--rows N` | auto | Number of character rows (auto-calculated from aspect ratio if omitted) |
| `--terminal` | off | Render to terminal with ANSI truecolor |
| `--no-color` | off | Disable color in terminal output |
| `--output PATH` | none | Write JSON output to a file |
| `--font-size N` | 16 | Font size used for the character atlas |
| `--contrast F` | 1.2 | Contrast exponent for shape vector enhancement |

### `video` -- Convert a video

```
ascii-render-machine video INPUT [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--cols N` | 80 | Number of character columns |
| `--rows N` | auto | Number of character rows |
| `--fps N` | 10 | Target frames per second |
| `--terminal` | off | Play ASCII video in the terminal |
| `--output-dir DIR` | none | Write chunked binary files and manifest to this directory |
| `--font-size N` | 16 | Font size used for the character atlas |
| `--contrast F` | 1.2 | Contrast exponent |

## Output Formats

### JSON (photo)

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

### Binary Chunks (video)

Each chunk file contains:
- `uint16` frame count (little-endian)
- Per frame: `[char_code, R, G, B]` x (rows * cols) followed by a flame mask bitfield of `ceil(rows * cols / 8)` zero bytes

A `manifest.json` accompanies the chunks:

```json
{
  "cols": 120,
  "rows": 33,
  "fps": 10,
  "total_frames": 300,
  "chunk_count": 3,
  "frame_size": 15844,
  "flame_bytes": 495,
  "chunks": [
    {"file": "chunk_000.bin", "frames": 100, "size": 1584402},
    ...
  ]
}
```

## Development

### Type Checking

The project uses pyright in strict mode:

```bash
uv run pyright
```

### Tests

```bash
uv run pytest
```

### Generate Sample Image

```bash
cd ascii-render-machine
uv run python examples/generate_sample.py
```

## Dependencies

- [Pillow](https://pillow.readthedocs.io/) -- Image loading and character bitmap rendering
- [opencv-python-headless](https://github.com/opencv/opencv-python) -- Video frame extraction
- [NumPy](https://numpy.org/) -- Vectorized shape vector computation and matching

## License

MIT -- see [LICENSE](LICENSE).
