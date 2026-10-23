from __future__ import annotations

_RA_DECIMALS = 6
_RADIUS_DECIMALS = 1


def region_key(
    *,
    ra_deg: float,
    dec_deg: float,
    radius_arcsec: float,
    row_limit: int,
) -> str:
    ra_text = f"{ra_deg:.{_RA_DECIMALS}f}"
    dec_text = f"{dec_deg:.{_RA_DECIMALS}f}"
    radius_text = f"{radius_arcsec:.{_RADIUS_DECIMALS}f}"
    return f"{ra_text}:{dec_text}:{radius_text}:{row_limit}"
