from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import HTTPException
from app.models.equipo import Equipo, EstadoEquipo, TipoEquipo
from app.models.asignacion_equipo import AsignacionEquipo
from app.schemas.equipo import EquipoCreate, EquipoUpdate, AsignacionEquipoCreate


def obtener_equipos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    tipo: Optional[TipoEquipo] = None,
    estado: Optional[EstadoEquipo] = None
) -> List[Equipo]:
    """Obtiene lista de equipos."""
    query = db.query(Equipo).filter(Equipo.activo == True)

    if tipo:
        query = query.filter(Equipo.tipo == tipo)
    if estado:
        query = query.filter(Equipo.estado == estado)

    return query.order_by(Equipo.nombre).offset(skip).limit(limit).all()


def obtener_equipo(db: Session, equipo_id: UUID) -> Optional[Equipo]:
    """Obtiene un equipo por ID."""
    return db.query(Equipo).filter(
        Equipo.id == equipo_id,
        Equipo.activo == True
    ).first()


def crear_equipo(db: Session, equipo: EquipoCreate) -> Equipo:
    """Crea un nuevo equipo."""
    db_equipo = Equipo(
        codigo=equipo.codigo,
        nombre=equipo.nombre,
        descripcion=equipo.descripcion,
        tipo=equipo.tipo,
        marca=equipo.marca,
        modelo=equipo.modelo,
        estado=equipo.estado,
        fecha_adquisicion=equipo.fecha_adquisicion,
        costo_adquisicion=equipo.costo_adquisicion
    )
    db.add(db_equipo)
    db.commit()
    db.refresh(db_equipo)
    return db_equipo


def actualizar_equipo(
    db: Session,
    equipo_id: UUID,
    equipo: EquipoUpdate
) -> Optional[Equipo]:
    """Actualiza un equipo existente."""
    db_equipo = obtener_equipo(db, equipo_id)
    if not db_equipo:
        return None

    update_data = equipo.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_equipo, field, value)

    db.commit()
    db.refresh(db_equipo)
    return db_equipo


def eliminar_equipo(db: Session, equipo_id: UUID) -> bool:
    """Soft delete de equipo."""
    equipo = obtener_equipo(db, equipo_id)
    if not equipo:
        return False

    equipo.activo = False
    db.commit()
    return True


def obtener_equipos_disponibles(db: Session, fecha: date = None) -> List[Equipo]:
    """Retorna equipos que están disponibles en una fecha específica."""
    if fecha is None:
        fecha = date.today()

    # IDs de equipos con asignación activa en la fecha
    equipos_ocupados = db.query(AsignacionEquipo.equipo_id).filter(
        AsignacionEquipo.fecha_asignacion <= fecha,
        or_(
            AsignacionEquipo.fecha_devolucion_real.is_(None),
            AsignacionEquipo.fecha_devolucion_real >= fecha
        )
    ).subquery()

    return db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado.notin_([EstadoEquipo.mantenimiento, EstadoEquipo.fuera_servicio]),
        ~Equipo.id.in_(equipos_ocupados)
    ).all()


def asignar_equipo_a_proyecto(
    db: Session,
    asignacion: AsignacionEquipoCreate,
    usuario_id: UUID
) -> AsignacionEquipo:
    """Asigna un equipo a un proyecto."""
    equipo = obtener_equipo(db, asignacion.equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    if equipo.estado in [EstadoEquipo.mantenimiento, EstadoEquipo.fuera_servicio]:
        raise HTTPException(
            status_code=400,
            detail=f"El equipo está en {equipo.estado.value}"
        )

    # Verificar conflictos de fecha
    fecha_devolucion = asignacion.fecha_devolucion_est or date(2100, 1, 1)
    conflicto = db.query(AsignacionEquipo).filter(
        AsignacionEquipo.equipo_id == asignacion.equipo_id,
        AsignacionEquipo.fecha_asignacion <= fecha_devolucion,
        or_(
            AsignacionEquipo.fecha_devolucion_real.is_(None),
            AsignacionEquipo.fecha_devolucion_real >= asignacion.fecha_asignacion
        )
    ).first()

    if conflicto:
        raise HTTPException(
            status_code=400,
            detail="El equipo ya tiene una asignación en esas fechas"
        )

    # Crear asignación
    db_asignacion = AsignacionEquipo(
        equipo_id=asignacion.equipo_id,
        proyecto_id=asignacion.proyecto_id,
        fecha_asignacion=asignacion.fecha_asignacion,
        fecha_devolucion_est=asignacion.fecha_devolucion_est,
        notas=asignacion.notas,
        asignado_por_id=usuario_id
    )
    db.add(db_asignacion)

    # Actualizar estado del equipo
    equipo.estado = EstadoEquipo.asignado

    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion


def finalizar_asignacion(db: Session, asignacion_id: UUID) -> AsignacionEquipo:
    """Finaliza una asignación y libera el equipo."""
    asignacion = db.query(AsignacionEquipo).filter(
        AsignacionEquipo.id == asignacion_id
    ).first()

    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    asignacion.fecha_devolucion_real = date.today()

    # Verificar si tiene otras asignaciones activas
    otras = db.query(AsignacionEquipo).filter(
        AsignacionEquipo.equipo_id == asignacion.equipo_id,
        AsignacionEquipo.id != asignacion_id,
        or_(
            AsignacionEquipo.fecha_devolucion_real.is_(None),
            AsignacionEquipo.fecha_devolucion_real >= date.today()
        )
    ).first()

    if not otras:
        equipo = obtener_equipo(db, asignacion.equipo_id)
        if equipo:
            equipo.estado = EstadoEquipo.disponible

    db.commit()
    db.refresh(asignacion)
    return asignacion


def obtener_historial_equipo(
    db: Session,
    equipo_id: UUID,
    limit: int = 50
) -> List[AsignacionEquipo]:
    """Retorna el historial de asignaciones de un equipo."""
    return db.query(AsignacionEquipo).filter(
        AsignacionEquipo.equipo_id == equipo_id
    ).order_by(AsignacionEquipo.fecha_asignacion.desc()).limit(limit).all()
