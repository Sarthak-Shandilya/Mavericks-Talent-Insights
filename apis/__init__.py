"""HTTP routers — map URLs to service calls; keep thin."""

from apis.auth import router as auth_router
from apis.health import router as health_router
from apis.users import router as users_router

__all__ = ["auth_router", "health_router", "users_router"]
