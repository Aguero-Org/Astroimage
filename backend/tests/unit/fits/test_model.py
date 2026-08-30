from astroimage.fits.model import FitsRecord


def test_fits_record_persists_object_key_and_filename() -> None:
    record = FitsRecord(
        object_key="fits/sample.fits",
        original_filename="sample.fits",
        size_bytes=128,
        metadata_payload={"source_name": "sample.fits"},
    )
    assert record.object_key == "fits/sample.fits"
    assert record.original_filename == "sample.fits"
    assert record.size_bytes == 128
    assert record.metadata_payload["source_name"] == "sample.fits"
