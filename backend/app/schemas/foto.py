from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class FotoCreate(BaseModel):
    """Schema para crear foto."""
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    url: str = Field(..., max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    descripcion: Optional[str] = None
    fecha: date
    visible_cliente: bool = False


class FotoUpdate(BaseModel):
    """Schema para actualizar foto."""
    descripcion: Optional[str] = None
    visible_cliente: Optional[bool] = None


class FotoResponse(BaseModel):
    """Schema de respuesta de foto."""
    id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    url: str
    thumbnail_url: Optional[str] = None
    descripcion: Optional[str] = None
    fecha: date
    visible_cliente: bool
    created_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True


class FotoClienteResponse(BaseModel):
    """Schema de respuesta de foto para cliente."""
    id: UUID
    url: str
    descripcion: Optional[str] = None
    fecha: date

    class Config:
        from_attributes = True
