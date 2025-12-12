# backend/app/schemas/auth.py
"""Schemas de autenticación."""

from datetime import datetime
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Request de login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Response de token."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TokenPayload(BaseModel):
    """Payload del JWT."""
    sub: str
    tenant_id: str
    email: str
    rol: str
    exp: datetime
