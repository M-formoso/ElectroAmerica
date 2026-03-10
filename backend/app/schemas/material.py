from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from app.models.movimiento_stock import TipoMovimiento


class MaterialBase(BaseModel):
    """Schema base de material."""
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., min_length=2, max_length=200)
    descripcion: Optional[str] = None
    unidad: str = Field(..., max_length=50)
    stock_minimo: Decimal = Field(default=0, ge=0)
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    ubicacion_almacen: Optional[str] = Field(None, max_length=100)


class MaterialCreate(MaterialBase):
    """Schema para crear material."""
    stock_actual: Decimal = Field(default=0, ge=0)


class MaterialUpdate(BaseModel):
    """Schema para actualizar material."""
    codigo: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    descripcion: Optional[str] = None
    unidad: Optional[str] = Field(None, max_length=50)
    stock_minimo: Optional[Decimal] = Field(None, ge=0)
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    ubicacion_almacen: Optional[str] = Field(None, max_length=100)


class MaterialResponse(MaterialBase):
    """Schema de respuesta de material."""
    id: UUID
    stock_actual: Decimal
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AsignacionMaterialCreate(BaseModel):
    """Schema para asignar material a proyecto."""
    material_id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    cantidad: Decimal = Field(..., gt=0)
    observaciones: Optional[str] = None


class AsignacionMaterialResponse(BaseModel):
    """Schema de respuesta de asignación de material."""
    id: UUID
    material_id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    cantidad: Decimal
    precio_unitario: Optional[Decimal] = None
    fecha: date
    observaciones: Optional[str] = None
    material_nombre: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IngresoStockCreate(BaseModel):
    """Schema para registrar ingreso de stock."""
    material_id: UUID
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    motivo: Optional[str] = Field(None, max_length=300)


class MovimientoStockResponse(BaseModel):
    """Schema de respuesta de movimiento de stock."""
    id: UUID
    material_id: UUID
    tipo: TipoMovimiento
    cantidad: Decimal
    stock_anterior: Decimal
    stock_nuevo: Decimal
    motivo: Optional[str] = None
    proyecto_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ValorInventarioResponse(BaseModel):
    """Schema de respuesta de valor total del inventario."""
    valor_total: Decimal
    total_items: int
    items_stock_bajo: int
