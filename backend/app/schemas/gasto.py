from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class GastoBase(BaseModel):
    """Schema base de gasto."""
    fecha: date
    categoria: str = Field(..., max_length=100)
    descripcion: str = Field(..., min_length=2)
    monto: Decimal = Field(..., gt=0)


class GastoCreate(GastoBase):
    """Schema para crear gasto."""
    proyecto_id: Optional[UUID] = None
    responsable_id: UUID
    comprobante_url: Optional[str] = Field(None, max_length=500)


class GastoUpdate(BaseModel):
    """Schema para actualizar gasto."""
    fecha: Optional[date] = None
    categoria: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, min_length=2)
    monto: Optional[Decimal] = Field(None, gt=0)
    proyecto_id: Optional[UUID] = None
    comprobante_url: Optional[str] = Field(None, max_length=500)


class GastoResponse(GastoBase):
    """Schema de respuesta de gasto."""
    id: UUID
    proyecto_id: Optional[UUID] = None
    responsable_id: UUID
    comprobante_url: Optional[str] = None
    activo: bool
    created_at: datetime
    proyecto_nombre: Optional[str] = None
    responsable_nombre: Optional[str] = None

    class Config:
        from_attributes = True


class CategoriaGastoCreate(BaseModel):
    """Schema para crear categoría de gasto."""
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    color: str = Field(default="#E53935", max_length=7)


class CategoriaGastoResponse(BaseModel):
    """Schema de respuesta de categoría de gasto."""
    id: UUID
    nombre: str
    descripcion: Optional[str] = None
    color: str
    activo: bool

    class Config:
        from_attributes = True


class ResumenGastosPeriodo(BaseModel):
    """Schema de resumen de gastos por período."""
    fecha_desde: date
    fecha_hasta: date
    total: Decimal
    por_categoria: dict
    por_proyecto: dict
