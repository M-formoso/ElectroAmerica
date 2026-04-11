from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class EstadoJornadaEnum(str, Enum):
    planificada = "planificada"
    iniciada = "iniciada"
    en_camino = "en_camino"
    en_obra = "en_obra"
    finalizada = "finalizada"
    cancelada = "cancelada"


class EstadoMaterialJornadaEnum(str, Enum):
    asignado = "asignado"
    pendiente_retiro = "pendiente_retiro"
    cargado = "cargado"
    en_uso = "en_uso"
    consumido = "consumido"
    devuelto_deposito = "devuelto_deposito"
    devuelto_obra = "devuelto_obra"


class DestinoDevolucionEnum(str, Enum):
    deposito = "deposito"
    obra = "obra"
    otro_operario = "otro_operario"


# ============== MATERIAL JORNADA ==============

class MaterialJornadaBase(BaseModel):
    material_id: UUID
    cantidad_asignada: float = Field(..., gt=0)
    notas: Optional[str] = None


class MaterialJornadaCreate(MaterialJornadaBase):
    pass


class MaterialJornadaCargar(BaseModel):
    """Schema para cuando el operario confirma materiales cargados."""
    material_id: UUID
    cantidad_cargada: float = Field(..., ge=0)
    notas: Optional[str] = None


class MaterialJornadaRendir(BaseModel):
    """Schema para rendición de materiales al cerrar jornada."""
    material_id: UUID
    cantidad_consumida: float = Field(..., ge=0)
    cantidad_devuelta: float = Field(default=0, ge=0)
    destino_devolucion: Optional[DestinoDevolucionEnum] = None
    notas: Optional[str] = None


class MaterialJornadaResponse(BaseModel):
    id: UUID
    jornada_id: UUID
    material_id: UUID
    cantidad_asignada: float
    cantidad_cargada: Optional[float] = None
    cantidad_consumida: Optional[float] = None
    cantidad_devuelta: Optional[float] = None
    estado: EstadoMaterialJornadaEnum
    destino_devolucion: Optional[DestinoDevolucionEnum] = None
    notas: Optional[str] = None
    actividad_tipo_id: Optional[UUID] = None

    # Datos del material
    material_codigo: Optional[str] = None
    material_nombre: Optional[str] = None
    material_unidad: Optional[str] = None

    class Config:
        from_attributes = True


# ============== JORNADA OPERARIO ==============

class JornadaOperarioBase(BaseModel):
    fecha: date
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    vehiculo_id: Optional[UUID] = None


class IniciarJornadaRequest(BaseModel):
    """Schema para iniciar una jornada."""
    vehiculo_id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    km_inicial: Optional[int] = None
    observaciones: Optional[str] = None
    materiales: List[MaterialJornadaCargar] = []  # Materiales que confirma cargar


class MarcarLlegadaRequest(BaseModel):
    """Schema para marcar llegada a obra."""
    observaciones: Optional[str] = None


class CerrarJornadaRequest(BaseModel):
    """Schema para cerrar una jornada."""
    km_final: Optional[int] = None
    horas_trabajadas: Optional[float] = None
    horas_extra: Optional[float] = None
    observaciones: Optional[str] = None
    materiales: List[MaterialJornadaRendir] = []  # Rendición de materiales


class ReportarNovedadRequest(BaseModel):
    """Schema para reportar novedades durante la jornada."""
    novedad: str = Field(..., min_length=10)
    es_urgente: bool = False


class JornadaOperarioCreate(JornadaOperarioBase):
    """Schema para crear jornada desde asignación (uso interno)."""
    operario_id: UUID
    asignacion_diaria_id: Optional[UUID] = None


class JornadaOperarioUpdate(BaseModel):
    vehiculo_id: Optional[UUID] = None
    proyecto_id: Optional[UUID] = None
    etapa_id: Optional[UUID] = None
    km_inicial: Optional[int] = None
    km_final: Optional[int] = None
    observaciones_inicio: Optional[str] = None
    observaciones_cierre: Optional[str] = None
    novedades: Optional[str] = None


class JornadaOperarioResponse(BaseModel):
    id: UUID
    operario_id: UUID
    fecha: date
    vehiculo_id: Optional[UUID] = None
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    km_inicial: Optional[int] = None
    km_final: Optional[int] = None
    hora_inicio: Optional[datetime] = None
    hora_llegada_obra: Optional[datetime] = None
    hora_fin: Optional[datetime] = None
    horas_trabajadas: Optional[float] = None
    horas_extra: Optional[float] = None
    estado: EstadoJornadaEnum
    observaciones_inicio: Optional[str] = None
    observaciones_cierre: Optional[str] = None
    novedades: Optional[str] = None
    asignacion_diaria_id: Optional[UUID] = None
    created_at: datetime

    # Datos relacionados
    operario_nombre: Optional[str] = None
    vehiculo_nombre: Optional[str] = None
    vehiculo_patente: Optional[str] = None
    proyecto_nombre: Optional[str] = None
    etapa_nombre: Optional[str] = None

    # Propiedades calculadas
    km_recorridos: Optional[int] = None
    duracion_total: Optional[float] = None

    # Materiales
    materiales: List[MaterialJornadaResponse] = []

    class Config:
        from_attributes = True


class JornadaOperarioListResponse(BaseModel):
    """Schema simplificado para listados."""
    id: UUID
    operario_id: UUID
    operario_nombre: Optional[str] = None
    fecha: date
    vehiculo_patente: Optional[str] = None
    proyecto_nombre: Optional[str] = None
    etapa_nombre: Optional[str] = None
    estado: EstadoJornadaEnum
    hora_inicio: Optional[datetime] = None
    hora_fin: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== RESÚMENES Y ESTADÍSTICAS ==============

class ResumenJornadasOperario(BaseModel):
    """Resumen de jornadas de un operario."""
    operario_id: UUID
    operario_nombre: str
    total_jornadas: int
    jornadas_completadas: int
    total_horas: float
    total_km: int
    proyectos_visitados: int


class EstadisticasJornadasDia(BaseModel):
    """Estadísticas de jornadas de un día."""
    fecha: date
    total_operarios: int
    jornadas_planificadas: int
    jornadas_iniciadas: int
    jornadas_en_obra: int
    jornadas_finalizadas: int
