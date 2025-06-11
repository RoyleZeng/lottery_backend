from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    name: str
    phone_number: Optional[str] = None
    email: EmailStr
    password: str
    address: Optional[str] = None
    birthday: Optional[date] = None

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str = "consumer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    user_id: str
    email: str
    name: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    user: UserInfo


class MeResponse(UserInfo):
    phone_number: Optional[str] = None
    address: Optional[str] = None
    birthday: Optional[date] = None
