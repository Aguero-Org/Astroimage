from astroimage.hub.importer import HubbleProduct
from astroimage.hub.sorting import sort_by_key, sort_products


def _product(filename: str, **overrides: object) -> HubbleProduct:
    values: dict[str, object] = {
        "product_filename": filename,
        "data_uri": f"mast:{filename}",
        "size_bytes": 10,
        "observation_id": "obs",
        "proposal_id": "100",
        "instrument": "WFC3",
        "ra_deg": 1.0,
        "dec_deg": 2.0,
        "filters": "F814W",
        "observed_at": "2020-01-02",
    }
    values.update(overrides)
    return HubbleProduct(**values)  # type: ignore[arg-type]


def test_sort_by_key_keeps_missing_values_last() -> None:
    items = ["b", None, "A"]

    ordered = sort_by_key(items, key=lambda item: item, order="asc")

    assert ordered == ["A", "b", None]


def test_sort_products_covers_each_field() -> None:
    light = _product("b.fits", size_bytes=1, instrument=None, filters=None, observed_at=None)
    heavy = _product("a.fits", size_bytes=9, proposal_id="2", instrument="ACS")

    by_name = sort_products([heavy, light], sort="product_filename", order="asc")
    by_size = sort_products([light, heavy], sort="size_bytes", order="desc")
    by_instrument = sort_products([heavy, light], sort="instrument", order="asc")
    by_proposal = sort_products([heavy, light], sort="proposal_id", order="desc")
    by_filters = sort_products([light, heavy], sort="filters", order="asc")
    by_observed = sort_products([light, heavy], sort="observed_at", order="asc")

    assert [item.product_filename for item in by_name] == ["a.fits", "b.fits"]
    assert [item.size_bytes for item in by_size] == [9, 1]
    assert by_instrument[-1].instrument is None
    assert [item.proposal_id for item in by_proposal] == ["2", "100"]
    assert by_filters[-1].filters is None
    assert by_observed[-1].observed_at is None
