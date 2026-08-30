from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile

from astroimage.render.schema import RenderConfigSchema
from astroimage.render.service import RenderService

router = APIRouter(prefix="/render", tags=["render"])
_service = RenderService()
_DEFAULTS = RenderConfigSchema()

SourceFile = Annotated[UploadFile, File(description="FITS file to render")]
HduIndex = Annotated[
    int | None,
    Query(ge=0, description="Optional image HDU index; defaults to the first 2D image HDU"),
]

StretchParam = Annotated[str, Form(pattern="^(sqrt|log|asinh)$")]
PminParam = Annotated[float, Form(ge=0.0, lt=100.0)]
PmaxParam = Annotated[float, Form(gt=0.0, le=100.0)]
GammaParam = Annotated[float, Form(ge=0.1, le=5.0)]


def _config(stretch: str, pmin: float, pmax: float, gamma: float) -> RenderConfigSchema:
    return RenderConfigSchema(stretch=stretch, pmin=pmin, pmax=pmax, gamma=gamma)


@router.post(
    "/image",
    responses={200: {"content": {"image/png": {}}}},
    operation_id="renderFitsImage",
)
async def render_fits_image(
    file: SourceFile,
    hdu: HduIndex = None,
    stretch: StretchParam = _DEFAULTS.stretch,
    pmin: PminParam = _DEFAULTS.pmin,
    pmax: PmaxParam = _DEFAULTS.pmax,
    gamma: GammaParam = _DEFAULTS.gamma,
) -> Response:
    payload = await file.read()
    try:
        png = _service.render_png_from_bytes(
            payload,
            config=_config(stretch, pmin, pmax, gamma),
            hdu_index=hdu,
        )
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(content=png, media_type="image/png")
