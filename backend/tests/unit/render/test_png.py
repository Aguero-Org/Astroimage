from __future__ import annotations

import struct
import zlib

import numpy as np
import pytest

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


def test_roundtrip_decompression_matches_frame() -> None:
    rng = np.random.default_rng(seed=9)
    frame = rng.integers(0, 256, size=(7, 5), dtype=np.uint8)
    png = encode_greyscale_png(frame)
    width, height = _png_dimensions(png)

    idat_offset = 33
    length = struct.unpack(">I", png[idat_offset : idat_offset + 4])[0]
    assert png[idat_offset + 4 : idat_offset + 8] == b"IDAT"
    payload = png[idat_offset + 8 : idat_offset + 8 + length]
    raw = zlib.decompress(payload)

    row_stride = width + 1
    rows = [raw[row : row + row_stride] for row in range(0, len(raw), row_stride)]

    assert len(rows) == height
    for row, expected in zip(rows, frame, strict=True):
        assert row[0] == 0
        assert np.array_equal(np.frombuffer(row[1:], dtype=np.uint8), expected)


def test_rgb_roundtrip_decompression_matches_frame() -> None:
    rng = np.random.default_rng(seed=4)
    frame = rng.integers(0, 256, size=(6, 4, 3), dtype=np.uint8)
    png = encode_rgb_png(frame)
    width, height = _png_dimensions(png)

    idat_offset = 33
    length = struct.unpack(">I", png[idat_offset : idat_offset + 4])[0]
    assert png[idat_offset + 4 : idat_offset + 8] == b"IDAT"
    payload = png[idat_offset + 8 : idat_offset + 8 + length]
    raw = zlib.decompress(payload)

    row_stride = width * 3 + 1
    rows = [raw[row : row + row_stride] for row in range(0, len(raw), row_stride)]

    assert len(rows) == height
    for row, expected in zip(rows, frame, strict=True):
        assert row[0] == 0
        decoded = np.frombuffer(row[1:], dtype=np.uint8).reshape(width, 3)
        assert np.array_equal(decoded, expected)


def test_non_2d_frame_raises() -> None:
    with pytest.raises(ValueError, match="2D"):
        encode_greyscale_png(np.zeros((2, 2, 2), dtype=np.uint8))


def test_rgb_frame_without_three_channels_raises() -> None:
    with pytest.raises(ValueError, match="3"):
        encode_rgb_png(np.zeros((2, 2, 2), dtype=np.uint8))
