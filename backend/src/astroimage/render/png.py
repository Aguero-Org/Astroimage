from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image


def encode_greyscale_png(frame: np.ndarray) -> bytes:
    image = np.asarray(frame, dtype=np.uint8)
    if image.ndim != 2:
        raise ValueError(f"The image must be 2D, received {image.ndim}D")
    return _encode_png(Image.fromarray(image, mode="L"))


def encode_rgb_png(frame: np.ndarray) -> bytes:
    image = np.asarray(frame, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("The image must be (height, width, 3)")
    return _encode_png(Image.fromarray(image, mode="RGB"))


def _encode_png(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
