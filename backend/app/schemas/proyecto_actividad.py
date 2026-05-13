"""
Schemas para actividades de proyecto y avances.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


# ============ Materiales Calculados ============

class MaterialDesgloseTarea(BaseModel):
    """Aporte de una tarea (proyecto_actividad) al total de un material."""
    proyecto_actividad_id: UUID
    actividad_tipo_id: UUID
    actividad_nombre: str
    cantidad_planificada: Decimal
    unidad_trabajo: Optional[str] = None
    cantidad_aporte: Decimal


class MaterialCalculado(BaseModel):
    """Material calculado para una actividad."""
    material_id: UUID
    material_nombre: str
    material_codigo: Optional[str] = None
    cantidad_total: Decimal
    unidad: str
    stock_actual: Optional[Decimal] = None
    # Solo se completa en el resumen total del proyecto (no en el calculo de
    # una sola actividad). Lista las tareas que aportan a este total.
    desglose_por_tarea: List[MaterialDesgloseTarea] = []


class MaterialConsumido(BaseModel):
    """Material consumido en un avance."""
    material_id: UUID
    material_nombre: str
    cantidad: Decimal
    unidad: str


# ============ Proyecto Actividad ============

class ProyectoActividadBase(BaseModel):
    """Schema base de actividad de proyecto."""
    cantidad_planificada: Decimal = Field(default=1, ge=0)
    observaciones: Optional[str] = None


class ProyectoActividadCreate(ProyectoActividadBase):
    """Schema para asignar actividad a proyecto."""
    actividad_tipo_id: UUID
    orden: Optional[int] = 0


class ProyectoActividadUpdate(BaseModel):
    """Schema para actualizar actividad de proyecto."""
    cantidad_planificada: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = None
    orden: Optional[int] = None


class ProyectoActividadResponse(ProyectoActividadBase):
    """Schema de respuesta de actividad de proyecto."""
    id: UUID
    proyecto_id: UUID
    actividad_tipo_id: UUID
    cantidad_ejecutada: Decimal
    orden: int
    materiales_calculados: Optional[List[MaterialCalculado]] = None
    porcentaje_avance: Decimal
    cantidad_pendiente: Decimal
    activo: bool
    created_at: datetime

    # Datos de la actividad tipo
    actividad_codigo: Optional[str] = None
    actividad_nombre: Optional[str] = None
    actividad_categoria: Optional[str] = None
    unidad_trabajo: Optional[str] = None

    class Config:
        from_attributes = True


class ProyectoActividadListResponse(BaseModel):
    """Schema de respuesta para lista de actividades."""
    id: UUID
    actividad_tipo_id: UUID
    actividad_codigo: Optional[str] = None
    actividad_nombre: Optional[str] = None
    actividad_categoria: Optional[str] = None
    unidad_trabajo: Optional[str] = None
    cantidad_planificada: Decimal
    cantidad_ejecutada: Decimal
    porcentaje_avance: Decimal
    orden: int

    class Config:
        from_attributes = True


# ============ Avance Actividad ============

class AvanceActividadBase(BaseModel):
    """Schema base de avance de actividad."""
    fecha: date
    cantidad: Decimal = Field(..., gt=0)
    observaciones: Optional[str] = None


class AvanceActividadCreate(AvanceActividadBase):
    """Schema para registrar avance."""
    materiales_consumidos: Optional[List[MaterialConsumido]] = None


class AvanceActividadUpdate(BaseModel):
    """Schema para actualizar avance."""
    cantidad: Optional[Decimal] = Field(None, gt=0)
    observaciones: Optional[str] = None
    materiales_consumidos: Optional[List[MaterialConsumido]] = None


class AvanceActividadResponse(AvanceActividadBase):
    """Schema de respuesta de avance."""
    id: UUID
    proyecto_actividad_id: UUID
    materiales_consumidos: Optional[List[MaterialConsumido]] = None
    registrado_por_id: Optional[UUID] = None
    registrado_por_nombre: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Proyecto Herramienta ============

class ProyectoHerramientaCreate(BaseModel):
    """Schema para asignar herramienta a proyecto."""
    herramienta_id: UUID
    fecha_asignacion: Optional[date] = None
    observaciones: Optional[str] = None


class ProyectoHerramientaResponse(BaseModel):
    """Schema de respuesta de herramienta asignada."""
    id: UUID
    proyecto_id: UUID
    herramienta_id: UUID
    herramienta_nombre: Optional[str] = None
    herramienta_codigo: Optional[str] = None
    fecha_asignacion: Optional[date] = None
    observaciones: Optional[str] = None
    activo: bool

    class Config:
        from_attributes = True


# ============ Bulk Operations ============

class AsignarActividadesRequest(BaseModel):
    """Schema para asignar múltiples actividades a un proyecto."""
    actividades: List[ProyectoActividadCreate]


class AsignarHerramientasRequest(BaseModel):
    """Schema para asignar múltiples herramientas a un proyecto."""
    herramientas_ids: List[UUID]


# ============ Resumen de Proyecto ============

class ResumenActividadesProyecto(BaseModel):
    """Resumen de actividades de un proyecto."""
    total_actividades: int
    actividades_completadas: int
    actividades_en_progreso: int
    actividades_pendientes: int
    porcentaje_avance_global: Decimal
    materiales_totales: List[MaterialCalculado]
