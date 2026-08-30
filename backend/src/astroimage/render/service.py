from __future__ import annotations

from astroimage.fits.service import FitsService
from astroimage.render.normalization import normalize_to_uint8
from astroimage.render.png import encode_greyscale_png
from astroimage.render.schema import RenderConfigSchema


class RenderService:
    def __init__(self, fits_service: FitsService | None = None) -> None:
        self._fits = fits_service or FitsService()

    def render_png_from_bytes(
        self,
        payload: bytes,
        *,
        config: RenderConfigSchema | None = None,
        hdu_index: int | None = None,
    ) -> bytes:
        render_config = config or RenderConfigSchema()
        image = self._fits.image_data_from_bytes(payload, hdu_index=hdu_index)
        frame = normalize_to_uint8(
            image.data,
            stretch=render_config.stretch,
            pmin=render_config.pmin,
            pmax=render_config.pmax,
            gamma=render_config.gamma,
        )
        return encode_greyscale_png(frame)
