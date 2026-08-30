from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from astroimage.fits.model import FitsImageData, FitsMetadata
from astroimage.fits.service import FitsService


def _write_sample_fits(path: Path) -> None:
    data = np.ones((2, 3), dtype=float)
    hdu = fits.PrimaryHDU(data)
    hdu.header["TELESCOP"] = "KECK"
    hdu.writeto(path, overwrite=True)


def test_service_returns_model_and_schema(tmp_path: Path) -> None:
    fits_path = tmp_path / "keck.fits"
    _write_sample_fits(fits_path)
    service = FitsService()

    model = service.metadata_from_path(fits_path)
    schema = service.to_schema(model)

    assert isinstance(model, FitsMetadata)
    assert model.instrument.telescope == "KECK"
    assert schema.instrument.telescope == "KECK"
    assert schema.image.shape == [2, 3]
    assert schema.hdus.selected == model.hdus.selected


def test_service_image_data_from_path(tmp_path: Path) -> None:
    fits_path = tmp_path / "keck.fits"
    _write_sample_fits(fits_path)

    image = FitsService().image_data_from_path(fits_path)

    assert isinstance(image, FitsImageData)
    assert image.source_name == "keck.fits"
    assert image.hdu_index == 0
    assert image.data.shape == (2, 3)
    assert np.issubdtype(image.data.dtype, np.floating)


def test_service_image_data_from_bytes(tmp_path: Path) -> None:
    fits_path = tmp_path / "keck.fits"
    _write_sample_fits(fits_path)

    image = FitsService().image_data_from_bytes(
        fits_path.read_bytes(),
        source_name="upload.fits",
        hdu_index=0,
    )

    assert image.source_name == "upload.fits"
    assert image.hdu_index == 0
    assert np.allclose(image.data, np.ones((2, 3)))


def test_service_image_data_empty_payload_raises() -> None:
    with pytest.raises(ValueError, match="Empty"):
        FitsService().image_data_from_bytes(b"")
