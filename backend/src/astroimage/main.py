from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from astroimage.config import Settings, get_settings
from astroimage.fits.controller import router as fits_router
from astroimage.health.controller import router as health_router
from astroimage.render.controller import router as render_router
from astroimage.shared.database import create_engine_from_settings, create_session_factory
from astroimage.shared.logging import setup_logging
from astroimage.shared.metrics import setup_metrics
from astroimage.shared.middleware import RequestContextMiddleware
from astroimage.shared.telemetry import setup_tracing
from astroimage.sources.controller import router as sources_router


def build_api_router() -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(health_router)
    api_router.include_router(fits_router)
    api_router.include_router(sources_router)
    api_router.include_router(render_router)
    return api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    engine = create_engine_from_settings(settings)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(build_api_router())
    setup_metrics(application)
    setup_tracing(
        application,
        service_name=settings.app_name,
        otlp_endpoint=settings.otlp_endpoint,
    )
    return application


app = create_app()
