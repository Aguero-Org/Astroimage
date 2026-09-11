from __future__ import annotations

import numpy as np
import pytest

from astroimage.render.colormap import COLORMAPS, apply_colormap

_NAMES = tuple(COLORMAPS.keys())


def test_colormaps_have_expected_shape_and_dtype() -> None:
    assert set(COLORMAPS) == {"grey", "inverse", "heat", "rainbow", "cube_helix"}
    for name, lut in COLORMAPS.items():
        assert lut.shape == (256, 3), name
        assert lut.dtype == np.uint8


@pytest.mark.parametrize("name", _NAMES)
def test_colormaps_are_finite(name: str) -> None:
    assert np.all(np.isfinite(COLORMAPS[name]))


def test_grey_and_inverse_are_opposites() -> None:
    assert (COLORMAPS["grey"][0] == (0, 0, 0)).all()
    assert (COLORMAPS["grey"][-1] == (255, 255, 255)).all()
    assert (COLORMAPS["inverse"][0] == (255, 255, 255)).all()
    assert (COLORMAPS["inverse"][-1] == (0, 0, 0)).all()


def test_heat_runs_black_to_white() -> None:
    heat = COLORMAPS["heat"]
    assert (heat[0] == (0, 0, 0)).all()
    assert (heat[-1] == (255, 255, 255)).all()
    assert len({tuple(row) for row in heat}) == 256


def test_rainbow_goes_blue_to_red() -> None:
    rainbow = COLORMAPS["rainbow"]
    low_channel = rainbow[0]
    high_channel = rainbow[-1]
    assert low_channel[2] >= 200 and low_channel[0] <= 50
    assert high_channel[0] >= 200 and high_channel[2] <= 50


def test_cube_helix_endpoints() -> None:
    cube_helix = COLORMAPS["cube_helix"]
    assert cube_helix[0][2] >= cube_helix[0][0]
    assert cube_helix[-1][0] >= cube_helix[-1][2]


def test_apply_colormap_maps_frame_to_rgb() -> None:
    frame = np.array([[0, 128, 255]], dtype=np.uint8)

    colored = apply_colormap(frame, "grey")

    assert colored.shape == (1, 3, 3)
    assert (colored[0, 0] == (0, 0, 0)).all()
    assert (colored[0, 1] == (128, 128, 128)).all()
    assert (colored[0, 2] == (255, 255, 255)).all()


def test_apply_colormap_unknown_name_raises() -> None:
    with pytest.raises(KeyError):
        apply_colormap(np.zeros((1, 1), dtype=np.uint8), "magma")  # type: ignore[arg-type]
