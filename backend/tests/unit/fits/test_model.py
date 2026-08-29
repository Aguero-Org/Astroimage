from astroimage.fits.model import FitsMetadata, FitsTableInfo


def test_fits_metadata_is_immutable() -> None:
    metadata = FitsMetadata(
        source_name="sample.fits",
        hdu_index=0,
        shape=(4, 4),
        telescope="HST",
        instrument="WFC3",
        detector=None,
        filter_name="F814W",
        exptime=100.0,
        date_obs="2020-01-01",
        time_obs=None,
        photflam=None,
        photplam=None,
        photbw=None,
        naxis=2,
        naxis1=4,
        naxis2=4,
        crval1=None,
        crval2=None,
        crpix1=None,
        crpix2=None,
        ctype1=None,
        ctype2=None,
        cd1_1=None,
        cd1_2=None,
        cd2_1=None,
        cd2_2=None,
        cdelt1=None,
        cdelt2=None,
        image_hdus=(0,),
        tables=(FitsTableInfo(index=1, name="CAT", rows=2, columns=("RA", "DEC")),),
        header={"TELESCOP": "HST"},
    )
    assert metadata.telescope == "HST"
    assert metadata.tables[0].columns == ("RA", "DEC")
