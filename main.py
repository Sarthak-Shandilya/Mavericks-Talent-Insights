from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apis.auth import router as auth_router
from apis.health import router as health_router
from apis.users import router as users_router
from configs.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.bootstrap import maybe_bootstrap_admin

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
    return app


app = create_app()
