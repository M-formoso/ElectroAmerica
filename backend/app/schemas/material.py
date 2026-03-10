from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from app.models.movimiento_stock import TipoMovimiento


class MaterialBase(BaseModel):
    """Schema base de material."""
    nombre: str = Field(..., min_length=2, max_length=255)
    codigo: Optional[str] = Field(None, max_length=50)
    categoria: Optional[str] = Field(None, max_length=100)
    unidad: str = Field(..., max_length=30)
    stock_minimo: Decimal = Field(default=0, ge=0)
    precio_costo: Optional[Decimal] = Field(None, ge=0)
    proveedor: Optional[str] = Field(None, max_length=255)


class MaterialCreate(MaterialBase):
    """Schema para crear material."""
    stock_actual: Decimal = Field(default=0, ge=0)


class MaterialUpdate(BaseModel):
    """Schema para actualizar material."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=255)
    codigo: Optional[str] = Field(None, max_length=50)
    categoria: Optional[str] = Field(None, max_length=100)
    unidad: Optional[str] = Field(None, max_length=30)
    stock_minimo: Optional[Decimal] = Field(None, ge=0)
    precio_costo: Optional[Decimal] = Field(None, ge=0)
    proveedor: Optional[str] = Field(None, max_length=255)


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
    proveedor: Optional[str] = Field(None, max_length=255)
    observaciones: Optional[str] = None


class MovimientoStockResponse(BaseModel):
    """Schema de respuesta de movimiento de stock."""
    id: UUID
    material_id: UUID
    tipo: TipoMovimiento
    cantidad: Decimal
    referencia_tipo: Optional[str] = None
    referencia_id: Optional[UUID] = None
    observaciones: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ValorInventarioResponse(BaseModel):
    """Schema de respuesta de valor total del inventario."""
    valor_total: Decimal
    total_items: int
    items_stock_bajo: int
