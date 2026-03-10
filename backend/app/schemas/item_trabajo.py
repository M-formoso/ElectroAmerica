from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.models.item_trabajo import EstadoItem


class ItemTrabajoBase(BaseModel):
    """Schema base de ítem de trabajo."""
    descripcion: str = Field(..., min_length=2, max_length=500)
    responsable: Optional[str] = Field(None, max_length=100)
    cantidad: Optional[Decimal] = Field(None, ge=0)
    unidad: Optional[str] = Field(None, max_length=30)
    estado: EstadoItem = EstadoItem.pendiente


class ItemTrabajoCreate(ItemTrabajoBase):
    """Schema para crear ítem de trabajo."""
    etapa_id: UUID
    precio_unitario: Optional[Decimal] = Field(None, ge=0)


class ItemTrabajoUpdate(BaseModel):
    """Schema para actualizar ítem de trabajo."""
    descripcion: Optional[str] = Field(None, min_length=2, max_length=500)
    responsable: Optional[str] = Field(None, max_length=100)
    cantidad: Optional[Decimal] = Field(None, ge=0)
    unidad: Optional[str] = Field(None, max_length=30)
    estado: Optional[EstadoItem] = None
    precio_unitario: Optional[Decimal] = Field(None, ge=0)


class ItemTrabajoResponse(ItemTrabajoBase):
    """Schema de respuesta de ítem de trabajo."""
    id: UUID
    etapa_id: UUID
    precio_unitario: Optional[Decimal] = None  # Solo para admin/supervisor
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True
