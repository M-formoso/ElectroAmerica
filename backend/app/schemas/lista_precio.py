from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class ListaPrecioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    descripcion: Optional[str] = None


class ListaPrecioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=120)
    descripcion: Optional[str] = None


class ListaPrecioResponse(BaseModel):
    id: UUID
    nombre: str
    descripcion: Optional[str] = None
    activo: bool
    created_at: datetime
    cantidad_actividades_con_precio: int = 0

    class Config:
        from_attributes = True


class PrecioActividadItem(BaseModel):
    """Item para listar precios de una lista: incluye la actividad
    completa (codigo y nombre) y el precio (puede ser 0 si no esta cargado).
    """
    actividad_tipo_id: UUID
    actividad_codigo: Optional[str] = None
    actividad_nombre: str
    actividad_unidad: Optional[str] = None
    precio_unitario: Decimal = Decimal("0")


class ListaPrecioDetailResponse(ListaPrecioResponse):
    items: List[PrecioActividadItem] = []


class PrecioBulkSet(BaseModel):
    """Setea precios de varias actividades en una lista en una sola llamada."""
    items: List["PrecioBulkItem"] = Field(..., min_length=1)


class PrecioBulkItem(BaseModel):
    actividad_tipo_id: UUID
    precio_unitario: Decimal = Field(..., ge=0)


PrecioBulkSet.model_rebuild()


class TotalProyectoItem(BaseModel):
    """Total presupuestado de un proyecto para mostrar en finanzas."""
    proyecto_id: UUID
    proyecto_nombre: str
    cliente_nombre: Optional[str] = None
    estado: Optional[str] = None
    lista_precio_id: Optional[UUID] = None
    lista_precio_nombre: Optional[str] = None
    cantidad_actividades: int = 0
    total_presupuestado: Decimal = Decimal("0")
    total_ejecutado: Decimal = Decimal("0")


class DetalleActividadPresupuesto(BaseModel):
    """Una linea del detalle del presupuesto de un proyecto."""
    proyecto_actividad_id: UUID
    actividad_tipo_id: UUID
    actividad_codigo: Optional[str] = None
    actividad_nombre: str
    unidad: Optional[str] = None
    cantidad_planificada: Decimal = Decimal("0")
    cantidad_ejecutada: Decimal = Decimal("0")
    precio_unitario_snapshot: Decimal = Decimal("0")
    subtotal_presupuestado: Decimal = Decimal("0")
    subtotal_ejecutado: Decimal = Decimal("0")


class DetallePresupuestoProyecto(BaseModel):
    """Detalle del presupuesto y ejecutado de un proyecto."""
    proyecto_id: UUID
    proyecto_nombre: str
    cliente_nombre: Optional[str] = None
    lista_precio_nombre: Optional[str] = None
    total_presupuestado: Decimal = Decimal("0")
    total_ejecutado: Decimal = Decimal("0")
    items: List[DetalleActividadPresupuesto] = []
