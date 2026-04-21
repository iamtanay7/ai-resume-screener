"""User models for authentication and authorization."""

from typing import Literal

from pydantic import BaseModel, EmailStr


class UserSignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["recruiter", "candidate"]


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: Literal["recruiter", "candidate"]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
