# ASCII Render Machine

ascii-render-machine converts images and videos to full-color ASCII art by matching each cell of the input to the printable ASCII character with the closest 6D shape vector. The technique comes from [ASCII Rendering](https://alexharri.com/blog/ascii-rendering) by Alex Harri.

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:robotrocketscience/ascii-render-machine.git
cd ascii-render-machine
uv sync
```

Video output also requires [ffmpeg](https://ffmpeg.org/) on your system.

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

The renderer divides the image into a grid of cells. For each cell it computes a 6-dimensional shape vector: the average brightness inside 6 circular sampling regions laid out in a 2x3 pattern (2 columns, 3 rows), with the regions vertically staggered for better coverage.

Every printable ASCII character (32-126) is pre-rendered to a bitmap and sampled the same way, which gives a lookup table of 6D vectors. Each cell gets the character whose vector has the smallest Euclidean distance to the cell's vector. The cell keeps its average RGB color, so the output is in full color.

The pipeline runs in this order:

1. Build the character atlas. Render all printable ASCII characters at a fixed font size, compute their 6D shape vectors, then normalize the vectors and apply a contrast exponent to sharpen the differences between characters.
2. Sample the image. Divide the input into a grid and compute each cell's 6D shape vector from the grayscale channel and its average RGB from the color channels.
3. Match. Run a vectorized nearest-neighbor search in 6D space using expanded Euclidean distance.
4. Write the output as a PNG/JPG image, ANSI truecolor terminal text, MP4/GIF video, or JSON.

## CLI reference

### Convert a single image with `photo`

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

### Convert a video with `video`

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

Draws the ASCII art as colored monospace characters on a black background. Any format Pillow can write works (PNG, JPG, BMP, TIFF, etc.).

### Video (video --output result.mp4)

Converts each frame to ASCII art, renders it as an image, and pipes it to ffmpeg for encoding. Supports MP4 (H.264), GIF, and WebM (VP9).

### Terminal (--terminal)

Prints ANSI truecolor (24-bit) text directly to the terminal. For video, the screen is cleared between frames for real-time playback.

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

- [Pillow](https://pillow.readthedocs.io/) for image loading, character bitmap rendering, and image output
- [opencv-python-headless](https://github.com/opencv/opencv-python) for video frame extraction
- [NumPy](https://numpy.org/) for vectorized shape vector computation and matching
- [ffmpeg](https://ffmpeg.org/) for video encoding (system dependency, needed only for video output)

## License

MIT. See [LICENSE](LICENSE).
