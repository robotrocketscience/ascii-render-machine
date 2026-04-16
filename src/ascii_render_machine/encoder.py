"""Image-to-ASCII grid encoder."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from PIL import Image

from ascii_render_machine.charset import atlas_matrix, build_atlas
from ascii_render_machine.matcher import match_grid
from ascii_render_machine.sampler import sample_image_cells
from ascii_render_machine.types import Cell, CharEntry, EncoderConfig, Frame


class Encoder:
    """Stateful encoder that caches the character atlas across calls."""

    def __init__(self, config: EncoderConfig) -> None:
        self.config = config
        self._atlas: list[CharEntry] = build_atlas(
            font_size=config.font_size,
            contrast_exp=config.contrast_exp,
        )
        self._atlas_mat: npt.NDArray[np.float64] = atlas_matrix(self._atlas)

    def encode_image(self, img: Image.Image) -> Frame:
        """Convert a PIL Image to an ASCII Frame."""
        rows = self.config.effective_rows(img.height, img.width)
        cols = self.config.cols

        # Grayscale for shape matching.
        gray_img = img.convert("L")
        gray: npt.NDArray[np.float64] = (
            np.array(gray_img, dtype=np.float64) / 255.0
        )

        # RGB for color sampling.
        rgb_img = img.convert("RGB")
        rgb: npt.NDArray[np.uint8] = np.array(rgb_img, dtype=np.uint8)

        # Sample shape vectors.
        vectors = sample_image_cells(gray, rows, cols)

        # Match to atlas characters.
        indices = match_grid(vectors, self._atlas, self._atlas_mat)

        # Build frame.
        h, w = gray.shape
        cell_h = max(1, h // rows)
        cell_w = max(1, w // cols)

        frame = Frame(cols=cols, rows=rows)
        for r in range(rows):
            y0 = r * cell_h
            y1 = min(y0 + cell_h, h)
            for c in range(cols):
                x0 = c * cell_w
                x1 = min(x0 + cell_w, w)
                region = rgb[y0:y1, x0:x1]
                mean_rgb = region.mean(axis=(0, 1))
                char = self._atlas[int(indices[r, c])].char
                frame.cells.append(
                    Cell(
                        char=char,
                        r=int(mean_rgb[0]),
                        g=int(mean_rgb[1]),
                        b=int(mean_rgb[2]),
                    )
                )
        return frame

    def encode_array(
        self,
        rgb_array: npt.NDArray[np.uint8],
        rows: int | None = None,
    ) -> Frame:
        """Encode a raw numpy RGB array (H, W, 3) to an ASCII Frame."""
        img = Image.fromarray(rgb_array, mode="RGB")
        if rows is not None:
            old_rows = self.config.rows
            object.__setattr__(self.config, "rows", rows)
            frame = self.encode_image(img)
            object.__setattr__(self.config, "rows", old_rows)
            return frame
        return self.encode_image(img)
