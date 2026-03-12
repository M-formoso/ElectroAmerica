from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.models.jornada import Jornada
from app.models.proyecto import Proyecto
from app.models.etapa import Etapa
from app.models.usuario import Usuario
from app.schemas.jornada import JornadaCreate, JornadaUpdate


def get_jornadas(
    db: Session,
    proyecto_id: Optional[UUID] = None,
    usuario_id: Optional[UUID] = None,
    etapa_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Jornada]:
    """Obtiene jornadas con filtros."""
    query = db.query(Jornada).filter(Jornada.activo == True)

    if proyecto_id:
        query = query.filter(Jornada.proyecto_id == proyecto_id)
    if usuario_id:
        query = query.filter(Jornada.usuario_id == usuario_id)
    if etapa_id:
        query = query.filter(Jornada.etapa_id == etapa_id)
    if fecha_desde:
        query = query.filter(Jornada.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Jornada.fecha <= fecha_hasta)

    return query.order_by(Jornada.fecha.desc()).offset(skip).limit(limit).all()


def get_jornada(db: Session, jornada_id: UUID) -> Optional[Jornada]:
    """Obtiene una jornada por ID."""
    return db.query(Jornada).filter(
        Jornada.id == jornada_id,
        Jornada.activo == True
    ).first()


def create_jornada(db: Session, jornada: JornadaCreate, registrado_por_id: UUID) -> Jornada:
    """Crea una nueva jornada."""
    db_jornada = Jornada(
        usuario_id=jornada.usuario_id,
        proyecto_id=jornada.proyecto_id,
        etapa_id=jornada.etapa_id,
        fecha=jornada.fecha,
        horas_trabajadas=Decimal(str(jornada.horas_trabajadas)),
        horas_extra=Decimal(str(jornada.horas_extra)),
        costo_hora=Decimal(str(jornada.costo_hora)),
        costo_hora_extra=Decimal(str(jornada.costo_hora_extra)) if jornada.costo_hora_extra else None,
        descripcion=jornada.descripcion,
        notas=jornada.notas,
        registrado_por_id=registrado_por_id
    )
    db.add(db_jornada)
    db.commit()
    db.refresh(db_jornada)
    return db_jornada


def update_jornada(db: Session, jornada_id: UUID, jornada: JornadaUpdate) -> Optional[Jornada]:
    """Actualiza una jornada."""
    db_jornada = get_jornada(db, jornada_id)
    if not db_jornada:
        return None

    update_data = jornada.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field in ['horas_trabajadas', 'horas_extra', 'costo_hora', 'costo_hora_extra']:
                value = Decimal(str(value))
            setattr(db_jornada, field, value)

    db.commit()
    db.refresh(db_jornada)
    return db_jornada


def delete_jornada(db: Session, jornada_id: UUID) -> bool:
    """Elimina una jornada (soft delete)."""
    db_jornada = get_jornada(db, jornada_id)
    if not db_jornada:
        return False

    db_jornada.activo = False
    db.commit()
    return True


def get_resumen_por_proyecto(
    db: Session,
    proyecto_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> dict:
    """Obtiene resumen de jornadas por proyecto."""
    query = db.query(
        func.sum(Jornada.horas_trabajadas).label('total_horas'),
        func.sum(Jornada.horas_extra).label('total_horas_extra'),
        func.count(Jornada.id).label('cantidad')
    ).filter(
        Jornada.proyecto_id == proyecto_id,
        Jornada.activo == True
    )

    if fecha_desde:
        query = query.filter(Jornada.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Jornada.fecha <= fecha_hasta)

    result = query.first()

    # Calcular costo total
    jornadas = get_jornadas(db, proyecto_id=proyecto_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    costo_total = sum(j.costo_total for j in jornadas)

    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()

    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto.nombre if proyecto else "",
        "total_horas": float(result.total_horas or 0),
        "total_horas_extra": float(result.total_horas_extra or 0),
        "costo_total": costo_total,
        "cantidad_jornadas": result.cantidad or 0
    }


def get_resumen_por_usuario(
    db: Session,
    usuario_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> dict:
    """Obtiene resumen de jornadas por usuario."""
    query = db.query(
        func.sum(Jornada.horas_trabajadas).label('total_horas'),
        func.sum(Jornada.horas_extra).label('total_horas_extra'),
        func.count(Jornada.id).label('cantidad')
    ).filter(
        Jornada.usuario_id == usuario_id,
        Jornada.activo == True
    )

    if fecha_desde:
        query = query.filter(Jornada.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Jornada.fecha <= fecha_hasta)

    result = query.first()

    # Calcular costo total
    jornadas = get_jornadas(db, usuario_id=usuario_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    costo_total = sum(j.costo_total for j in jornadas)

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    return {
        "usuario_id": usuario_id,
        "usuario_nombre": f"{usuario.nombre} {usuario.apellido}" if usuario else "",
        "total_horas": float(result.total_horas or 0),
        "total_horas_extra": float(result.total_horas_extra or 0),
        "costo_total": costo_total,
        "cantidad_jornadas": result.cantidad or 0
    }


def get_costo_mano_obra_proyecto(db: Session, proyecto_id: UUID) -> float:
    """Calcula el costo total de mano de obra de un proyecto."""
    jornadas = get_jornadas(db, proyecto_id=proyecto_id, limit=10000)
    return sum(j.costo_total for j in jornadas)


def get_horas_por_etapa(db: Session, proyecto_id: UUID) -> List[dict]:
    """Obtiene las horas trabajadas por etapa de un proyecto."""
    results = db.query(
        Etapa.id,
        Etapa.nombre,
        func.coalesce(func.sum(Jornada.horas_trabajadas), 0).label('horas'),
        func.coalesce(func.sum(Jornada.horas_extra), 0).label('horas_extra')
    ).outerjoin(
        Jornada, Jornada.etapa_id == Etapa.id
    ).filter(
        Etapa.proyecto_id == proyecto_id,
        Etapa.activo == True
    ).group_by(
        Etapa.id, Etapa.nombre
    ).all()

    return [
        {
            "etapa_id": str(r.id),
            "etapa_nombre": r.nombre,
            "horas": float(r.horas),
            "horas_extra": float(r.horas_extra)
        }
        for r in results
    ]
