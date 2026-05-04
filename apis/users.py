from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from apis.deps import require_roles
from configs.constants import RoleName
from models.user import User
from schemas.user import UserCreate, UserRead
from services import auth_service
from utils.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    body: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_roles(RoleName.SYSTEM_ADMIN))],
) -> UserRead:
    return auth_service.create_user(db, body)
