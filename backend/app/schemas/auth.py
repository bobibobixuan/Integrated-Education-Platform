from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4)
    nickname: str = Field(..., min_length=1, max_length=50)


class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
    is_active: bool
    force_password_change: bool = False
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=4)


class ProfileUpdateRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50)
