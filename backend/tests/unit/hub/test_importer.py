from __future__ import annotations

from io import BytesIO
from typing import Any

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table, vstack
from httpx import AsyncClient, MockTransport, Response

from astroimage.hub.importer import (
    HubbleDownloadError,
    HubbleImporter,
    HubbleNotFoundError,
)


def _sample_fits_bytes() -> bytes:
    data = np.ones((2, 3), dtype=float)
    header = fits.Header()
    header["TELESCOP"] = "HST"
    header["INSTRUME"] = "WFC3"
    buffer = BytesIO()
    fits.PrimaryHDU(data=data, header=header).writeto(buffer)
    return buffer.getvalue()


class _FakeMast:
    def __init__(self, observations: Table, products: Table) -> None:
        self._observations = observations
        self._products = products
        self.criteria: list[dict[str, Any]] = []

    def query_criteria(
        self,
        *,
        coordinates: Any,
        radius: Any,
        obs_collection: str,
        pagesize: int,
        page: int,
    ) -> Table:
        self.criteria.append(
            {
                "coordinates": coordinates,
                "radius": radius,
                "obs_collection": obs_collection,
                "pagesize": pagesize,
                "page": page,
            }
        )
        return self._observations

    def get_product_list(self, rows: Any) -> Table:
        return self._products


class _PagedMast:
    def __init__(self, products_by_obs: dict[str, Table]) -> None:
        self._products_by_obs = products_by_obs
        self.criteria: list[dict[str, Any]] = []

    def query_criteria(
        self,
        *,
        coordinates: Any,
        radius: Any,
        obs_collection: str,
        pagesize: int,
        page: int,
    ) -> Table:
        self.criteria.append(
            {
                "coordinates": coordinates,
                "radius": radius,
                "obs_collection": obs_collection,
                "pagesize": pagesize,
                "page": page,
            }
        )
        if page > len(self._products_by_obs):
            return Table()
        row = {
            "obs_collection": ["HST"],
            "obs_id": [f"obs-{page}"],
            "proposal_id": ["10000"],
            "instrument_name": ["WFC3/UVIS"],
            "s_ra": [10.684],
            "s_dec": [41.269],
        }
        if page == 2:
            row["instrument_name"] = ["ACS/WFC"]
        return Table(row)

    def get_product_list(self, rows: Any) -> Table:
        tables = [self._products_by_obs[str(row["obs_id"])] for row in rows]
        return vstack(tables)


def _observations_table() -> Table:
    return Table(
        {
            "obs_collection": ["HST", "HST", "SLOAN"],
            "obs_id": ["obs-1", "obs-2", "obs-3"],
            "proposal_id": ["10000", "10000", "9000"],
            "instrument_name": ["WFC3/UVIS", "ACS/WFC", "SDSS"],
            "s_ra": [10.684, 10.684, 11.0],
            "s_dec": [41.269, 41.269, 40.0],
        }
    )


def _science_products_table() -> Table:
    return Table(
        {
            "productFilename": ["hst_drz.fits", "hst_flt.fits", "hst_cal.fits", "extra.fits"],
            "productType": ["SCIENCE", "SCIENCE", "CALIBRATION", "SCIENCE"],
            "contentType": ["image/fits", "image/fits", "image/fits", "image/fits"],
            "dataURI": [
                "mast:HST/product/hst_drz.fits",
                "mast:HST/product/hst_flt.fits",
                "mast:HST/product/hst_cal.fits",
                "mast:HST/product/extra.fits",
            ],
            "productSubGroupDescription": ["DRZ", "FLT", "CAL", "DRZ"],
            "size": [150 * 1024 * 1024, 300, None, 100],
            "obs_id": ["obs-1", "obs-1", "obs-1", "obs-2"],
        }
    )


def _sample_fits_handler(request: Any) -> Response:
    return Response(200, content=_sample_fits_bytes())


