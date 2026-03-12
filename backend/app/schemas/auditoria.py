"""Schemas de auditoría."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, date
from enum import Enum


class TipoAccion(str, Enum):
    crear = "crear"
    actualizar = "actualizar"
    eliminar = "eliminar"
    login = "login"
    logout = "logout"
    ver = "ver"
    exportar = "exportar"
    asignar = "asignar"
    desasignar = "desasignar"
    cambiar_estado = "cambiar_estado"
    subir_archivo = "subir_archivo"


class ModuloAuditado(str, Enum):
    auth = "auth"
    usuarios = "usuarios"
    proyectos = "proyectos"
    etapas = "etapas"
    items_trabajo = "items_trabajo"
    materiales = "materiales"
    equipos = "equipos"
    gastos = "gastos"
    clientes = "clientes"
    fotos = "fotos"
    reportes = "reportes"
    finanzas = "finanzas"
    alertas = "alertas"
    jornadas = "jornadas"


class AuditoriaBase(BaseModel):
    """Base para auditoría."""
    accion: TipoAccion
    modulo: ModuloAuditado
    descripcion: str
    recurso_id: Optional[UUID] = None
    recurso_tipo: Optional[str] = None
    datos_adicionales: Optional[Dict[str, Any]] = None


class AuditoriaResponse(AuditoriaBase):
    """Respuesta de auditoría."""
    id: UUID
    usuario_id: Optional[UUID] = None
    usuario_nombre: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResumenActividadResponse(BaseModel):
    """Resumen de actividad del sistema."""
    periodo: Dict[str, str]
    total_acciones: int
    acciones_por_tipo: Dict[str, int]
    acciones_por_modulo: Dict[str, int]
    usuarios_mas_activos: List[Dict[str, Any]]


class FiltrosAuditoria(BaseModel):
    """Filtros para búsqueda de auditorías."""
    usuario_id: Optional[UUID] = None
    modulo: Optional[ModuloAuditado] = None
    accion: Optional[TipoAccion] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    recurso_id: Optional[UUID] = None
    skip: int = 0
    limit: int = 50
