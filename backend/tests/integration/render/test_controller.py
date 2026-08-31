from __future__ import annotations

from io import BytesIO
from uuid import uuid4

import numpy as np
import pytest
from astropy.io import fits
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from astroimage.fits.service import FitsService

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _gradient_fits_bytes() -> bytes:
    image = np.linspace(0.0, 100.0, 256).reshape(16, 16)
    buffer = BytesIO()
    fits.PrimaryHDU(image).writeto(buffer)
    return buffer.getvalue()


async def _store_gradient(
    fits_service: FitsService,
    db_session: AsyncSession,
) -> str:
    record = await fits_service.store_bytes(_gradient_fits_bytes(), source_name="gradient.fits")
    await db_session.commit()
    return str(record.id)


class TestRenderFitsImage:
    @pytest.mark.asyncio
    async def test_returns_png(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(f"/image/{record_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content.startswith(_PNG_SIGNATURE)

    @pytest.mark.asyncio
    async def test_accepts_config_params(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(
            f"/image/{record_id}",
            params={"stretch": "asinh", "pmin": "5.0", "pmax": "95.0", "gamma": "1.4"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    @pytest.mark.asyncio
    async def test_accepts_linear_stretch_and_zscale_limits(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(
            f"/image/{record_id}",
            params={"stretch": "linear", "limits": "zscale"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    @pytest.mark.parametrize("colormap", ["inverse", "heat", "rainbow", "cube_helix"])
    @pytest.mark.asyncio
    async def test_accepts_colormaps(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
        colormap: str,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(f"/image/{record_id}", params={"colormap": colormap})

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    @pytest.mark.asyncio
    async def test_rejects_unknown_stretch(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(f"/image/{record_id}", params={"stretch": "exp"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_unknown_limits(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(f"/image/{record_id}", params={"limits": "minmax"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_unknown_colormap(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(f"/image/{record_id}", params={"colormap": "magma"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_record_returns_not_found(self, client: AsyncClient) -> None:
        response = await client.get(f"/image/{uuid4()}")

        assert response.status_code == 404


class TestRenderFitsHistogram:
    @pytest.mark.asyncio
    async def test_returns_bin_stats(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(f"/image/{record_id}/histogram", params={"bins": "32"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        payload = response.json()
        assert len(payload["bin_centers"]) == 32
        assert len(payload["counts"]) == 32
        assert sum(payload["counts"]) == 16 * 16
        assert payload["minimum"] <= payload["maximum"]

    @pytest.mark.asyncio
    async def test_uses_default_bins(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(f"/image/{record_id}/histogram")

        assert response.status_code == 200
        assert len(response.json()["counts"]) == 256

    @pytest.mark.asyncio
    async def test_rejects_invalid_bins(
        self,
        client: AsyncClient,
        fits_service: FitsService,
        db_session: AsyncSession,
    ) -> None:
        record_id = await _store_gradient(fits_service, db_session)

        response = await client.get(f"/image/{record_id}/histogram", params={"bins": "4097"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_record_returns_not_found(self, client: AsyncClient) -> None:
        response = await client.get(f"/image/{uuid4()}/histogram")

        assert response.status_code == 404
