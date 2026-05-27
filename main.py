from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apis.admin import router as admin_router
from apis.auth import router as auth_router
from apis.business_head import router as business_head_router
from apis.health import router as health_router
from apis.hr import router as hr_router
from apis.reports import router as reports_router
from apis.trainer import router as trainer_router
from apis.training_coordinator import router as training_coordinator_router
from apis.uploads import router as uploads_router
from apis.users import router as users_router
from configs.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    from sqlalchemy.engine.url import make_url

    from configs.settings import get_settings
    from services.bootstrap import maybe_bootstrap_admin
    from utils.database import engine
    from utils.sqlite_schema import prepare_sqlite_for_dev

    settings = get_settings()
    logger = logging.getLogger("mavericks-api")
    try:
        safe_db = make_url(settings.database_url).render_as_string(hide_password=True)
    except Exception:
        safe_db = "<invalid DATABASE_URL>"
    logger.info(
        "api boot db=%s queue_type=%s queue=%s storage=%s",
        safe_db,
        settings.queue_type,
        settings.queue_name_ingestion,
        settings.storage_type,
    )

    prepare_sqlite_for_dev(engine)
    maybe_bootstrap_admin()
    yield
    from utils.database import engine

    engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix=settings.api_v1_prefix, tags=["health"])
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(users_router, prefix=settings.api_v1_prefix)
    app.include_router(uploads_router, prefix=settings.api_v1_prefix)
    app.include_router(training_coordinator_router, prefix=settings.api_v1_prefix)
    app.include_router(admin_router, prefix=settings.api_v1_prefix)
    app.include_router(reports_router, prefix=settings.api_v1_prefix)
    app.include_router(trainer_router, prefix=settings.api_v1_prefix)
    app.include_router(hr_router, prefix=settings.api_v1_prefix)
    app.include_router(business_head_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
