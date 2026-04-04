from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class UserRoleEnum(StrEnum):
    ADMIN = "admin"
    VIEWER = "viewer"


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=3, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRoleEnum
    is_system_account: bool
    created_at: datetime
    updated_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    expires_at: datetime
    user: UserResponse


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=3, max_length=128)
    role: UserRoleEnum


class UpdateAccountRequest(BaseModel):
    current_password: str = Field(min_length=3, max_length=128)
    username: str | None = Field(default=None, min_length=3, max_length=64)
    new_password: str | None = Field(default=None, min_length=3, max_length=128)

    @model_validator(mode="after")
    def validate_change(self) -> "UpdateAccountRequest":
        if not (self.username or self.new_password):
            raise ValueError("Provide a new username or a new password")
        return self
