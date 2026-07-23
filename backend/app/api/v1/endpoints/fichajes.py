from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import date

from app.core.deps import get_db, require_admin_or_supervisor, require_any_authenticated
from app.models.usuario import Usuario
from app.models.fichaje import EstadoFichaje
from app.schemas.fichaje import (
    IniciarFichajeRequest, IniciarFichajeAdminRequest, FinalizarFichajeRequest,
    FichajeResponse, FichajeListResponse, ResumenFichajes,
)
from app.services import fichaje_service

router = APIRouter()


# ============ OPERARIO ============

@router.post("/iniciar", response_model=FichajeResponse)
def iniciar_fichaje(
    data: IniciarFichajeRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_authenticated),
):
    """El operario ficha su entrada."""
    return fichaje_service.iniciar_fichaje(db, current_user.id, data)


@router.get("/activo", response_model=Optional[FichajeResponse])
def obtener_fichaje_activo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_authenticated),
):
    """Obtiene el fichaje activo del operario actual, si existe."""
    fichaje = fichaje_service.obtener_fichaje_activo(db, current_user.id)
    if not fichaje:
        return None
    from app.services.fichaje_service import _to_response
    return _to_response(fichaje)


@router.post("/{fichaje_id}/finalizar", response_model=FichajeResponse)
def finalizar_fichaje(
    fichaje_id: UUID,
    data: FinalizarFichajeRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_authenticated),
):
    """El operario ficha su salida."""
    return fichaje_service.finalizar_fichaje(db, fichaje_id, current_user.id, data)


@router.post("/{fichaje_id}/cancelar", response_model=FichajeResponse)
def cancelar_fichaje(
    fichaje_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_authenticated),
):
    """Cancela un fichaje activo (operario o admin)."""
    return fichaje_service.cancelar_fichaje(db, fichaje_id, current_user.id)


@router.get("/mis-fichajes", response_model=List[FichajeListResponse])
def mis_fichajes(
    limit: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_authenticated),
):
    """Historial de fichajes del operario actual."""
    return fichaje_service.obtener_mis_fichajes(db, current_user.id, limit=limit)


# ============ ADMIN / SUPERVISOR ============

@router.get("/", response_model=List[FichajeListResponse])
def listar_fichajes(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    operario_id: Optional[UUID] = None,
    estado: Optional[EstadoFichaje] = None,
    skip: int = 0,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Lista todos los fichajes con filtros (solo admin/supervisor)."""
    return fichaje_service.listar_fichajes(
        db,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        operario_id=operario_id,
        estado=estado,
        skip=skip,
        limit=limit,
    )


@router.get("/admin/activos", response_model=List[FichajeListResponse])
def obtener_todos_activos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Lista todos los fichajes activos en este momento."""
    return fichaje_service.obtener_todos_activos(db)


@router.post("/admin/fichar-entrada", response_model=FichajeResponse)
def fichar_entrada_por_admin(
    data: IniciarFichajeAdminRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Admin/supervisor ficha la entrada de un operario."""
    return fichaje_service.iniciar_fichaje_admin(db, data.operario_id, data)


@router.post("/admin/{fichaje_id}/fichar-salida", response_model=FichajeResponse)
def fichar_salida_por_admin(
    fichaje_id: UUID,
    data: FinalizarFichajeRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """Admin/supervisor ficha la salida de cualquier fichaje activo."""
    return fichaje_service.finalizar_fichaje_admin(db, fichaje_id, data)


@router.get("/resumen", response_model=ResumenFichajes)
def resumen_fichajes(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    operario_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin_or_supervisor),
):
    """KPIs de fichajes para el panel admin."""
    return fichaje_service.resumen_fichajes(
        db,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        operario_id=operario_id,
    )
