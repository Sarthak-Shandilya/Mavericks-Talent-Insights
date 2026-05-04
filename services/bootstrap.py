"""Optional first admin creation when DB is empty (env-guarded)."""

from configs.constants import RoleName
from configs.settings import get_settings
import repositories.role_repository as role_repository
import repositories.user_repository as user_repository
from utils.database import SessionLocal
from utils.security import hash_password

from services.auth_service import normalize_email


def maybe_bootstrap_admin() -> None:
    settings = get_settings()
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return

    db = SessionLocal()
    try:
        if user_repository.count_all(db) > 0:
            return
        role = role_repository.get_by_name(db, RoleName.SYSTEM_ADMIN.value)
        if not role:
            return
        email = normalize_email(settings.bootstrap_admin_email)
        user_repository.create(
            db,
            email=email,
            password_hash=hash_password(settings.bootstrap_admin_password),
            full_name=settings.bootstrap_admin_full_name,
            role_id=role.id,
        )
    finally:
        db.close()
