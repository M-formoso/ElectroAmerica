from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.jornada_operario import EstadoJornada
from app.schemas.jornada_operario import (
    JornadaOperarioResponse, JornadaOperarioListResponse,
    IniciarJornadaRequest, MarcarLlegadaRequest, CerrarJornadaRequest,
    ReportarNovedadRequest, EstadisticasJornadasDia
)
from app.services import jornada_operario_service

router = APIRouter()


# ============== ENDPOINTS PARA OPERARIOS ==============

@router.get("/mi-jornada", response_model=Optional[JornadaOperarioResponse])
async def obtener_mi_jornada_activa(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene la jornada activa del operario actual."""
    jornada = jornada_operario_service.get_jornada_activa_operario(db, current_user.id)
    if not jornada:
        return None
    return jornada_operario_service.enrich_jornada_response(db, jornada)


@router.post("/iniciar", response_model=JornadaOperarioResponse)
async def iniciar_jornada(
    data: IniciarJornadaRequest,
    asignacion_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """
    Inicia una nueva jornada para el operario.

    El operario debe seleccionar:
    - Vehículo en el que viaja
    - Proyecto/obra de destino
    - Etapa/zona específica (opcional)
    - Materiales que carga (confirmación)
    """
    try:
        jornada = jornada_operario_service.iniciar_jornada(
            db, current_user.id, data, asignacion_id
        )
        return jornada_operario_service.enrich_jornada_response(db, jornada)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{jornada_id}/en-camino", response_model=JornadaOperarioResponse)
async def marcar_en_camino(
    jornada_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Marca que el operario está en camino a la obra."""
    try:
        jornada = jornada_operario_service.marcar_en_camino(db, jornada_id)
        return jornada_operario_service.enrich_jornada_response(db, jornada)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{jornada_id}/llegada", response_model=JornadaOperarioResponse)
async def marcar_llegada(
    jornada_id: UUID,
    data: MarcarLlegadaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Marca la llegada del operario a la obra."""
    try:
        jornada = jornada_operario_service.marcar_llegada_obra(db, jornada_id, data)
        return jornada_operario_service.enrich_jornada_response(db, jornada)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{jornada_id}/novedad", response_model=JornadaOperarioResponse)
async def reportar_novedad(
    jornada_id: UUID,
    data: ReportarNovedadRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Reporta una novedad durante la jornada."""
    try:
        jornada = jornada_operario_service.reportar_novedad(
            db, jornada_id, data.novedad, data.es_urgente, current_user.id
        )
        return jornada_operario_service.enrich_jornada_response(db, jornada)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{jornada_id}/cerrar", response_model=JornadaOperarioResponse)
async def cerrar_jornada(
    jornada_id: UUID,
    data: CerrarJornadaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """
    Cierra una jornada con rendición de materiales.

    El operario debe indicar:
    - Km final del vehículo
    - Horas trabajadas (si no se calculan automáticamente)
    - Materiales consumidos y sobrantes
    - Destino de los materiales sobrantes
    """
    try:
        jornada = jornada_operario_service.cerrar_jornada(db, jornada_id, data)
        return jornada_operario_service.enrich_jornada_response(db, jornada)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== ENDPOINTS PARA SUPERVISORES ==============

@router.get("/activas", response_model=List[JornadaOperarioListResponse])
async def listar_jornadas_activas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Lista todas las jornadas activas (en curso). Solo supervisor/admin."""
    jornadas = jornada_operario_service.get_jornadas_activas(db)
    result = []
    for j in jornadas:
        enriched = jornada_operario_service.enrich_jornada_response(db, j)
        result.append(JornadaOperarioListResponse(
            id=j.id,
            operario_id=j.operario_id,
            operario_nombre=enriched.get("operario_nombre"),
            fecha=j.fecha,
            vehiculo_patente=enriched.get("vehiculo_patente"),
            proyecto_nombre=enriched.get("proyecto_nombre"),
            etapa_nombre=enriched.get("etapa_nombre"),
            estado=j.estado,
            hora_inicio=j.hora_inicio,
            hora_fin=j.hora_fin
        ))
    return result


@router.get("", response_model=List[JornadaOperarioListResponse])
async def listar_jornadas(
    operario_id: Optional[UUID] = None,
    proyecto_id: Optional[UUID] = None,
    fecha: Optional[date] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    estado: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Lista jornadas con filtros."""
    estado_enum = EstadoJornada(estado) if estado else None

    jornadas = jornada_operario_service.get_jornadas_operario(
        db,
        operario_id=operario_id,
        proyecto_id=proyecto_id,
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        estado=estado_enum,
        skip=skip,
        limit=limit
    )

    result = []
    for j in jornadas:
        enriched = jornada_operario_service.enrich_jornada_response(db, j)
        result.append(JornadaOperarioListResponse(
            id=j.id,
            operario_id=j.operario_id,
            operario_nombre=enriched.get("operario_nombre"),
            fecha=j.fecha,
            vehiculo_patente=enriched.get("vehiculo_patente"),
            proyecto_nombre=enriched.get("proyecto_nombre"),
            etapa_nombre=enriched.get("etapa_nombre"),
            estado=j.estado,
            hora_inicio=j.hora_inicio,
            hora_fin=j.hora_fin
        ))
    return result


@router.get("/{jornada_id}", response_model=JornadaOperarioResponse)
async def obtener_jornada(
    jornada_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene una jornada por ID."""
    jornada = jornada_operario_service.get_jornada_operario(db, jornada_id)
    if not jornada:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")
    return jornada_operario_service.enrich_jornada_response(db, jornada)


@router.post("/{jornada_id}/cancelar", response_model=JornadaOperarioResponse)
async def cancelar_jornada(
    jornada_id: UUID,
    motivo: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Cancela una jornada (solo supervisor/admin). Devuelve materiales al stock."""
    try:
        jornada = jornada_operario_service.cancelar_jornada(db, jornada_id, motivo)
        return jornada_operario_service.enrich_jornada_response(db, jornada)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/estadisticas/dia", response_model=EstadisticasJornadasDia)
async def estadisticas_del_dia(
    fecha: date = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene estadísticas de jornadas de un día (solo supervisor/admin)."""
    if not fecha:
        fecha = date.today()
    return jornada_operario_service.get_estadisticas_dia(db, fecha)


@router.get("/historial/mi-historial", response_model=List[JornadaOperarioListResponse])
async def mi_historial_jornadas(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene el historial de jornadas del operario actual."""
    jornadas = jornada_operario_service.get_jornadas_operario(
        db,
        operario_id=current_user.id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit
    )

    result = []
    for j in jornadas:
        enriched = jornada_operario_service.enrich_jornada_response(db, j)
        result.append(JornadaOperarioListResponse(
            id=j.id,
            operario_id=j.operario_id,
            operario_nombre=enriched.get("operario_nombre"),
            fecha=j.fecha,
            vehiculo_patente=enriched.get("vehiculo_patente"),
            proyecto_nombre=enriched.get("proyecto_nombre"),
            etapa_nombre=enriched.get("etapa_nombre"),
            estado=j.estado,
            hora_inicio=j.hora_inicio,
            hora_fin=j.hora_fin
        ))
    return result