def _importer(observations: Table, products: Table, *, status_code: int = 200) -> HubbleImporter:
    payload = _sample_fits_bytes() if status_code == 200 else b""
    transport = MockTransport(lambda request: Response(status_code, content=payload))
    return HubbleImporter(
        mast=_FakeMast(observations, products),
        http_client_factory=lambda: AsyncClient(transport=transport),
    )


def _fake_mast(importer: HubbleImporter) -> _FakeMast:
    return importer._mast  # type: ignore[return-value]


@pytest.fixture
def resolved_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        SkyCoord,
        "from_name",
        lambda name: SkyCoord(10.684, 41.269, unit="deg"),
    )


@pytest.mark.asyncio
async def test_fetch_image_selects_drizzled_science_product(resolved_target: None) -> None:
    importer = _importer(_observations_table(), _science_products_table())

    image = await importer.fetch_image("M31")

    assert image.filename == "hst_drz.fits"
    assert image.observation_id == "obs-1"
    assert image.proposal_id == "10000"
    assert image.instrument == "WFC3/UVIS"
    assert image.ra_deg == pytest.approx(10.684)
    assert image.dec_deg == pytest.approx(41.269)
    with fits.open(BytesIO(image.payload)) as hdul:
        assert hdul[0].header["AI_TARG"] == "M31"
        assert hdul[0].header["AI_SRC"] == "hubble-mast"
        assert hdul[0].header["AI_MAST"] == "mast:HST/product/hst_drz.fits"


@pytest.mark.asyncio
async def test_fetch_image_downloads_via_mast_file_endpoint(resolved_target: None) -> None:
    requested_urls: list[str] = []

    def handler(request: Any) -> Response:
        requested_urls.append(str(request.url))
        return Response(200, content=_sample_fits_bytes())

    importer = HubbleImporter(
        mast=_FakeMast(_observations_table(), _science_products_table()),
        http_client_factory=lambda: AsyncClient(transport=MockTransport(handler)),
    )

    await importer.fetch_image("M31")

    assert requested_urls == [
        "https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:HST/product/hst_drz.fits"
    ]


@pytest.mark.asyncio
async def test_fetch_image_resolution_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        SkyCoord,
        "from_name",
        lambda name: (_ for _ in ()).throw(RuntimeError("Sesame unavailable")),
    )
    importer = _importer(_observations_table(), _science_products_table())

    with pytest.raises(HubbleNotFoundError):
        await importer.fetch_image("unknown-object")


@pytest.mark.asyncio
async def test_fetch_image_no_observations(resolved_target: None) -> None:
    empty_mast = _FakeMast(Table(), _science_products_table())
    importer = _importer(_observations_table(), _science_products_table())
    importer._mast = empty_mast

    with pytest.raises(HubbleNotFoundError):
        await importer.fetch_image("M31")


@pytest.mark.asyncio
async def test_fetch_image_no_hst_observations(resolved_target: None) -> None:
    observations = Table(
        {
            "obs_collection": ["SLOAN"],
            "obs_id": ["obs-3"],
            "proposal_id": ["9000"],
            "instrument_name": ["SDSS"],
            "s_ra": [11.0],
            "s_dec": [40.0],
        }
    )
    importer = _importer(observations, _science_products_table())

    with pytest.raises(HubbleNotFoundError):
        await importer.fetch_image("M31")


@pytest.mark.asyncio
async def test_fetch_image_filters_by_hst_server_side(resolved_target: None) -> None:
    importer = _importer(_observations_table(), _science_products_table())

    await importer.fetch_image("M31")

    criteria = _fake_mast(importer).criteria
    assert len(criteria) == 1
    assert criteria[0]["obs_collection"] == "HST"
    assert criteria[0]["radius"].deg == pytest.approx(0.05)
    assert criteria[0]["pagesize"] == 10
    assert criteria[0]["page"] == 1


