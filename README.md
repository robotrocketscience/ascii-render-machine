# ASCII Render Machine

Convert images and videos to ASCII art using shape-vector 6D matching, based on the technique described in [ASCII Rendering](https://alexharri.com/blog/ascii-rendering) by Alex Harri.

## How it works

The algorithm divides each image into a grid of cells. For each cell, it computes a 6-dimensional "shape vector" by measuring average brightness within 6 circular sampling regions arranged in a 2x3 pattern (2 columns, 3 rows, vertically staggered for better coverage).

Every printable ASCII character (32-126) is pre-rendered to a bitmap and sampled identically, producing a lookup table of 6D vectors. For each image cell, the algorithm finds the character whose vector has the minimum Euclidean distance to the cell's vector. The average RGB color of the cell is preserved, so the output is full color.

### Pipeline

1. **Character atlas** -- Render all printable ASCII characters at a fixed font size. Compute 6D shape vectors. Normalize and apply a contrast exponent to sharpen distinctions.
2. **Image sampling** -- Divide the input image into a grid. For each cell, compute the 6D shape vector from the grayscale channel and the average RGB from the color channels.
3. **Matching** -- Vectorized nearest-neighbor search in 6D space using expanded Euclidean distance.
4. **Output** -- Emit as PNG/JPG image, ANSI truecolor terminal text, MP4/GIF video, or JSON.

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:robotrocketscience/ascii-render-machine.git
cd ascii-render-machine
uv sync
```

Video output requires [ffmpeg](https://ffmpeg.org/) installed on your system.

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

## CLI reference

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
| `--output PATH` | none | Output file (.png, .jpg, or .json) |
| `--font-size N` | 16 | Font size used for the character atlas and image rendering |
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
| `--output PATH` | none | Output video file (.mp4, .gif, or .webm). Requires ffmpeg. |
| `--font-size N` | 16 | Font size used for the character atlas |
| `--contrast F` | 1.2 | Contrast exponent |

## Output formats

### Image (photo --output result.png)

Renders ASCII art as colored monospace characters on a black background. Supports any format Pillow can write (PNG, JPG, BMP, TIFF, etc.).

### Video (video --output result.mp4)

Each frame is converted to ASCII art, rendered as an image, and piped to ffmpeg for encoding. Supports MP4 (H.264), GIF, and WebM (VP9).

### Terminal (--terminal)

Prints ANSI truecolor (24-bit) text directly to the terminal. For video, clears the screen between frames for real-time playback.

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

### Type checking

The project uses pyright in strict mode:

```bash
uv run pyright
```

### Tests

```bash
uv run pytest
```

### Generate the sample image

```bash
uv run python examples/generate_sample.py
```

## Dependencies

- [Pillow](https://pillow.readthedocs.io/) -- Image loading, character bitmap rendering, and image output
- [opencv-python-headless](https://github.com/opencv/opencv-python) -- Video frame extraction
- [NumPy](https://numpy.org/) -- Vectorized shape vector computation and matching
- [ffmpeg](https://ffmpeg.org/) -- Video encoding (system dependency, required for video output only)

## License

MIT -- see [LICENSE](LICENSE).
