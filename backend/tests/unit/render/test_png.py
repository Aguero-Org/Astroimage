from __future__ import annotations

import struct
from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from astroimage.render.png import encode_greyscale_png, encode_rgb_png

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_dimensions(png: bytes) -> tuple[int, int]:
    return struct.unpack(">II", png[16:24])


def test_encodes_png_signature() -> None:
    png = encode_greyscale_png(np.zeros((4, 4), dtype=np.uint8))

    assert png.startswith(_PNG_SIGNATURE)


def test_ihdr_carries_image_dimensions() -> None:
    frame = np.zeros((8, 6), dtype=np.uint8)
    png = encode_greyscale_png(frame)

    width, height = _png_dimensions(png)

    assert (width, height) == (6, 8)


def test_greyscale_roundtrip_matches_frame() -> None:
    rng = np.random.default_rng(seed=9)
    frame = rng.integers(0, 256, size=(7, 5), dtype=np.uint8)
    png = encode_greyscale_png(frame)

    decoded = np.asarray(Image.open(BytesIO(png)).convert("L"), dtype=np.uint8)

    assert decoded.shape == frame.shape
    assert np.array_equal(decoded, frame)


def test_rgb_roundtrip_matches_frame() -> None:
    rng = np.random.default_rng(seed=4)
    frame = rng.integers(0, 256, size=(6, 4, 3), dtype=np.uint8)
    png = encode_rgb_png(frame)

    decoded = np.asarray(Image.open(BytesIO(png)).convert("RGB"), dtype=np.uint8)

    assert decoded.shape == frame.shape
    assert np.array_equal(decoded, frame)


def test_non_2d_frame_raises() -> None:
    with pytest.raises(ValueError, match="2D"):
        encode_greyscale_png(np.zeros((2, 2, 2), dtype=np.uint8))


def test_rgb_frame_without_three_channels_raises() -> None:
    with pytest.raises(ValueError) as excinfo:
        encode_rgb_png(np.zeros((2, 2, 2), dtype=np.uint8))

    assert str(excinfo.value) == "The image must be (height, width, 3)"


def test_greyscale_converts_float_frame_to_uint8() -> None:
    frame = np.array([[0.0, 127.9, 255.0]])

    png = encode_greyscale_png(frame)

    decoded = np.asarray(Image.open(BytesIO(png)).convert("L"), dtype=np.uint8)
    assert np.array_equal(decoded, np.array([[0, 127, 255]], dtype=np.uint8))


def test_rgb_converts_float_frame_to_uint8() -> None:
    frame = np.array([[[0.0, 127.9, 255.0]]])

    png = encode_rgb_png(frame)

    decoded = np.asarray(Image.open(BytesIO(png)).convert("RGB"), dtype=np.uint8)
    assert np.array_equal(decoded, np.array([[[0, 127, 255]]], dtype=np.uint8))
