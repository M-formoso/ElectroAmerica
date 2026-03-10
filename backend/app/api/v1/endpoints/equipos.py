from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.equipo import TipoEquipo, EstadoEquipo
from app.schemas.equipo import (
    EquipoCreate, EquipoUpdate, EquipoResponse,
    AsignacionEquipoCreate, AsignacionEquipoResponse
)
from app.services import equipo_service

router = APIRouter()


@router.get("/", response_model=List[EquipoResponse])
def listar_equipos(
    tipo: Optional[TipoEquipo] = None,
    estado: Optional[EstadoEquipo] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista equipos con filtros opcionales."""
    return equipo_service.obtener_equipos(db, skip, limit, tipo, estado)


@router.get("/disponibles", response_model=List[EquipoResponse])
def listar_equipos_disponibles(
    fecha: Optional[date] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista equipos disponibles en una fecha específica."""
    return equipo_service.obtener_equipos_disponibles(db, fecha)


@router.post("/", response_model=EquipoResponse, status_code=status.HTTP_201_CREATED)
def crear_equipo(
    equipo: EquipoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Crea un nuevo equipo (solo admin/supervisor)."""
    return equipo_service.crear_equipo(db, equipo)


@router.get("/{equipo_id}", response_model=EquipoResponse)
def obtener_equipo(
    equipo_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene un equipo por ID."""
    equipo = equipo_service.obtener_equipo(db, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return equipo


@router.put("/{equipo_id}", response_model=EquipoResponse)
def actualizar_equipo(
    equipo_id: UUID,
    equipo: EquipoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza un equipo (solo admin/supervisor)."""
    db_equipo = equipo_service.actualizar_equipo(db, equipo_id, equipo)
    if not db_equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return db_equipo


@router.delete("/{equipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_equipo(
    equipo_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina un equipo (soft delete, solo admin/supervisor)."""
    if not equipo_service.eliminar_equipo(db, equipo_id):
        raise HTTPException(status_code=404, detail="Equipo no encontrado")


@router.post("/{equipo_id}/asignar", response_model=AsignacionEquipoResponse)
def asignar_equipo(
    equipo_id: UUID,
    asignacion: AsignacionEquipoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Asigna un equipo a un proyecto."""
    asignacion.equipo_id = equipo_id
    db_asignacion = equipo_service.asignar_equipo_a_proyecto(db, asignacion, usuario.id)

    return AsignacionEquipoResponse(
        id=db_asignacion.id,
        equipo_id=db_asignacion.equipo_id,
        proyecto_id=db_asignacion.proyecto_id,
        etapa_id=db_asignacion.etapa_id,
        fecha_desde=db_asignacion.fecha_desde,
        fecha_hasta=db_asignacion.fecha_hasta,
        observaciones=db_asignacion.observaciones,
        equipo_nombre=db_asignacion.equipo.nombre if db_asignacion.equipo else None,
        proyecto_nombre=db_asignacion.proyecto.nombre if db_asignacion.proyecto else None,
        created_at=db_asignacion.created_at
    )


@router.get("/{equipo_id}/historial", response_model=List[AsignacionEquipoResponse])
def obtener_historial(
    equipo_id: UUID,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene el historial de asignaciones de un equipo."""
    asignaciones = equipo_service.obtener_historial_equipo(db, equipo_id, limit)
    return [
        AsignacionEquipoResponse(
            id=a.id,
            equipo_id=a.equipo_id,
            proyecto_id=a.proyecto_id,
            etapa_id=a.etapa_id,
            fecha_desde=a.fecha_desde,
            fecha_hasta=a.fecha_hasta,
            observaciones=a.observaciones,
            equipo_nombre=a.equipo.nombre if a.equipo else None,
            proyecto_nombre=a.proyecto.nombre if a.proyecto else None,
            created_at=a.created_at
        )
        for a in asignaciones
    ]


@router.post("/asignacion/{asignacion_id}/finalizar", response_model=AsignacionEquipoResponse)
def finalizar_asignacion(
    asignacion_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Finaliza una asignación de equipo."""
    asignacion = equipo_service.finalizar_asignacion(db, asignacion_id)

    return AsignacionEquipoResponse(
        id=asignacion.id,
        equipo_id=asignacion.equipo_id,
        proyecto_id=asignacion.proyecto_id,
        etapa_id=asignacion.etapa_id,
        fecha_desde=asignacion.fecha_desde,
        fecha_hasta=asignacion.fecha_hasta,
        observaciones=asignacion.observaciones,
        equipo_nombre=asignacion.equipo.nombre if asignacion.equipo else None,
        proyecto_nombre=asignacion.proyecto.nombre if asignacion.proyecto else None,
        created_at=asignacion.created_at
    )
