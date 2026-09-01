from __future__ import annotations

from uuid import UUID

import structlog
from opentelemetry import trace

from astroimage.fits.reader import FitsReader
from astroimage.fits.service import FitsService
from astroimage.render.colormap import apply_colormap
from astroimage.render.histogram import build_histogram
from astroimage.render.normalization import normalize_to_uint8
from astroimage.render.png import encode_rgb_png
from astroimage.render.schema import HistogramResponse, RenderConfigSchema

_log = structlog.get_logger("astroimage.render.service")
_tracer = trace.get_tracer("astroimage.render.service")


class RenderService:
    def __init__(self, reader: FitsReader | None = None, fits: FitsService | None = None) -> None:
        self._reader = reader or FitsReader()
        self._fits = fits

    async def _payload_for(self, record_id: UUID) -> bytes:
        if self._fits is None:
            raise RuntimeError("FitsService not configured")
        record = await self._fits.get_record(record_id)
        return await self._fits.get_payload(record)

    async def render_png_from_record(
        self,
        record_id: UUID,
        *,
        config: RenderConfigSchema | None = None,
        hdu_index: int | None = None,
    ) -> bytes:
        payload = await self._payload_for(record_id)
        return self.render_png_from_bytes(payload, config=config, hdu_index=hdu_index)

    async def histogram_from_record(
        self,
        record_id: UUID,
        *,
        bins: int = 256,
        hdu_index: int | None = None,
    ) -> HistogramResponse:
        payload = await self._payload_for(record_id)
        return self.histogram_from_bytes(payload, bins=bins, hdu_index=hdu_index)

    def render_png_from_bytes(
        self,
        payload: bytes,
        *,
        config: RenderConfigSchema | None = None,
        hdu_index: int | None = None,
    ) -> bytes:
        with _tracer.start_as_current_span("render_png") as span:
            render_config = config or RenderConfigSchema()
            image = self._reader.read_image_data_from_bytes(payload, hdu_index=hdu_index)
            span.set_attribute("image_hdu_index", image.hdu_index)
            frame = normalize_to_uint8(
                image.data,
                stretch=render_config.stretch,
                limits=render_config.limits,
                pmin=render_config.pmin,
                pmax=render_config.pmax,
                gamma=render_config.gamma,
            )
            colored = apply_colormap(frame, render_config.colormap)
            png = encode_rgb_png(colored)
            span.set_attribute("png_bytes", len(png))
            return png

    def histogram_from_bytes(
        self,
        payload: bytes,
        *,
        bins: int = 256,
        hdu_index: int | None = None,
    ) -> HistogramResponse:
        with _tracer.start_as_current_span("render_histogram") as span:
            image = self._reader.read_image_data_from_bytes(payload, hdu_index=hdu_index)
            span.set_attribute("image_hdu_index", image.hdu_index)
            histogram = build_histogram(image.data, bins)
            span.set_attribute("bins", bins)
            return histogram
