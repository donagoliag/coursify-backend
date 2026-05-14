from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import UserRole
from typing import Optional

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.student

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: UserRole
    bio: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ChangePassword(BaseModel):
    current_password: str
    new_password: str