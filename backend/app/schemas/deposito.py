from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class DepositoMaterialBase(BaseModel):
    material_id: UUID
    stock_actual: Decimal = Field(default=Decimal("0"), ge=0)
    stock_minimo: Decimal = Field(default=Decimal("0"), ge=0)


class DepositoMaterialCreate(DepositoMaterialBase):
    pass


class DepositoMaterialUpdate(BaseModel):
    stock_actual: Optional[Decimal] = Field(None, ge=0)
    stock_minimo: Optional[Decimal] = Field(None, ge=0)


class DepositoMaterialResponse(DepositoMaterialBase):
    id: UUID
    deposito_id: UUID
    activo: bool
    # Info denormalizada del material
    material_codigo: Optional[str] = None
    material_nombre: Optional[str] = None
    material_unidad: Optional[str] = None

    class Config:
        from_attributes = True


class DepositoBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    direccion: Optional[str] = Field(None, max_length=255)
    descripcion: Optional[str] = None


class DepositoCreate(DepositoBase):
    cliente_id: UUID
    parent_id: Optional[UUID] = None  # Si es subdeposito, id del padre


class DepositoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    direccion: Optional[str] = Field(None, max_length=255)
    descripcion: Optional[str] = None


class DepositoResponse(DepositoBase):
    id: UUID
    cliente_id: UUID
    cliente_nombre: Optional[str] = None
    parent_id: Optional[UUID] = None
    activo: bool
    created_at: datetime
    cantidad_materiales: int = 0
    cantidad_subdepositos: int = 0

    class Config:
        from_attributes = True


class MaterialAgregado(BaseModel):
    """Material agregado (suma de stock en deposito + subdepositos)."""
    material_id: UUID
    material_codigo: Optional[str] = None
    material_nombre: Optional[str] = None
    material_unidad: Optional[str] = None
    stock_total: Decimal = Decimal("0")


class DepositoDetailResponse(DepositoResponse):
    materiales: List[DepositoMaterialResponse] = []
    subdepositos: List[DepositoResponse] = []
    # Suma agregada: stock del deposito + stock de todos los subdepositos
    materiales_totales: List[MaterialAgregado] = []


# ============ Operaciones especiales sobre materiales del deposito ============

class DepositoMaterialBulkItem(BaseModel):
    """Item de la carga masiva de materiales del catalogo al deposito."""
    material_id: UUID
    stock_actual: Decimal = Field(default=Decimal("0"), ge=0)
    stock_minimo: Decimal = Field(default=Decimal("0"), ge=0)


class DepositoMaterialBulkCreate(BaseModel):
    """Agregar varios materiales del catalogo al deposito en una sola operacion."""
    items: List[DepositoMaterialBulkItem]


class DepositoMaterialNuevoCreate(BaseModel):
    """Crear un material nuevo en el catalogo y agregarlo al deposito directamente.

    Se da de alta el material en el catalogo global (stock global = 0) y
    se carga el stock indicado al deposito.
    """
    codigo: Optional[str] = Field(None, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=200)
    descripcion: Optional[str] = None
    unidad: str = Field(..., max_length=50)
    precio_unitario: Optional[Decimal] = Field(None, ge=0)
    stock_actual: Decimal = Field(default=Decimal("0"), ge=0)
    stock_minimo: Decimal = Field(default=Decimal("0"), ge=0)


class DepositoMovimientoCreate(BaseModel):
    """Entrada o salida manual de un material en un deposito."""
    cantidad: Decimal = Field(..., gt=0)
    motivo: Optional[str] = Field(None, max_length=300)
