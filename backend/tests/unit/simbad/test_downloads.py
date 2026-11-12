from astroimage.simbad.downloads import (
    objects_from_tables,
    simbad_region_key,
    simbad_region_suffix,
    table_from_objects,
)
from astroimage.simbad.model import SimbadObject


def test_region_key_marks_the_object_type() -> None:
    unfiltered = simbad_region_key(
        ra_deg=10,
        dec_deg=20,
        radius_arcsec=60,
        row_limit=25,
        object_type=None,
    )
    filtered = simbad_region_key(
        ra_deg=10,
        dec_deg=20,
        radius_arcsec=60,
        row_limit=25,
        object_type="SNR",
    )

    assert unfiltered == "10.000000:20.000000:60.0:25:type=*"
    assert filtered == "10.000000:20.000000:60.0:25:type=SNR"
    assert simbad_region_suffix("SNR") == ":type=SNR"
    assert simbad_region_suffix(None) == ":type=*"


def test_objects_roundtrip_through_the_download_row() -> None:
    original = SimbadObject(
        main_id="M   1",
        ra_deg=10.0,
        dec_deg=20.0,
        separation_arcsec=1.5,
        otype="SNR",
        otype_text="SuperNova Remnant",
        parallax_mas=1.2,
        reference_count=6602,
    )

    restored = objects_from_tables((table_from_objects([original]),))

    assert restored == [original]
