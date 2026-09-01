from __future__ import annotations

import asyncio
import io
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import quote

import astropy.units as u
import httpx
import structlog
from astropy.coordinates import Angle, SkyCoord
from astropy.io import fits
from astroquery.mast import Observations
from opentelemetry import trace

_log = structlog.get_logger("astroimage.hub.importer")
_tracer = trace.get_tracer("astroimage.hub.importer")

SEARCH_RADIUS_DEG = 0.05
DOWNLOAD_TIMEOUT_SECONDS = 300.0
MAST_COLLECTION = "HST"
MAST_SEARCH_PAGESIZE = 10
MAST_SEARCH_MAX_PAGES = 10
MAST_DOWNLOAD_URL = "https://mast.stsci.edu/api/v0.1/Download/file"
MIN_PRODUCT_SIZE_BYTES = 100 * 1024 * 1024
_FITS_SUFFIXES = (".fits", ".fit")
_SCIENCE_PRODUCT_TYPE = "SCIENCE"


class HubbleNotFoundError(ValueError):
    """Raised when a target has no Hubble imaging or cannot be resolved."""


class HubbleDownloadError(RuntimeError):
    """Raised when a Hubble product cannot be downloaded."""


class _MastObservations(Protocol):
    def query_criteria(
        self,
        *,
        coordinates: Any,
        radius: Any,
        obs_collection: str,
        pagesize: int,
        page: int,
    ) -> Any: ...
    def get_product_list(self, observations: Any) -> Any: ...


@dataclass(frozen=True)
class HubbleProduct:
    product_filename: str
    data_uri: str
    size_bytes: int | None
    observation_id: str
    proposal_id: str
    instrument: str | None
    ra_deg: float
    dec_deg: float


@dataclass(frozen=True)
class ImportedImage:
    payload: bytes
    filename: str
    target_name: str
    ra_deg: float
    dec_deg: float
    observation_id: str
    proposal_id: str
    instrument: str | None


def _row_str(row: Any, key: str) -> str | None:
    value = row[key]
    if value is None:
        return None
    return str(value)


def _row_float(row: Any, key: str) -> float:
    return float(row[key])


def _row_int(row: Any, key: str) -> int | None:
    value = row[key]
    if value is None:
        return None
    return int(value)


def _is_science_fits(product: Any) -> bool:
    if str(product["productType"]) != _SCIENCE_PRODUCT_TYPE:
        return False
    filename = str(product["productFilename"] or "")
    lowered = filename.lower()
    return lowered.endswith(_FITS_SUFFIXES) and not lowered.endswith((".fits.gz", ".fit.gz"))


def _best_science_product(products: list[HubbleProduct]) -> HubbleProduct | None:
    for product in products:
        if product.size_bytes is not None and product.size_bytes >= MIN_PRODUCT_SIZE_BYTES:
            return product
    return None


def _product_from_row(product: Any, hst_rows: Any) -> HubbleProduct | None:
    if not _is_science_fits(product):
        return None
    observation = next(
        (row for row in hst_rows if str(row["obs_id"]) == str(product["obs_id"])),
        None,
    )
    if observation is None:
        return None
    return HubbleProduct(
        product_filename=str(product["productFilename"]),
        data_uri=str(product["dataURI"]),
        size_bytes=_row_int(product, "size"),
        observation_id=str(observation["obs_id"]),
        proposal_id=str(observation["proposal_id"]),
        instrument=_row_str(observation, "instrument_name"),
        ra_deg=_row_float(observation, "s_ra"),
        dec_deg=_row_float(observation, "s_dec"),
    )


def _download_url(data_uri: str) -> str:
    return f"{MAST_DOWNLOAD_URL}?uri={quote(data_uri, safe=':/')}"


