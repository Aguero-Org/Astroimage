from astroimage.fits.model import (
    FitsHduInfo,
    FitsImageInfo,
    FitsInstrumentInfo,
    FitsMetadata,
    FitsTableInfo,
    FitsWcsInfo,
)


def test_fits_metadata_nested_groups() -> None:
    metadata = FitsMetadata(
        source_name="sample.fits",
        image=FitsImageInfo(shape=[4, 4], unit="electron/s", datamin=0.0, datamax=10.0),
        instrument=FitsInstrumentInfo(telescope="HST", instrument="WFC3", filter_name="F814W"),
        hdus=FitsHduInfo(selected=0, image_indices=[0]),
        tables=[FitsTableInfo(index=1, name="CAT", rows=2, columns=["RA", "DEC"])],
        wcs=FitsWcsInfo(present=False),
        header={"TELESCOP": "HST"},
    )
    assert metadata.instrument.telescope == "HST"
    assert metadata.image.shape == [4, 4]
    assert metadata.tables[0].columns == ["RA", "DEC"]
    assert metadata.hdus.selected == 0


def test_instrument_coerces_values() -> None:
    instrument = FitsInstrumentInfo.model_validate({"telescope": "  VLT  ", "exptime": "12.5"})
    assert instrument.telescope == "VLT"
    assert instrument.exptime == 12.5
