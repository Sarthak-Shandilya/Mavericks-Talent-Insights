import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.user import User


def get_by_email_with_role(db: Session, email: str) -> User | None:
    stmt = select(User).options(joinedload(User.role)).where(User.email == email)
    return db.execute(stmt).unique().scalar_one_or_none()


def get_by_id_with_role(db: Session, user_id: uuid.UUID) -> User | None:
    stmt = select(User).options(joinedload(User.role)).where(User.id == user_id)
    return db.execute(stmt).unique().scalar_one_or_none()


def count_all(db: Session) -> int:
    from sqlalchemy import func

    return db.execute(select(func.count()).select_from(User)).scalar_one()


def create(
    db: Session,
    *,
    email: str,
    password_hash: str,
    full_name: str | None,
    role_id: uuid.UUID,
) -> User:
    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role_id=role_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
