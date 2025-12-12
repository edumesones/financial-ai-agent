# backend/app/api/v1/auth.py
"""Authentication endpoints."""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_user,
    TokenPayload,
)
from app.models.usuario import Usuario
from app.models.tenant import Tenant
from app.schemas.auth import Token, LoginRequest
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Obtener token de acceso."""
    stmt = select(Usuario).where(Usuario.email == form_data.username, Usuario.activo == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    expires_at = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        rol=user.rol,
    )
    
    return Token(access_token=access_token, expires_at=expires_at)


@router.get("/me")
async def get_me(current_user: TokenPayload = Depends(get_current_user)):
    """Obtener información del usuario actual."""
    return {
        "user_id": current_user.sub,
        "tenant_id": current_user.tenant_id,
        "email": current_user.email,
        "rol": current_user.rol,
    }


@router.post("/register", response_model=Token)
async def register_tenant(
    tenant_name: str,
    email: str,
    password: str,
    nombre: str,
    db: AsyncSession = Depends(get_db),
):
    """Registrar nuevo tenant y usuario admin."""
    # Verificar que email no existe
    stmt = select(Usuario).where(Usuario.email == email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    # Crear tenant
    tenant = Tenant(nombre=tenant_name)
    db.add(tenant)
    await db.flush()
    
    # Crear usuario admin
    user = Usuario(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password(password),
        nombre=nombre,
        rol="admin",
    )
    db.add(user)
    await db.commit()
    
    # Generar token
    expires_at = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=tenant.id,
        email=user.email,
        rol=user.rol,
    )
    
    return Token(access_token=access_token, expires_at=expires_at)
