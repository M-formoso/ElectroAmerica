from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.schemas.jornada import (
    JornadaCreate, JornadaUpdate, JornadaResponse,
    ResumenJornadasProyecto, ResumenJornadasUsuario
)
from app.services import jornadas_service

router = APIRouter()


@router.get("", response_model=List[JornadaResponse])
def listar_jornadas(
    proyecto_id: Optional[UUID] = None,
    usuario_id: Optional[UUID] = None,
    etapa_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Lista jornadas con filtros."""
    jornadas = jornadas_service.get_jornadas(
        db,
        proyecto_id=proyecto_id,
        usuario_id=usuario_id,
        etapa_id=etapa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit
    )

    return [
        JornadaResponse(
            id=j.id,
            usuario_id=j.usuario_id,
            proyecto_id=j.proyecto_id,
            etapa_id=j.etapa_id,
            fecha=j.fecha,
            horas_trabajadas=float(j.horas_trabajadas),
            horas_extra=float(j.horas_extra),
            costo_hora=float(j.costo_hora),
            costo_hora_extra=float(j.costo_hora_extra) if j.costo_hora_extra else None,
            descripcion=j.descripcion,
            notas=j.notas,
            registrado_por_id=j.registrado_por_id,
            created_at=j.created_at,
            costo_total=j.costo_total,
            usuario_nombre=f"{j.usuario.nombre} {j.usuario.apellido}" if j.usuario else None,
            proyecto_nombre=j.proyecto.nombre if j.proyecto else None,
            etapa_nombre=j.etapa.nombre if j.etapa else None
        )
        for j in jornadas
    ]


@router.get("/{jornada_id}", response_model=JornadaResponse)
def obtener_jornada(
    jornada_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene una jornada por ID."""
    j = jornadas_service.get_jornada(db, jornada_id)
    if not j:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")

    return JornadaResponse(
        id=j.id,
        usuario_id=j.usuario_id,
        proyecto_id=j.proyecto_id,
        etapa_id=j.etapa_id,
        fecha=j.fecha,
        horas_trabajadas=float(j.horas_trabajadas),
        horas_extra=float(j.horas_extra),
        costo_hora=float(j.costo_hora),
        costo_hora_extra=float(j.costo_hora_extra) if j.costo_hora_extra else None,
        descripcion=j.descripcion,
        notas=j.notas,
        registrado_por_id=j.registrado_por_id,
        created_at=j.created_at,
        costo_total=j.costo_total,
        usuario_nombre=f"{j.usuario.nombre} {j.usuario.apellido}" if j.usuario else None,
        proyecto_nombre=j.proyecto.nombre if j.proyecto else None,
        etapa_nombre=j.etapa.nombre if j.etapa else None
    )


@router.post("", response_model=JornadaResponse)
def crear_jornada(
    jornada: JornadaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Crea una nueva jornada."""
    j = jornadas_service.create_jornada(db, jornada, current_user.id)

    return JornadaResponse(
        id=j.id,
        usuario_id=j.usuario_id,
        proyecto_id=j.proyecto_id,
        etapa_id=j.etapa_id,
        fecha=j.fecha,
        horas_trabajadas=float(j.horas_trabajadas),
        horas_extra=float(j.horas_extra),
        costo_hora=float(j.costo_hora),
        costo_hora_extra=float(j.costo_hora_extra) if j.costo_hora_extra else None,
        descripcion=j.descripcion,
        notas=j.notas,
        registrado_por_id=j.registrado_por_id,
        created_at=j.created_at,
        costo_total=j.costo_total,
        usuario_nombre=f"{j.usuario.nombre} {j.usuario.apellido}" if j.usuario else None,
        proyecto_nombre=j.proyecto.nombre if j.proyecto else None,
        etapa_nombre=j.etapa.nombre if j.etapa else None
    )


@router.put("/{jornada_id}", response_model=JornadaResponse)
def actualizar_jornada(
    jornada_id: UUID,
    jornada: JornadaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza una jornada (solo admin/supervisor)."""
    j = jornadas_service.update_jornada(db, jornada_id, jornada)
    if not j:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")

    return JornadaResponse(
        id=j.id,
        usuario_id=j.usuario_id,
        proyecto_id=j.proyecto_id,
        etapa_id=j.etapa_id,
        fecha=j.fecha,
        horas_trabajadas=float(j.horas_trabajadas),
        horas_extra=float(j.horas_extra),
        costo_hora=float(j.costo_hora),
        costo_hora_extra=float(j.costo_hora_extra) if j.costo_hora_extra else None,
        descripcion=j.descripcion,
        notas=j.notas,
        registrado_por_id=j.registrado_por_id,
        created_at=j.created_at,
        costo_total=j.costo_total,
        usuario_nombre=f"{j.usuario.nombre} {j.usuario.apellido}" if j.usuario else None,
        proyecto_nombre=j.proyecto.nombre if j.proyecto else None,
        etapa_nombre=j.etapa.nombre if j.etapa else None
    )


@router.delete("/{jornada_id}")
def eliminar_jornada(
    jornada_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina una jornada (solo admin/supervisor)."""
    if not jornadas_service.delete_jornada(db, jornada_id):
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    return {"message": "Jornada eliminada"}


@router.get("/proyecto/{proyecto_id}/resumen", response_model=ResumenJornadasProyecto)
def resumen_proyecto(
    proyecto_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene resumen de jornadas por proyecto."""
    return jornadas_service.get_resumen_por_proyecto(db, proyecto_id, fecha_desde, fecha_hasta)


@router.get("/usuario/{usuario_id}/resumen", response_model=ResumenJornadasUsuario)
def resumen_usuario(
    usuario_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene resumen de jornadas por usuario (solo admin/supervisor)."""
    return jornadas_service.get_resumen_por_usuario(db, usuario_id, fecha_desde, fecha_hasta)


@router.get("/proyecto/{proyecto_id}/por-etapa")
def horas_por_etapa(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene horas trabajadas por etapa de un proyecto."""
    return jornadas_service.get_horas_por_etapa(db, proyecto_id)
