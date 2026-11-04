from __future__ import annotations

import asyncio
from uuid import UUID

from opentelemetry import trace

from astroimage.fits.reader import FitsReader
from astroimage.fits.service import FitsService
from astroimage.render.colormap import apply_colormap
from astroimage.render.histogram import build_histogram
from astroimage.render.normalization import normalize_to_uint8
from astroimage.render.png import encode_rgb_png
from astroimage.render.schema import HistogramResponse, RenderConfigSchema
from astroimage.render.spec import Histogram, RenderConfig

_tracer = trace.get_tracer("astroimage.render.service")


def domain_config(schema: RenderConfigSchema | None = None) -> RenderConfig:
    source = schema or RenderConfigSchema()
    return RenderConfig(
        stretch=source.stretch,
        limits=source.limits,
        colormap=source.colormap,
        pmin=source.pmin,
        pmax=source.pmax,
        gamma=source.gamma,
    )


def _histogram_response(histogram: Histogram) -> HistogramResponse:
    return HistogramResponse(
        bin_centers=histogram.bin_centers,
        counts=histogram.counts,
        minimum=histogram.minimum,
        maximum=histogram.maximum,
    )


def render_png_bytes(
    reader: FitsReader,
    payload: bytes,
    config: RenderConfig,
    hdu_index: int | None = None,
) -> bytes:
    with _tracer.start_as_current_span("render_png") as span:
        image = reader.read_image_data_from_bytes(payload, hdu_index=hdu_index)
        span.set_attribute("image_hdu_index", image.hdu_index)
        frame = normalize_to_uint8(
            image.data,
            stretch=config.stretch,
            limits=config.limits,
            pmin=config.pmin,
            pmax=config.pmax,
            gamma=config.gamma,
        )
        colored = apply_colormap(frame, config.colormap)
        png = encode_rgb_png(colored)
        span.set_attribute("png_bytes", len(png))
        return png


def histogram_bytes(
    reader: FitsReader,
    payload: bytes,
    bins: int,
    hdu_index: int | None = None,
) -> HistogramResponse:
    with _tracer.start_as_current_span("render_histogram") as span:
        image = reader.read_image_data_from_bytes(payload, hdu_index=hdu_index)
        span.set_attribute("image_hdu_index", image.hdu_index)
        histogram = build_histogram(image.data, bins)
        span.set_attribute("bins", bins)
        return _histogram_response(histogram)


class RenderService:
    def __init__(self, reader: FitsReader, fits: FitsService) -> None:
        self._reader = reader
        self._fits = fits

    async def _payload_for(self, record_id: UUID) -> bytes:
        record = await self._fits.get_record(record_id)
        return await self._fits.get_payload(record)

    async def png_for_record(
        self,
        record_id: UUID,
        *,
        config: RenderConfig,
        hdu_index: int | None = None,
    ) -> bytes:
        payload = await self._payload_for(record_id)
        return await asyncio.to_thread(
            render_png_bytes,
            self._reader,
            payload,
            config,
            hdu_index,
        )

    async def render_png_from_record(
        self,
        record_id: UUID,
        *,
        config: RenderConfigSchema | None = None,
        hdu_index: int | None = None,
    ) -> bytes:
        return await self.png_for_record(
            record_id,
            config=domain_config(config),
            hdu_index=hdu_index,
        )

    async def histogram_from_record(
        self,
        record_id: UUID,
        *,
        bins: int = 256,
        hdu_index: int | None = None,
    ) -> HistogramResponse:
        payload = await self._payload_for(record_id)
        return await asyncio.to_thread(
            histogram_bytes,
            self._reader,
            payload,
            bins,
            hdu_index,
        )

    def render_png_from_bytes(
        self,
        payload: bytes,
        *,
        config: RenderConfig | None = None,
        hdu_index: int | None = None,
    ) -> bytes:
        return render_png_bytes(
            self._reader,
            payload,
            config or domain_config(),
            hdu_index,
        )

    def histogram_from_bytes(
        self,
        payload: bytes,
        *,
        bins: int = 256,
        hdu_index: int | None = None,
    ) -> HistogramResponse:
        return histogram_bytes(self._reader, payload, bins, hdu_index)
