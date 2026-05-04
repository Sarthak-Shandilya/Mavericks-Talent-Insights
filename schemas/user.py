import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": False}


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=512)
    full_name: str | None = None
    role: str = Field(
        ...,
        description="Role name: training_coordinator, trainer, hr, business_head, system_admin",
    )
