from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from astroimage.fits.dao import FitsDao
from astroimage.fits.model import FitsImageData, FitsMetadata


def _write_sample_fits(path: Path) -> None:
    data = np.arange(16, dtype=float).reshape(4, 4)
    primary = fits.PrimaryHDU(data)
    primary.header["TELESCOP"] = "TEST"
    primary.header["INSTRUME"] = "CAM"
    primary.header["FILTER"] = "R"
    primary.header["EXPTIME"] = 12.5
    primary.header["DATE-OBS"] = "2024-01-02"
    primary.header["BUNIT"] = "count"
    primary.header["DATAMIN"] = 0.0
    primary.header["DATAMAX"] = 15.0
    primary.header["DATAMEAN"] = 7.5
    primary.header["MEDIAN"] = 7.5
    primary.header["BACKGRND"] = 1.0
    primary.header["PHOTFLAM"] = 1e-19
    primary.header["CRVAL1"] = 150.0
    primary.header["CRVAL2"] = 2.5
    primary.header["CRPIX1"] = 2.0
    primary.header["CRPIX2"] = 2.0
    primary.header["CTYPE1"] = "RA---TAN"
    primary.header["CTYPE2"] = "DEC--TAN"
    primary.header["CD1_1"] = -0.001
    primary.header["CD1_2"] = 0.0
    primary.header["CD2_1"] = 0.0
    primary.header["CD2_2"] = 0.001
    primary.writeto(path, overwrite=True)


def test_read_metadata_from_path(tmp_path: Path) -> None:
    fits_path = tmp_path / "sample.fits"
    _write_sample_fits(fits_path)

    metadata = FitsDao().read_metadata_from_path(fits_path)

    assert isinstance(metadata, FitsMetadata)
    assert metadata.source_name == "sample.fits"
    assert metadata.hdus.selected == 0
    assert metadata.hdus.image_indices == [0]
    assert metadata.image.shape == [4, 4]
    assert metadata.image.unit == "count"
    assert metadata.image.datamin == 0.0
    assert metadata.image.datamax == 15.0
    assert metadata.image.datamean == 7.5
    assert metadata.image.median == 7.5
    assert metadata.image.background == 1.0
    assert metadata.instrument.telescope == "TEST"
    assert metadata.instrument.instrument == "CAM"
    assert metadata.instrument.filter_name == "R"
    assert metadata.instrument.exptime == 12.5
    assert metadata.instrument.date_obs == "2024-01-02"
    assert metadata.photometry.photflam == 1e-19
    assert metadata.header["TELESCOP"] == "TEST"
    assert metadata.wcs.present is True
    assert metadata.wcs.crval == [150.0, 2.5]
    assert metadata.wcs.crpix == [2.0, 2.0]
    assert metadata.wcs.ctype == ["RA---TAN", "DEC--TAN"]
    assert metadata.wcs.cd is not None
    assert metadata.wcs.cd[0][0] == -0.001
    assert metadata.wcs.cd[1][1] == 0.001


def test_read_metadata_from_bytes(tmp_path: Path) -> None:
    fits_path = tmp_path / "sample.fits"
    _write_sample_fits(fits_path)
    payload = fits_path.read_bytes()

    metadata = FitsDao().read_metadata_from_bytes(payload, source_name="upload.fits")

    assert metadata.source_name == "upload.fits"
    assert metadata.instrument.telescope == "TEST"
    assert metadata.wcs.crval == [150.0, 2.5]


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        FitsDao().read_metadata_from_path(tmp_path / "missing.fits")


def test_invalid_hdu_raises(tmp_path: Path) -> None:
    fits_path = tmp_path / "sample.fits"
    _write_sample_fits(fits_path)
    with pytest.raises(ValueError, match="not a 2D image"):
        FitsDao().read_metadata_from_path(fits_path, hdu_index=9)


def test_wcs_absent(tmp_path: Path) -> None:
    fits_path = tmp_path / "plain.fits"
    fits.PrimaryHDU(np.ones((3, 3))).writeto(fits_path, overwrite=True)

    metadata = FitsDao().read_metadata_from_path(fits_path)

    assert metadata.wcs.present is False
    assert metadata.wcs.crval is None
    assert metadata.wcs.cd is None
    assert metadata.wcs.cdelt is None


def test_read_image_data_from_path(tmp_path: Path) -> None:
    fits_path = tmp_path / "sample.fits"
    _write_sample_fits(fits_path)

    image = FitsDao().read_image_data_from_path(fits_path)

    assert isinstance(image, FitsImageData)
    assert image.source_name == "sample.fits"
    assert image.hdu_index == 0
    assert image.data.shape == (4, 4)
    assert np.allclose(image.data, np.arange(16, dtype=float).reshape(4, 4))


def test_read_image_data_from_bytes(tmp_path: Path) -> None:
    fits_path = tmp_path / "sample.fits"
    _write_sample_fits(fits_path)

    image = FitsDao().read_image_data_from_bytes(
        fits_path.read_bytes(),
        source_name="upload.fits",
        hdu_index=0,
    )

    assert image.source_name == "upload.fits"
    assert image.hdu_index == 0
    assert image.data.shape == (4, 4)
    assert np.issubdtype(image.data.dtype, np.floating)


def test_read_image_data_selects_explicit_hdu(tmp_path: Path) -> None:
    primary = fits.PrimaryHDU(np.zeros((8, 8)))
    science = fits.ImageHDU(np.ones((16, 16)))
    fits_path = tmp_path / "multi.fits"
    fits.HDUList([primary, science]).writeto(fits_path)

    image = FitsDao().read_image_data_from_path(fits_path, hdu_index=1)

    assert image.hdu_index == 1
    assert image.data.shape == (16, 16)


def test_read_image_data_invalid_hdu_raises(tmp_path: Path) -> None:
    fits_path = tmp_path / "sample.fits"
    _write_sample_fits(fits_path)

    with pytest.raises(ValueError, match="not a 2D image"):
        FitsDao().read_image_data_from_path(fits_path, hdu_index=9)


def test_read_image_data_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        FitsDao().read_image_data_from_path(tmp_path / "missing.fits")


def test_read_image_data_garbage_raises() -> None:
    with pytest.raises(OSError):
        FitsDao().read_image_data_from_bytes(b"not-a-fits-file")
