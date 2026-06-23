from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from app.models.herramienta import EstadoHerramienta, EstadoPrestamo


# ============ Herramienta Schemas ============

class HerramientaBase(BaseModel):
    """Schema base de herramienta."""
    nombre: str = Field(..., min_length=2, max_length=200)
    descripcion: Optional[str] = None


class HerramientaCreate(HerramientaBase):
    """Schema para crear herramienta."""
    estado: EstadoHerramienta = EstadoHerramienta.buen_estado


class HerramientaUpdate(BaseModel):
    """Schema para actualizar herramienta."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    descripcion: Optional[str] = None
    estado: Optional[EstadoHerramienta] = None


class HerramientaResponse(HerramientaBase):
    """Schema de respuesta de herramienta."""
    id: UUID
    estado: EstadoHerramienta
    estado_prestamo: EstadoPrestamo
    activo: bool
    created_at: datetime
    foto_url: Optional[str] = None
    foto_public_id: Optional[str] = None

    class Config:
        from_attributes = True


class HerramientaConPrestamoResponse(HerramientaResponse):
    """Schema de herramienta con info del préstamo activo."""
    retirado_por: Optional[str] = None
    fecha_retiro: Optional[date] = None


# ============ Préstamo Schemas ============

class PrestamoCreate(BaseModel):
    """Schema para registrar un préstamo."""
    herramienta_id: UUID
    retirado_por: str = Field(..., min_length=2, max_length=200)
    fecha_retiro: date


class PrestamoDevolucion(BaseModel):
    """Schema para registrar devolución."""
    fecha_devolucion: date
    notas_devolucion: Optional[str] = None


class PrestamoUpdate(BaseModel):
    """Schema para actualizar un préstamo."""
    retirado_por: Optional[str] = Field(None, min_length=2, max_length=200)
    fecha_retiro: Optional[date] = None
    fecha_devolucion: Optional[date] = None
    notas_devolucion: Optional[str] = None


class PrestamoResponse(BaseModel):
    """Schema de respuesta de préstamo."""
    id: UUID
    herramienta_id: UUID
    retirado_por: str
    fecha_retiro: date
    fecha_devolucion: Optional[date] = None
    notas_devolucion: Optional[str] = None
    registrado_por_id: Optional[UUID] = None
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PrestamoConHerramientaResponse(PrestamoResponse):
    """Schema de préstamo con info de herramienta."""
    herramienta_nombre: Optional[str] = None
