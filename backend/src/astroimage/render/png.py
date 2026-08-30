from __future__ import annotations

import struct
import zlib

import numpy as np

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + tag
        + payload
        + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    )


def _encode_png(image: np.ndarray, color_type: int) -> bytes:
    height, width = image.shape[:2]
    header = struct.pack(
        ">IIBBBBB",
        width,
        height,
        8,
        color_type,
        0,
        0,
        0,
    )
    rows = b"".join(b"\x00" + image[row_index].tobytes() for row_index in range(height))
    compressed = zlib.compress(rows, level=6)
    return (
        _PNG_SIGNATURE
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )


def encode_greyscale_png(frame: np.ndarray) -> bytes:
    image = np.asarray(frame, dtype=np.uint8)
    if image.ndim != 2:
        raise ValueError(f"la imagen debe ser 2D, se recibió {image.ndim}D")
    return _encode_png(image, color_type=0)


def encode_rgb_png(frame: np.ndarray) -> bytes:
    image = np.asarray(frame, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("la imagen debe ser (alto, ancho, 3)")
    return _encode_png(image, color_type=2)
