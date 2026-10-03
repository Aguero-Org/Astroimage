from astroimage.hub.importer import HubbleProduct
from astroimage.hub.sorting import sort_products


def _product(name: str, instrument: str | None, size: int | None) -> HubbleProduct:
    return HubbleProduct(
        product_filename=name,
        data_uri=f"mast:{name}",
        size_bytes=size,
        observation_id="obs",
        proposal_id="100",
        instrument=instrument,
        ra_deg=0,
        dec_deg=0,
    )


def test_sort_by_size_puts_missing_values_last() -> None:
    products = [
        _product("b.fits", "WFC3", 20),
        _product("a.fits", None, None),
        _product("c.fits", "ACS", 5),
    ]
    ordered = sort_products(products, sort="size_bytes", order="asc")
    assert [product.product_filename for product in ordered] == ["c.fits", "b.fits", "a.fits"]


def test_sort_text_is_case_insensitive_and_reversible() -> None:
    products = [
        _product("b.fits", "wfc3", 1),
        _product("a.fits", "ACS", 1),
    ]
    ordered = sort_products(products, sort="instrument", order="desc")
    assert [product.instrument for product in ordered] == ["wfc3", "ACS"]
