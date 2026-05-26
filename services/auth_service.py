"""Login and admin user provisioning."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from configs.settings import get_settings
from models.user import User
import repositories.role_repository as role_repository
import repositories.user_repository as user_repository
from schemas.auth import TokenResponse
from schemas.user import UserCreate, UserRead
from utils.security import create_access_token, hash_password, verify_password


def normalize_email(email: str) -> str:
    return email.strip().lower()


def user_to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role_name=user.role.name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def login(db: Session, email: str, password: str) -> TokenResponse:
    normalized = normalize_email(email)
    user = user_repository.get_by_email_with_role(db, normalized)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    settings = get_settings()
    token = create_access_token(
        subject=str(user.id),
        role_name=user.role.name,
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


def create_user(db: Session, body: UserCreate) -> UserRead:
    role = role_repository.get_by_name(db, body.role)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role: {body.role}",
        )
    normalized = normalize_email(str(body.email))
    pwd_hash = hash_password(body.password)
    try:
        user_repository.create(
            db,
            email=normalized,
            password_hash=pwd_hash,
            full_name=body.full_name,
            role_id=role.id,
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc
    created = user_repository.get_by_email_with_role(db, normalized)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed",
        )
    from services import audit_service

    audit_service.log_action(
        db,
        actor=None,
        action="user.create",
        entity_type="user",
        entity_id=created.id,
        details={"email": created.email, "role": body.role},
    )
    db.commit()
    return user_to_read(created)

