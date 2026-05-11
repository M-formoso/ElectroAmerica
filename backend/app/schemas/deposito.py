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


class DepositoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    direccion: Optional[str] = Field(None, max_length=255)
    descripcion: Optional[str] = None


class DepositoResponse(DepositoBase):
    id: UUID
    cliente_id: UUID
    cliente_nombre: Optional[str] = None
    activo: bool
    created_at: datetime
    cantidad_materiales: int = 0

    class Config:
        from_attributes = True


class DepositoDetailResponse(DepositoResponse):
    materiales: List[DepositoMaterialResponse] = []