@pytest.mark.asyncio
async def test_fetch_image_keeps_first_hst_observation_only(resolved_target: None) -> None:
    def get_product_list(rows: Any) -> Table:
        assert rows["obs_id"][0] == "obs-1"
        return _science_products_table()

    mast = _FakeMast(_observations_table(), _science_products_table())
    mast.get_product_list = get_product_list  # type: ignore[method-assign]
    importer = _importer(_observations_table(), _science_products_table())
    importer._mast = mast

    image = await importer.fetch_image("M31")

    assert image.filename == "hst_drz.fits"
    assert image.observation_id == "obs-1"


@pytest.mark.asyncio
async def test_fetch_image_prefers_science_product_above_min_size(
    resolved_target: None,
) -> None:
    products = Table(
        {
            "productFilename": ["hst_small.fits", "hst_large.fits", "hst_bigger.fits"],
            "productType": ["SCIENCE", "SCIENCE", "SCIENCE"],
            "contentType": ["image/fits", "image/fits", "image/fits"],
            "dataURI": [
                "mast:HST/product/hst_small.fits",
                "mast:HST/product/hst_large.fits",
                "mast:HST/product/hst_bigger.fits",
            ],
            "productSubGroupDescription": ["DRZ", "DRZ", "DRZ"],
            "size": [500, 100 * 1024 * 1024, 200 * 1024 * 1024],
            "obs_id": ["obs-1", "obs-1", "obs-1"],
        }
    )
    importer = _importer(_observations_table(), products)

    image = await importer.fetch_image("M31")

    assert image.filename == "hst_large.fits"


def _product_table(filename: str, obs_id: str, size: int) -> Table:
    return Table(
        {
            "productFilename": [filename],
            "productType": ["SCIENCE"],
            "contentType": ["image/fits"],
            "dataURI": [f"mast:HST/product/{filename}"],
            "productSubGroupDescription": ["DRZ"],
            "size": [size],
            "obs_id": [obs_id],
        }
    )


@pytest.mark.asyncio
async def test_fetch_image_paginates_until_heavy_product_found(
    resolved_target: None,
) -> None:
    mast = _PagedMast(
        {
            "obs-1": _product_table("hst_small.fits", "obs-1", 500),
            "obs-2": _product_table("hst_large.fits", "obs-2", 150 * 1024 * 1024),
        }
    )
    importer = HubbleImporter(
        mast=mast,
        http_client_factory=lambda: AsyncClient(transport=MockTransport(_sample_fits_handler)),
    )

    image = await importer.fetch_image("M31")

    assert image.filename == "hst_large.fits"
    assert image.observation_id == "obs-2"
    assert [criterion["page"] for criterion in mast.criteria] == [1, 2]


@pytest.mark.asyncio
async def test_fetch_image_rejects_when_no_product_reaches_min_size(
    resolved_target: None,
) -> None:
    mast = _PagedMast(
        {
            "obs-1": _product_table("hst_small.fits", "obs-1", 500),
            "obs-2": _product_table("hst_tiny.fits", "obs-2", 300),
            "obs-3": _product_table("hst_mini.fits", "obs-3", 100),
            "obs-4": _product_table("hst_short.fits", "obs-4", 200),
            "obs-5": _product_table("hst_sliver.fits", "obs-5", 400),
        }
    )
    importer = HubbleImporter(mast=mast)

    with pytest.raises(HubbleNotFoundError):
        await importer.fetch_image("M31")


@pytest.mark.asyncio
async def test_fetch_image_no_science_fits_products(resolved_target: None) -> None:
    products = Table(
        {
            "productFilename": ["hst_cal.fits"],
            "productType": ["CALIBRATION"],
            "contentType": ["image/fits"],
            "dataURI": ["mast:HST/product/hst_cal.fits"],
            "productSubGroupDescription": ["CAL"],
            "size": [None],
            "obs_id": ["obs-1"],
        }
    )
    importer = _importer(_observations_table(), products)

    with pytest.raises(HubbleNotFoundError):
        await importer.fetch_image("M31")


@pytest.mark.asyncio
async def test_fetch_image_download_failure(resolved_target: None) -> None:
    importer = _importer(_observations_table(), _science_products_table(), status_code=500)

    with pytest.raises(HubbleDownloadError):
        await importer.fetch_image("M31")
