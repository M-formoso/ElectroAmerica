from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.deps import get_db, get_usuario_actual, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.alerta import TipoAlerta, PrioridadAlerta
from app.schemas.alerta import (
    AlertaResponse, AlertaConteo, VerificacionResultado
)
from app.services import alertas_service

router = APIRouter()


@router.get("", response_model=List[AlertaResponse])
def listar_alertas(
    solo_no_leidas: bool = False,
    solo_no_resueltas: bool = True,
    tipo: Optional[str] = None,
    prioridad: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista las alertas del usuario."""
    tipo_enum = TipoAlerta(tipo) if tipo else None
    prioridad_enum = PrioridadAlerta(prioridad) if prioridad else None

    alertas = alertas_service.get_alertas(
        db,
        usuario_id=usuario.id,
        solo_no_leidas=solo_no_leidas,
        solo_no_resueltas=solo_no_resueltas,
        tipo=tipo_enum,
        prioridad=prioridad_enum,
        skip=skip,
        limit=limit
    )

    return [
        AlertaResponse(
            id=a.id,
            tipo=a.tipo,
            prioridad=a.prioridad,
            titulo=a.titulo,
            mensaje=a.mensaje,
            referencia_tipo=a.referencia_tipo,
            referencia_id=a.referencia_id,
            usuario_id=a.usuario_id,
            leida=a.leida,
            resuelta=a.resuelta,
            fecha_resolucion=a.fecha_resolucion,
            resuelto_por_id=a.resuelto_por_id,
            created_at=a.created_at
        )
        for a in alertas
    ]


@router.get("/conteo", response_model=AlertaConteo)
def contar_alertas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Obtiene el conteo de alertas por prioridad."""
    alertas = alertas_service.get_alertas(
        db,
        usuario_id=usuario.id,
        solo_no_resueltas=True,
        limit=500
    )

    return AlertaConteo(
        total=len(alertas),
        criticas=sum(1 for a in alertas if a.prioridad == 'critica'),
        altas=sum(1 for a in alertas if a.prioridad == 'alta'),
        medias=sum(1 for a in alertas if a.prioridad == 'media'),
        bajas=sum(1 for a in alertas if a.prioridad == 'baja'),
        no_leidas=sum(1 for a in alertas if not a.leida)
    )


@router.post("/{alerta_id}/leer", response_model=AlertaResponse)
def marcar_leida(
    alerta_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Marca una alerta como leída."""
    alerta = alertas_service.marcar_como_leida(db, alerta_id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    return AlertaResponse(
        id=alerta.id,
        tipo=alerta.tipo,
        prioridad=alerta.prioridad,
        titulo=alerta.titulo,
        mensaje=alerta.mensaje,
        referencia_tipo=alerta.referencia_tipo,
        referencia_id=alerta.referencia_id,
        usuario_id=alerta.usuario_id,
        leida=alerta.leida,
        resuelta=alerta.resuelta,
        fecha_resolucion=alerta.fecha_resolucion,
        resuelto_por_id=alerta.resuelto_por_id,
        created_at=alerta.created_at
    )


@router.post("/leer-todas")
def marcar_todas_leidas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Marca todas las alertas como leídas."""
    cantidad = alertas_service.marcar_todas_leidas(db, usuario.id)
    return {"message": f"Se marcaron {cantidad} alertas como leídas"}


@router.post("/{alerta_id}/resolver", response_model=AlertaResponse)
def resolver_alerta(
    alerta_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Marca una alerta como resuelta."""
    alerta = alertas_service.resolver_alerta(db, alerta_id, usuario.id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    return AlertaResponse(
        id=alerta.id,
        tipo=alerta.tipo,
        prioridad=alerta.prioridad,
        titulo=alerta.titulo,
        mensaje=alerta.mensaje,
        referencia_tipo=alerta.referencia_tipo,
        referencia_id=alerta.referencia_id,
        usuario_id=alerta.usuario_id,
        leida=alerta.leida,
        resuelta=alerta.resuelta,
        fecha_resolucion=alerta.fecha_resolucion,
        resuelto_por_id=alerta.resuelto_por_id,
        created_at=alerta.created_at
    )


@router.post("/verificar", response_model=VerificacionResultado)
def ejecutar_verificaciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Ejecuta todas las verificaciones y genera alertas (solo admin/supervisor)."""
    resultado = alertas_service.ejecutar_todas_verificaciones(db)
    return VerificacionResultado(**resultado)


@router.get("/tipos")
def obtener_tipos():
    """Obtiene los tipos de alerta disponibles."""
    return [
        {"value": t.value, "label": t.value.replace("_", " ").title()}
        for t in TipoAlerta
    ]


@router.get("/prioridades")
def obtener_prioridades():
    """Obtiene las prioridades disponibles."""
    return [
        {"value": p.value, "label": p.value.title()}
        for p in PrioridadAlerta
    ]
