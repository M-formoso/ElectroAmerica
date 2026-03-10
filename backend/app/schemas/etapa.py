from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from app.models.etapa import EstadoEtapa


class EtapaBase(BaseModel):
    """Schema base de etapa."""
    nombre: str = Field(..., min_length=2, max_length=255)
    descripcion: Optional[str] = None
    orden: int = Field(default=0, ge=0)
    fecha_inicio_est: Optional[date] = None
    fecha_fin_est: Optional[date] = None
    estado: EstadoEtapa = EstadoEtapa.pendiente


class EtapaCreate(EtapaBase):
    """Schema para crear etapa."""
    proyecto_id: UUID


class EtapaUpdate(BaseModel):
    """Schema para actualizar etapa."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=255)
    descripcion: Optional[str] = None
    orden: Optional[int] = Field(None, ge=0)
    fecha_inicio_est: Optional[date] = None
    fecha_fin_est: Optional[date] = None
    fecha_inicio_real: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    estado: Optional[EstadoEtapa] = None
    porcentaje_avance: Optional[Decimal] = Field(None, ge=0, le=100)


class EtapaResponse(EtapaBase):
    """Schema de respuesta de etapa."""
    id: UUID
    proyecto_id: UUID
    fecha_inicio_real: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    porcentaje_avance: Decimal
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EtapaClienteResponse(BaseModel):
    """Schema de respuesta de etapa para cliente."""
    id: UUID
    nombre: str
    descripcion: Optional[str] = None
    orden: int
    fecha_inicio_est: Optional[date] = None
    fecha_fin_est: Optional[date] = None
    fecha_inicio_real: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    estado: EstadoEtapa
    porcentaje_avance: Decimal

    class Config:
        from_attributes = True
