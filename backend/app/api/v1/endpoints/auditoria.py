"""Endpoints de auditoría."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, require_admin
from app.models.usuario import Usuario
from app.models.auditoria import TipoAccion, ModuloAuditado
from app.schemas.auditoria import (
    AuditoriaResponse,
    ResumenActividadResponse,
)
from app.services import auditoria_service

router = APIRouter()


@router.get("", response_model=List[AuditoriaResponse])
def listar_auditorias(
    usuario_id: Optional[UUID] = None,
    modulo: Optional[str] = None,
    accion: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    recurso_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Lista registros de auditoría con filtros (solo admin)."""
    # Convertir strings a enums si vienen
    modulo_enum = ModuloAuditado(modulo) if modulo else None
    accion_enum = TipoAccion(accion) if accion else None

    auditorias = auditoria_service.get_auditorias(
        db,
        usuario_id=usuario_id,
        modulo=modulo_enum,
        accion=accion_enum,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        recurso_id=recurso_id,
        skip=skip,
        limit=limit
    )

    return [
        AuditoriaResponse(
            id=a.id,
            usuario_id=a.usuario_id,
            usuario_nombre=f"{a.usuario.nombre} {a.usuario.apellido}" if a.usuario else None,
            accion=a.accion.value,
            modulo=a.modulo.value,
            descripcion=a.descripcion,
            recurso_id=a.recurso_id,
            recurso_tipo=a.recurso_tipo,
            datos_adicionales=a.datos_adicionales,
            ip_address=a.ip_address,
            user_agent=a.user_agent,
            created_at=a.created_at
        )
        for a in auditorias
    ]


@router.get("/usuario/{usuario_id}", response_model=List[AuditoriaResponse])
def obtener_auditoria_usuario(
    usuario_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Obtiene los registros de auditoría de un usuario (solo admin)."""
    auditorias = auditoria_service.get_auditoria_usuario(db, usuario_id, limit)

    return [
        AuditoriaResponse(
            id=a.id,
            usuario_id=a.usuario_id,
            usuario_nombre=f"{a.usuario.nombre} {a.usuario.apellido}" if a.usuario else None,
            accion=a.accion.value,
            modulo=a.modulo.value,
            descripcion=a.descripcion,
            recurso_id=a.recurso_id,
            recurso_tipo=a.recurso_tipo,
            datos_adicionales=a.datos_adicionales,
            ip_address=a.ip_address,
            user_agent=a.user_agent,
            created_at=a.created_at
        )
        for a in auditorias
    ]


@router.get("/recurso/{recurso_id}", response_model=List[AuditoriaResponse])
def obtener_auditoria_recurso(
    recurso_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Obtiene los registros de auditoría de un recurso (solo admin)."""
    auditorias = auditoria_service.get_auditoria_recurso(db, recurso_id, limit)

    return [
        AuditoriaResponse(
            id=a.id,
            usuario_id=a.usuario_id,
            usuario_nombre=f"{a.usuario.nombre} {a.usuario.apellido}" if a.usuario else None,
            accion=a.accion.value,
            modulo=a.modulo.value,
            descripcion=a.descripcion,
            recurso_id=a.recurso_id,
            recurso_tipo=a.recurso_tipo,
            datos_adicionales=a.datos_adicionales,
            ip_address=a.ip_address,
            user_agent=a.user_agent,
            created_at=a.created_at
        )
        for a in auditorias
    ]


@router.get("/resumen", response_model=ResumenActividadResponse)
def obtener_resumen_actividad(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Obtiene un resumen de la actividad del sistema (solo admin)."""
    return auditoria_service.get_resumen_actividad(db, fecha_desde, fecha_hasta)


@router.get("/logins/{usuario_id}", response_model=List[AuditoriaResponse])
def obtener_logins_usuario(
    usuario_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Obtiene los últimos logins de un usuario (solo admin)."""
    auditorias = auditoria_service.get_logins_usuario(db, usuario_id, limit)

    return [
        AuditoriaResponse(
            id=a.id,
            usuario_id=a.usuario_id,
            usuario_nombre=f"{a.usuario.nombre} {a.usuario.apellido}" if a.usuario else None,
            accion=a.accion.value,
            modulo=a.modulo.value,
            descripcion=a.descripcion,
            recurso_id=a.recurso_id,
            recurso_tipo=a.recurso_tipo,
            datos_adicionales=a.datos_adicionales,
            ip_address=a.ip_address,
            user_agent=a.user_agent,
            created_at=a.created_at
        )
        for a in auditorias
    ]


@router.get("/reciente", response_model=List[AuditoriaResponse])
def obtener_actividad_reciente(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Obtiene la actividad más reciente del sistema (solo admin)."""
    auditorias = auditoria_service.get_actividad_reciente(db, limit)

    return [
        AuditoriaResponse(
            id=a.id,
            usuario_id=a.usuario_id,
            usuario_nombre=f"{a.usuario.nombre} {a.usuario.apellido}" if a.usuario else None,
            accion=a.accion.value,
            modulo=a.modulo.value,
            descripcion=a.descripcion,
            recurso_id=a.recurso_id,
            recurso_tipo=a.recurso_tipo,
            datos_adicionales=a.datos_adicionales,
            ip_address=a.ip_address,
            user_agent=a.user_agent,
            created_at=a.created_at
        )
        for a in auditorias
    ]


@router.get("/tipos")
def obtener_tipos_accion():
    """Obtiene los tipos de acción disponibles."""
    return [{"value": t.value, "label": t.value.replace("_", " ").title()} for t in TipoAccion]


@router.get("/modulos")
def obtener_modulos():
    """Obtiene los módulos auditados disponibles."""
    return [{"value": m.value, "label": m.value.replace("_", " ").title()} for m in ModuloAuditado]
