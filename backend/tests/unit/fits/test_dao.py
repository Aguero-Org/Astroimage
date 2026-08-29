from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from astroimage.fits.dao import FitsDao


def _write_sample_fits(path: Path) -> None:
    data = np.arange(16, dtype=float).reshape(4, 4)
    primary = fits.PrimaryHDU(data)
    primary.header["TELESCOP"] = "TEST"
    primary.header["INSTRUME"] = "CAM"
    primary.header["FILTER"] = "R"
    primary.header["EXPTIME"] = 12.5
    primary.header["DATE-OBS"] = "2024-01-02"
    primary.writeto(path, overwrite=True)


def test_read_metadata_from_path(tmp_path: Path) -> None:
    fits_path = tmp_path / "sample.fits"
    _write_sample_fits(fits_path)

    metadata = FitsDao().read_metadata_from_path(fits_path)

    assert metadata.source_name == "sample.fits"
    assert metadata.hdu_index == 0
    assert metadata.shape == (4, 4)
    assert metadata.telescope == "TEST"
    assert metadata.instrument == "CAM"
    assert metadata.filter_name == "R"
    assert metadata.exptime == 12.5
    assert metadata.date_obs == "2024-01-02"
    assert metadata.naxis1 == 4
    assert metadata.naxis2 == 4
    assert metadata.image_hdus == (0,)
    assert metadata.header["TELESCOP"] == "TEST"


def test_read_metadata_from_bytes(tmp_path: Path) -> None:
    fits_path = tmp_path / "sample.fits"
    _write_sample_fits(fits_path)
    payload = fits_path.read_bytes()

    metadata = FitsDao().read_metadata_from_bytes(payload, source_name="upload.fits")

    assert metadata.source_name == "upload.fits"
    assert metadata.telescope == "TEST"
    assert isinstance(metadata, type(FitsDao().read_metadata_from_path(fits_path)))


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        FitsDao().read_metadata_from_path(tmp_path / "missing.fits")


def test_invalid_hdu_raises(tmp_path: Path) -> None:
    fits_path = tmp_path / "sample.fits"
    _write_sample_fits(fits_path)
    with pytest.raises(ValueError, match="not a 2D image"):
        FitsDao().read_metadata_from_path(fits_path, hdu_index=9)