class HubbleImporter:
    def __init__(
        self,
        mast: _MastObservations | None = None,
        *,
        search_radius_deg: float = SEARCH_RADIUS_DEG,
        http_client_factory: Callable[[], httpx.AsyncClient] | None = None,
    ) -> None:
        self._mast = mast or Observations
        self._search_radius_deg = search_radius_deg
        self._http_client_factory = http_client_factory or (
            lambda: httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT_SECONDS)
        )

    async def fetch_image(self, target_name: str) -> ImportedImage:
        with _tracer.start_as_current_span("mast_search") as span:
            span.set_attribute("target_name", target_name)
            products, ra_deg, dec_deg = await asyncio.to_thread(self._search_products, target_name)
            span.set_attribute("product_count", len(products))

        product = _best_science_product(products)
        if product is None:
            _log.warning(
                "no_heavy_product_found",
                target_name=target_name,
                product_count=len(products),
            )
            raise HubbleNotFoundError(
                f"No Hubble science FITS of at least {MIN_PRODUCT_SIZE_BYTES} bytes "
                f"found for {target_name!r}"
            )
        _log.info(
            "product_selected",
            target_name=target_name,
            product_filename=product.product_filename,
            observation_id=product.observation_id,
            size_bytes=product.size_bytes,
        )

        with _tracer.start_as_current_span("mast_download") as span:
            span.set_attribute("data_uri", product.data_uri)
            download_url = _download_url(product.data_uri)
            download_start = time.perf_counter()
            payload = await self._download(download_url)
            download_ms = round((time.perf_counter() - download_start) * 1000, 2)
            span.set_attribute("payload_bytes", len(payload))
            _log.info(
                "download_complete",
                target_name=target_name,
                payload_bytes=len(payload),
                download_ms=download_ms,
            )

        with _tracer.start_as_current_span("annotate_header") as span:
            annotate_start = time.perf_counter()
            annotated = self._annotate_header(payload, target_name, product)
            annotate_ms = round((time.perf_counter() - annotate_start) * 1000, 2)
            span.set_attribute("annotated_bytes", len(annotated))
            _log.info(
                "annotate_complete",
                target_name=target_name,
                annotated_bytes=len(annotated),
                annotate_ms=annotate_ms,
            )

        return ImportedImage(
            payload=annotated,
            filename=product.product_filename,
            target_name=target_name,
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            observation_id=product.observation_id,
            proposal_id=product.proposal_id,
            instrument=product.instrument,
        )

    def _search_products(self, target_name: str) -> tuple[list[HubbleProduct], float, float]:
        coordinates = self._resolve(target_name)
        products: list[HubbleProduct] = []
        for page in range(1, MAST_SEARCH_MAX_PAGES + 1):
            observations = self._mast.query_criteria(
                coordinates=coordinates,
                radius=Angle(self._search_radius_deg * u.deg),
                obs_collection=MAST_COLLECTION,
                pagesize=MAST_SEARCH_PAGESIZE,
                page=page,
            )
            if observations is None or len(observations) == 0:
                break
            hst_rows = observations[:MAST_SEARCH_PAGESIZE]
            obs_id = str(hst_rows[0]["obs_id"]) if len(hst_rows) > 0 else None
            _log.debug("mast_page", target_name=target_name, page=page, obs_id=obs_id)

            product_rows = self._mast.get_product_list(hst_rows)
            for product in product_rows:
                hubble_product = _product_from_row(product, hst_rows)
                if hubble_product is not None:
                    products.append(hubble_product)
            if any(
                product.size_bytes is not None and product.size_bytes >= MIN_PRODUCT_SIZE_BYTES
                for product in products
            ):
                break

        ra_deg = float(coordinates.ra.deg)
        dec_deg = float(coordinates.dec.deg)
        return products, ra_deg, dec_deg

    def _resolve(self, target_name: str) -> SkyCoord:
        try:
            return SkyCoord.from_name(target_name)
        except Exception as exc:
            raise HubbleNotFoundError(f"Could not resolve celestial body {target_name!r}") from exc

    async def _download(self, data_url: str) -> bytes:
        async with self._http_client_factory() as http_client:
            try:
                response = await http_client.get(data_url)
                response.raise_for_status()
                return response.content
            except (httpx.HTTPError, OSError) as exc:
                raise HubbleDownloadError(
                    f"Failed to download Hubble FITS from {data_url}"
                ) from exc

    def _annotate_header(self, payload: bytes, target_name: str, product: HubbleProduct) -> bytes:
        with fits.open(io.BytesIO(payload)) as hdul:
            header = hdul[0].header
            header["AI_SRC"] = ("hubble-mast", "AstroImage fetch backend")
            header["AI_TARG"] = (target_name, "Requested celestial body")
            header["AI_OBS"] = (product.observation_id, "MAST observation id")
            header["AI_MAST"] = (product.data_uri, "MAST product URI")
            output = io.BytesIO()
            hdul.writeto(output, overwrite=True)
            return output.getvalue()
