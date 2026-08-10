from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from app.models.fichaje import EstadoFichaje


class IniciarFichajeRequest(BaseModel):
    proyecto_id: Optional[UUID] = None
    notas_inicio: Optional[str] = None


class IniciarFichajeAdminRequest(BaseModel):
    operario_id: UUID
    proyecto_id: Optional[UUID] = None
    notas_inicio: Optional[str] = None
    hora_manual: Optional[str] = None  # "HH:MM" en hora Argentina
    fecha_manual: Optional[date] = None  # YYYY-MM-DD; default = hoy en Argentina


class FinalizarFichajeRequest(BaseModel):
    notas_fin: Optional[str] = None


class FinalizarFichajeAdminRequest(BaseModel):
    notas_fin: Optional[str] = None
    hora_manual: Optional[str] = None  # "HH:MM" en hora Argentina
    fecha_manual: Optional[date] = None  # YYYY-MM-DD; default = hoy en Argentina


class MarcarInasistenciaRequest(BaseModel):
    operario_id: UUID
    fecha: date
    motivo: Optional[str] = None


class FichajeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    operario_id: UUID
    operario_nombre: Optional[str] = None
    operario_apellido: Optional[str] = None
    fecha: date
    hora_inicio: datetime
    hora_fin: Optional[datetime] = None
    horas_trabajadas: Optional[Decimal] = None
    estado: EstadoFichaje
    proyecto_id: Optional[UUID] = None
    proyecto_nombre: Optional[str] = None
    notas_inicio: Optional[str] = None
    notas_fin: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FichajeListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    operario_id: UUID
    operario_nombre: Optional[str] = None
    operario_apellido: Optional[str] = None
    fecha: date
    hora_inicio: datetime
    hora_fin: Optional[datetime] = None
    horas_trabajadas: Optional[Decimal] = None
    estado: EstadoFichaje
    proyecto_id: Optional[UUID] = None
    proyecto_nombre: Optional[str] = None


class ResumenFichajes(BaseModel):
    total_fichajes: int
    fichajes_activos: int
    fichajes_completados: int
    horas_totales: Decimal
    promedio_horas: Decimal
