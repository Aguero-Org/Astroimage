from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from astroimage.hub.importer import HubbleProduct
from astroimage.hub.schema import CandidateSortField, CandidateSortOrder


def sort_by_key[Item](
    items: list[Item],
    *,
    key: Callable[[Item], str | int | datetime | None],
    order: CandidateSortOrder,
) -> list[Item]:
    present = [item for item in items if key(item) is not None]
    missing = [item for item in items if key(item) is None]

    def ordering(item: Item) -> str | int | datetime:
        value = key(item)
        if isinstance(value, str):
            return value.casefold()
        if value is None:
            return 0
        return value

    present.sort(key=ordering, reverse=order == "desc")
    return present + missing


def _field_value(product: HubbleProduct, sort: CandidateSortField) -> str | int | None:
    if sort == "size_bytes":
        return product.size_bytes
    if sort == "instrument":
        return product.instrument
    if sort == "proposal_id":
        return product.proposal_id
    if sort == "filters":
        return product.filters
    if sort == "observed_at":
        return product.observed_at
    return product.product_filename


def sort_products(
    products: list[HubbleProduct],
    *,
    sort: CandidateSortField,
    order: CandidateSortOrder,
) -> list[HubbleProduct]:
    return sort_by_key(products, key=lambda product: _field_value(product, sort), order=order)
