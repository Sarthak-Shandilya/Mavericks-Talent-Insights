from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import Role


def get_by_name(db: Session, name: str) -> Role | None:
    return db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
