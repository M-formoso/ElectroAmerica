from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.asignacion_diaria import EstadoAsignacion
from app.schemas.asignacion_diaria import (
    AsignacionDiariaCreate, AsignacionDiariaUpdate, AsignacionDiariaResponse,
    AsignacionDiariaListResponse, AsignacionMasivaRequest, AsignacionMasivaResponse,
    ResumenAsignacionesDia
)
from app.services import asignacion_diaria_service

router = APIRouter()


# ============== CRUD ASIGNACIONES ==============

@router.get("", response_model=List[AsignacionDiariaListResponse])
async def listar_asignaciones(
    fecha: Optional[date] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    operario_id: Optional[UUID] = None,
    proyecto_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Lista asignaciones con filtros."""
    estado_enum = EstadoAsignacion(estado) if estado else None

    asignaciones = asignacion_diaria_service.get_asignaciones(
        db,
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        operario_id=operario_id,
        proyecto_id=proyecto_id,
        estado=estado_enum,
        skip=skip,
        limit=limit
    )

    result = []
    for a in asignaciones:
        enriched = asignacion_diaria_service.enrich_asignacion_response(db, a)
        result.append(AsignacionDiariaListResponse(
            id=a.id,
            fecha=a.fecha,
            operario_id=a.operario_id,
            operario_nombre=enriched.get("operario_nombre"),
            proyecto_nombre=enriched.get("proyecto_nombre"),
            vehiculo_patente=enriched.get("vehiculo_patente"),
            estado=a.estado,
            prioridad=a.prioridad,
            tiene_jornada=enriched.get("jornada_id") is not None
        ))
    return result


@router.get("/fecha/{fecha}", response_model=List[AsignacionDiariaResponse])
async def asignaciones_por_fecha(
    fecha: date,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene todas las asignaciones de una fecha específica."""
    asignaciones = asignacion_diaria_service.get_asignaciones(db, fecha=fecha, limit=1000)
    return [asignacion_diaria_service.enrich_asignacion_response(db, a) for a in asignaciones]


@router.get("/mis-asignaciones", response_model=List[AsignacionDiariaResponse])
async def mis_asignaciones_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene las asignaciones pendientes del operario actual."""
    asignaciones = asignacion_diaria_service.get_asignaciones_pendientes_operario(db, current_user.id)
    return [asignacion_diaria_service.enrich_asignacion_response(db, a) for a in asignaciones]


@router.get("/mis-asignaciones/hoy", response_model=List[AsignacionDiariaResponse])
async def mis_asignaciones_hoy(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene las asignaciones del operario actual para hoy."""
    asignaciones = asignacion_diaria_service.get_asignaciones_operario_fecha(
        db, current_user.id, date.today()
    )
    return [asignacion_diaria_service.enrich_asignacion_response(db, a) for a in asignaciones]


@router.get("/{asignacion_id}", response_model=AsignacionDiariaResponse)
async def obtener_asignacion(
    asignacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene una asignación por ID."""
    asignacion = asignacion_diaria_service.get_asignacion(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asignacion_diaria_service.enrich_asignacion_response(db, asignacion)


@router.post("", response_model=AsignacionDiariaResponse)
async def crear_asignacion(
    asignacion: AsignacionDiariaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Crea una nueva asignación diaria (solo supervisor/admin)."""
    nueva = asignacion_diaria_service.create_asignacion(db, asignacion, current_user.id)
    return asignacion_diaria_service.enrich_asignacion_response(db, nueva)


@router.post("/masiva", response_model=AsignacionMasivaResponse)
async def crear_asignaciones_masivas(
    request: AsignacionMasivaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """
    Crea múltiples asignaciones para una fecha (solo supervisor/admin).
    Útil para planificar el día siguiente.
    """
    asignaciones = asignacion_diaria_service.create_asignaciones_masivas(
        db, request, current_user.id
    )
    return AsignacionMasivaResponse(
        fecha=request.fecha,
        total_creadas=len(asignaciones),
        asignaciones=[
            asignacion_diaria_service.enrich_asignacion_response(db, a)
            for a in asignaciones
        ]
    )


@router.put("/{asignacion_id}", response_model=AsignacionDiariaResponse)
async def actualizar_asignacion(
    asignacion_id: UUID,
    asignacion: AsignacionDiariaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza una asignación (solo supervisor/admin)."""
    actualizada = asignacion_diaria_service.update_asignacion(db, asignacion_id, asignacion)
    if not actualizada:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asignacion_diaria_service.enrich_asignacion_response(db, actualizada)


@router.post("/{asignacion_id}/confirmar", response_model=AsignacionDiariaResponse)
async def confirmar_asignacion(
    asignacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """El operario confirma que vio/acepta la asignación."""
    asignacion = asignacion_diaria_service.confirmar_asignacion(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asignacion_diaria_service.enrich_asignacion_response(db, asignacion)


@router.post("/{asignacion_id}/cancelar", response_model=AsignacionDiariaResponse)
async def cancelar_asignacion(
    asignacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Cancela una asignación (solo supervisor/admin)."""
    asignacion = asignacion_diaria_service.cancelar_asignacion(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asignacion_diaria_service.enrich_asignacion_response(db, asignacion)


@router.delete("/{asignacion_id}")
async def eliminar_asignacion(
    asignacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina una asignación (solo supervisor/admin)."""
    if not asignacion_diaria_service.delete_asignacion(db, asignacion_id):
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return {"message": "Asignación eliminada"}


# ============== ESTADÍSTICAS ==============

@router.get("/resumen/dia", response_model=ResumenAsignacionesDia)
async def resumen_asignaciones_dia(
    fecha: date = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene resumen de asignaciones de un día (solo supervisor/admin)."""
    if not fecha:
        fecha = date.today()
    return asignacion_diaria_service.get_resumen_asignaciones_dia(db, fecha)
