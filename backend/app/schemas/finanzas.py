from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class PrecioItemCreate(BaseModel):
    """Schema para crear/actualizar precio de ítem."""
    item_trabajo_id: UUID
    precio_unitario: Decimal = Field(..., ge=0)


class PrecioItemResponse(BaseModel):
    """Schema de respuesta de precio de ítem."""
    id: UUID
    item_trabajo_id: UUID
    precio_unitario: Decimal
    fecha_desde: datetime
    fecha_hasta: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResumenCostosEtapa(BaseModel):
    """Schema de resumen de costos por etapa."""
    etapa_id: UUID
    nombre_etapa: str
    costo_items: Decimal
    costo_materiales: Decimal
    costo_total: Decimal


class ResumenFinancieroProyecto(BaseModel):
    """Schema de resumen financiero de proyecto."""
    proyecto_id: UUID
    nombre_proyecto: str
    monto_contratado: Optional[Decimal] = None
    costo_items: Decimal
    costo_materiales: Decimal
    costo_gastos: Decimal
    costo_total: Decimal
    rentabilidad: Optional[Decimal] = None
    porcentaje_rentabilidad: Optional[Decimal] = None
    etapas: List[ResumenCostosEtapa] = []


class ResumenFinancieroGeneral(BaseModel):
    """Schema de resumen financiero general."""
    total_contratado: Decimal
    total_costos: Decimal
    total_rentabilidad: Decimal
    proyectos_activos: int
    proyectos: List[ResumenFinancieroProyecto] = []


class ActualizarMontoRequest(BaseModel):
    """Schema para actualizar monto contratado."""
    monto: Decimal = Field(..., ge=0)
