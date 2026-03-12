from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class TipoAlerta(str, Enum):
    STOCK_MINIMO = "stock_minimo"
    DEMORA_ETAPA = "demora_etapa"
    ETAPA_PENDIENTE = "etapa_pendiente"
    LIMITE_CREDITO = "limite_credito"
    EQUIPO_MANTENIMIENTO = "equipo_mantenimiento"
    PROYECTO_VENCIDO = "proyecto_vencido"
    PAGO_PENDIENTE = "pago_pendiente"


class PrioridadAlerta(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class AlertaBase(BaseModel):
    tipo: TipoAlerta
    prioridad: PrioridadAlerta = PrioridadAlerta.MEDIA
    titulo: str
    mensaje: str
    referencia_tipo: Optional[str] = None
    referencia_id: Optional[UUID] = None
    usuario_id: Optional[UUID] = None


class AlertaCreate(AlertaBase):
    pass


class AlertaResponse(AlertaBase):
    id: UUID
    leida: bool
    resuelta: bool
    fecha_resolucion: Optional[datetime] = None
    resuelto_por_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertaConteo(BaseModel):
    total: int
    criticas: int
    altas: int
    medias: int
    bajas: int
    no_leidas: int


class VerificacionResultado(BaseModel):
    stock_minimo: int
    demoras_etapas: int
    equipos_mantenimiento: int
    limites_credito: int
    proyectos_vencidos: int
    total: int
