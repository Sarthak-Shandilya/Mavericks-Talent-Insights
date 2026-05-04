from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apis.deps import get_current_active_user
from models.user import User
from schemas.auth import LoginRequest, TokenResponse
from schemas.user import UserRead
from services import auth_service
from utils.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    return auth_service.login(db, str(body.email), body.password)


@router.get("/me", response_model=UserRead)
def me(current: Annotated[User, Depends(get_current_active_user)]) -> UserRead:
    return auth_service.user_to_read(current)
