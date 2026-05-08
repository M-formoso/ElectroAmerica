from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.usuario import RolUsuario, MODULOS_SISTEMA


class UsuarioBase(BaseModel):
    """Schema base de usuario."""
    email: EmailStr
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    rol: RolUsuario = RolUsuario.operario


class UsuarioCreate(UsuarioBase):
    """Schema para crear usuario."""
    password: str = Field(..., min_length=6)
    modulos_permitidos: Optional[List[str]] = None
    es_superadmin: bool = False


class UsuarioUpdate(BaseModel):
    """Schema para actualizar usuario."""
    email: Optional[EmailStr] = None
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)
    modulos_permitidos: Optional[List[str]] = None
    es_superadmin: Optional[bool] = None


class UsuarioResponse(UsuarioBase):
    """Schema de respuesta de usuario."""
    id: UUID
    activo: bool
    ultimo_acceso: Optional[datetime] = None
    created_at: datetime
    modulos_permitidos: Optional[List[str]] = None
    es_superadmin: bool = False

    class Config:
        from_attributes = True


class ModulosDisponibles(BaseModel):
    """Lista de módulos disponibles en el sistema."""
    modulos: List[str] = Field(default_factory=lambda: MODULOS_SISTEMA.copy())


class Token(BaseModel):
    """Schema de token JWT."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema de request para refrescar el token."""
    refresh_token: str


class TokenPayload(BaseModel):
    """Schema del payload del token."""
    sub: str
    rol: RolUsuario
    exp: datetime


class LoginRequest(BaseModel):
    """Schema de request de login."""
    email: EmailStr
    password: str
