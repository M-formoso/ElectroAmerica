from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class EstadoAsignacionEnum(str, Enum):
    planificada = "planificada"
    confirmada = "confirmada"
    en_curso = "en_curso"
    completada = "completada"
    cancelada = "cancelada"


class PrioridadEnum(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"
    urgente = "urgente"


# ============== TAREAS Y MATERIALES PLANIFICADOS ==============

class TareaPlanificada(BaseModel):
    """Tarea planificada para la asignación."""
    item_id: Optional[UUID] = None  # Si viene de un item_trabajo existente
    descripcion: str
    actividad_tipo_id: Optional[UUID] = None  # Si es una actividad tipo
    cantidad: Optional[float] = None  # Cantidad de trabajo (ej: 3 tableros)


class MaterialPlanificado(BaseModel):
    """Material planificado para la asignación."""
    material_id: UUID
    cantidad: float = Field(..., gt=0)
    notas: Optional[str] = None


# ============== ASIGNACIÓN DIARIA ==============

class AsignacionDiariaBase(BaseModel):
    fecha: date
    operario_id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    vehiculo_id: Optional[UUID] = None
    prioridad: PrioridadEnum = PrioridadEnum.media
    notas: Optional[str] = None


class AsignacionDiariaCreate(AsignacionDiariaBase):
    tareas_planificadas: List[TareaPlanificada] = []
    materiales_planificados: List[MaterialPlanificado] = []


class AsignacionDiariaUpdate(BaseModel):
    fecha: Optional[date] = None
    operario_id: Optional[UUID] = None
    proyecto_id: Optional[UUID] = None
    etapa_id: Optional[UUID] = None
    vehiculo_id: Optional[UUID] = None
    prioridad: Optional[PrioridadEnum] = None
    notas: Optional[str] = None
    tareas_planificadas: Optional[List[TareaPlanificada]] = None
    materiales_planificados: Optional[List[MaterialPlanificado]] = None


class AsignacionDiariaResponse(BaseModel):
    id: UUID
    fecha: date
    operario_id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    vehiculo_id: Optional[UUID] = None
    estado: EstadoAsignacionEnum
    prioridad: str
    notas: Optional[str] = None
    tareas_planificadas: Optional[List[Any]] = None  # JSONB
    materiales_planificados: Optional[List[Any]] = None  # JSONB
    creado_por_id: UUID
    created_at: datetime

    # Datos relacionados
    operario_nombre: Optional[str] = None
    proyecto_nombre: Optional[str] = None
    etapa_nombre: Optional[str] = None
    vehiculo_nombre: Optional[str] = None
    vehiculo_patente: Optional[str] = None

    # Estado de la jornada asociada
    jornada_id: Optional[UUID] = None
    jornada_estado: Optional[str] = None

    class Config:
        from_attributes = True


class AsignacionDiariaListResponse(BaseModel):
    """Schema simplificado para listados."""
    id: UUID
    fecha: date
    operario_id: UUID
    operario_nombre: Optional[str] = None
    proyecto_nombre: Optional[str] = None
    vehiculo_patente: Optional[str] = None
    estado: EstadoAsignacionEnum
    prioridad: str
    tiene_jornada: bool = False

    class Config:
        from_attributes = True


# ============== PLANIFICACIÓN MASIVA ==============

class AsignacionMasivaItem(BaseModel):
    """Item para crear múltiples asignaciones."""
    operario_id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    vehiculo_id: Optional[UUID] = None
    prioridad: PrioridadEnum = PrioridadEnum.media
    notas: Optional[str] = None
    tareas_planificadas: List[TareaPlanificada] = []
    materiales_planificados: List[MaterialPlanificado] = []


class AsignacionMasivaRequest(BaseModel):
    """Request para crear múltiples asignaciones en una fecha."""
    fecha: date
    asignaciones: List[AsignacionMasivaItem]


class AsignacionMasivaResponse(BaseModel):
    """Response de creación masiva."""
    fecha: date
    total_creadas: int
    asignaciones: List[AsignacionDiariaResponse]


# ============== CONSULTAS ==============

class FiltrosAsignacion(BaseModel):
    """Filtros para buscar asignaciones."""
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    operario_id: Optional[UUID] = None
    proyecto_id: Optional[UUID] = None
    estado: Optional[EstadoAsignacionEnum] = None
    prioridad: Optional[PrioridadEnum] = None


class ResumenAsignacionesDia(BaseModel):
    """Resumen de asignaciones de un día."""
    fecha: date
    total_asignaciones: int
    por_estado: dict  # {"planificada": 5, "en_curso": 3, ...}
    por_proyecto: List[dict]  # [{"proyecto_id": "...", "nombre": "...", "cantidad": 2}]
    operarios_asignados: int
    vehiculos_asignados: int
