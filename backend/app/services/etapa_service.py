from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.models.etapa import Etapa, EstadoEtapa
from app.schemas.etapa import EtapaCreate, EtapaUpdate
from app.services import proyecto_service


def obtener_etapas(
    db: Session,
    proyecto_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Etapa]:
    """Obtiene lista de etapas, opcionalmente filtradas por proyecto."""
    query = db.query(Etapa).filter(Etapa.activo == True)

    if proyecto_id:
        query = query.filter(Etapa.proyecto_id == proyecto_id)

    return query.order_by(Etapa.orden).offset(skip).limit(limit).all()


def obtener_etapa(db: Session, etapa_id: UUID) -> Optional[Etapa]:
    """Obtiene una etapa por ID."""
    return db.query(Etapa).filter(
        Etapa.id == etapa_id,
        Etapa.activo == True
    ).first()


def crear_etapa(db: Session, etapa: EtapaCreate) -> Etapa:
    """Crea una nueva etapa."""
    # Obtener el orden máximo actual
    max_orden = db.query(Etapa).filter(
        Etapa.proyecto_id == etapa.proyecto_id,
        Etapa.activo == True
    ).count()

    db_etapa = Etapa(
        proyecto_id=etapa.proyecto_id,
        nombre=etapa.nombre,
        descripcion=etapa.descripcion,
        orden=etapa.orden if etapa.orden > 0 else max_orden,
        fecha_inicio_est=etapa.fecha_inicio_est,
        fecha_fin_est=etapa.fecha_fin_est,
        estado=etapa.estado
    )
    db.add(db_etapa)
    db.commit()
    db.refresh(db_etapa)
    return db_etapa


def actualizar_etapa(
    db: Session,
    etapa_id: UUID,
    etapa: EtapaUpdate
) -> Optional[Etapa]:
    """Actualiza una etapa existente."""
    db_etapa = obtener_etapa(db, etapa_id)
    if not db_etapa:
        return None

    update_data = etapa.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_etapa, field, value)

    db.commit()
    db.refresh(db_etapa)

    # Recalcular avance del proyecto
    proyecto_service.recalcular_avance_proyecto(db, db_etapa.proyecto_id)

    return db_etapa


def eliminar_etapa(db: Session, etapa_id: UUID) -> bool:
    """Soft delete de etapa."""
    etapa = obtener_etapa(db, etapa_id)
    if not etapa:
        return False

    proyecto_id = etapa.proyecto_id
    etapa.activo = False
    db.commit()

    # Recalcular avance del proyecto
    proyecto_service.recalcular_avance_proyecto(db, proyecto_id)

    return True


def actualizar_avance_etapa(
    db: Session,
    etapa_id: UUID,
    porcentaje: Decimal
) -> Optional[Etapa]:
    """Actualiza el porcentaje de avance de una etapa."""
    etapa = obtener_etapa(db, etapa_id)
    if not etapa:
        return None

    etapa.porcentaje_avance = min(max(porcentaje, Decimal(0)), Decimal(100))

    # Si llega a 100%, marcar como completada
    if etapa.porcentaje_avance >= Decimal(100):
        etapa.estado = EstadoEtapa.completada
    elif etapa.porcentaje_avance > Decimal(0) and etapa.estado == EstadoEtapa.pendiente:
        etapa.estado = EstadoEtapa.en_progreso

    db.commit()
    db.refresh(etapa)

    # Recalcular avance del proyecto
    proyecto_service.recalcular_avance_proyecto(db, etapa.proyecto_id)

    return etapa


def reordenar_etapas(db: Session, proyecto_id: UUID, orden_ids: List[UUID]) -> bool:
    """Reordena las etapas de un proyecto."""
    for idx, etapa_id in enumerate(orden_ids):
        db.query(Etapa).filter(
            Etapa.id == etapa_id,
            Etapa.proyecto_id == proyecto_id
        ).update({"orden": idx})

    db.commit()
    return True


def obtener_etapas_demoradas(db: Session) -> List[Etapa]:
    """Obtiene etapas cuya fecha estimada de fin ha pasado y no están completadas."""
    from datetime import date

    return db.query(Etapa).filter(
        Etapa.activo == True,
        Etapa.fecha_fin_est < date.today(),
        Etapa.estado.notin_([EstadoEtapa.completada])
    ).all()
