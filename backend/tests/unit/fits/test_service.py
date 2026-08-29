from pathlib import Path

import numpy as np
from astropy.io import fits

from astroimage.fits.model import FitsMetadata
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
    assert model.telescope == "KECK"
    assert schema.telescope == "KECK"
    assert schema.shape == [2, 3]
    assert schema.hdu_index == 0
