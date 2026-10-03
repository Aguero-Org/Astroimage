from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import ProgrammingError

from astroimage.config import Settings, get_settings
from astroimage.fits.controller import router as fits_router
from astroimage.health.controller import router as health_router
from astroimage.hub.controller import router as hub_router
from astroimage.hub.repository import TransferRepository
from astroimage.render.controller import router as render_router
from astroimage.shared.background import BackgroundTasks
from astroimage.shared.database import create_engine_from_settings, create_session_factory
from astroimage.shared.errors import register_exception_handlers
from astroimage.shared.logging import setup_logging
from astroimage.shared.metrics import setup_metrics
from astroimage.shared.middleware import RequestContextMiddleware
from astroimage.shared.minio_storage import create_object_storage_client, ensure_bucket
from astroimage.shared.telemetry import setup_tracing
from astroimage.sources.controller import router as sources_router

_log = structlog.get_logger("astroimage.main")


def build_api_router() -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(health_router)
    api_router.include_router(fits_router)
    api_router.include_router(hub_router)
    api_router.include_router(sources_router)
    api_router.include_router(render_router)
    return api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    engine = create_engine_from_settings(settings)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.background_tasks = BackgroundTasks()
    minio_client = create_object_storage_client(settings)
    ensure_bucket(minio_client, settings.minio_bucket)
    app.state.minio_client = minio_client
    async with app.state.session_factory() as session:
        try:
            await TransferRepository(session).mark_running_as_interrupted()
            await session.commit()
        except ProgrammingError:
            await session.rollback()
            _log.warning("transfer_recovery_skipped", reason="image_transfers is not migrated")
    yield
    app.state.background_tasks.clear()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    application.state.settings = settings
    register_exception_handlers(application)
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
