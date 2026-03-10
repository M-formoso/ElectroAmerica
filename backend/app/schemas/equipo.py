from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from app.models.equipo import TipoEquipo, EstadoEquipo


class EquipoBase(BaseModel):
    """Schema base de equipo."""
    nombre: str = Field(..., min_length=2, max_length=255)
    tipo: TipoEquipo
    patente: Optional[str] = Field(None, max_length=20)
    codigo_interno: Optional[str] = Field(None, max_length=50)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    anio: Optional[str] = Field(None, max_length=4)
    observaciones: Optional[str] = None


class EquipoCreate(EquipoBase):
    """Schema para crear equipo."""
    estado: EstadoEquipo = EstadoEquipo.disponible


class EquipoUpdate(BaseModel):
    """Schema para actualizar equipo."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=255)
    tipo: Optional[TipoEquipo] = None
    patente: Optional[str] = Field(None, max_length=20)
    codigo_interno: Optional[str] = Field(None, max_length=50)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    anio: Optional[str] = Field(None, max_length=4)
    estado: Optional[EstadoEquipo] = None
    observaciones: Optional[str] = None


class EquipoResponse(EquipoBase):
    """Schema de respuesta de equipo."""
    id: UUID
    estado: EstadoEquipo
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AsignacionEquipoCreate(BaseModel):
    """Schema para asignar equipo a proyecto."""
    equipo_id: Optional[UUID] = None  # Se puede pasar por path
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    fecha_desde: date
    fecha_hasta: Optional[date] = None
    observaciones: Optional[str] = None


class AsignacionEquipoResponse(BaseModel):
    """Schema de respuesta de asignación de equipo."""
    id: UUID
    equipo_id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    fecha_desde: date
    fecha_hasta: Optional[date] = None
    observaciones: Optional[str] = None
    equipo_nombre: Optional[str] = None
    proyecto_nombre: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
