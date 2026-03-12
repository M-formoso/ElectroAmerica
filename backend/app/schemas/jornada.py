from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class JornadaBase(BaseModel):
    usuario_id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    fecha: date
    horas_trabajadas: float = Field(..., gt=0, le=24)
    horas_extra: float = Field(default=0, ge=0, le=24)
    costo_hora: float = Field(..., gt=0)
    costo_hora_extra: Optional[float] = None
    descripcion: Optional[str] = None
    notas: Optional[str] = None


class JornadaCreate(JornadaBase):
    pass


class JornadaUpdate(BaseModel):
    etapa_id: Optional[UUID] = None
    fecha: Optional[date] = None
    horas_trabajadas: Optional[float] = None
    horas_extra: Optional[float] = None
    costo_hora: Optional[float] = None
    costo_hora_extra: Optional[float] = None
    descripcion: Optional[str] = None
    notas: Optional[str] = None


class JornadaResponse(JornadaBase):
    id: UUID
    registrado_por_id: UUID
    created_at: datetime

    # Campos calculados
    costo_total: float
    usuario_nombre: Optional[str] = None
    proyecto_nombre: Optional[str] = None
    etapa_nombre: Optional[str] = None

    class Config:
        from_attributes = True


class ResumenJornadasProyecto(BaseModel):
    proyecto_id: UUID
    proyecto_nombre: str
    total_horas: float
    total_horas_extra: float
    costo_total: float
    cantidad_jornadas: int


class ResumenJornadasUsuario(BaseModel):
    usuario_id: UUID
    usuario_nombre: str
    total_horas: float
    total_horas_extra: float
    costo_total: float
    cantidad_jornadas: int
