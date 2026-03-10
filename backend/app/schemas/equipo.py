from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from app.models.equipo import TipoEquipo, EstadoEquipo


class EquipoBase(BaseModel):
    """Schema base de equipo."""
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., min_length=2, max_length=200)
    descripcion: Optional[str] = None
    tipo: TipoEquipo
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)


class EquipoCreate(EquipoBase):
    """Schema para crear equipo."""
    estado: EstadoEquipo = EstadoEquipo.disponible
    fecha_adquisicion: Optional[date] = None
    costo_adquisicion: Optional[float] = None


class EquipoUpdate(BaseModel):
    """Schema para actualizar equipo."""
    codigo: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    descripcion: Optional[str] = None
    tipo: Optional[TipoEquipo] = None
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    estado: Optional[EstadoEquipo] = None
    fecha_adquisicion: Optional[date] = None
    costo_adquisicion: Optional[float] = None


class EquipoResponse(EquipoBase):
    """Schema de respuesta de equipo."""
    id: UUID
    estado: EstadoEquipo
    fecha_adquisicion: Optional[date] = None
    costo_adquisicion: Optional[float] = None
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AsignacionEquipoCreate(BaseModel):
    """Schema para asignar equipo a proyecto."""
    equipo_id: Optional[UUID] = None  # Se puede pasar por path
    proyecto_id: UUID
    fecha_asignacion: date
    fecha_devolucion_est: Optional[date] = None
    notas: Optional[str] = None


class AsignacionEquipoResponse(BaseModel):
    """Schema de respuesta de asignación de equipo."""
    id: UUID
    equipo_id: UUID
    proyecto_id: UUID
    fecha_asignacion: date
    fecha_devolucion_est: Optional[date] = None
    fecha_devolucion_real: Optional[date] = None
    notas: Optional[str] = None
    equipo_nombre: Optional[str] = None
    proyecto_nombre: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
