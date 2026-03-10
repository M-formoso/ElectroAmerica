from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.models.item_trabajo import ItemTrabajo, EstadoItem
from app.schemas.item_trabajo import ItemTrabajoCreate, ItemTrabajoUpdate


def obtener_items(
    db: Session,
    etapa_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> List[ItemTrabajo]:
    """Obtiene lista de ítems de trabajo."""
    query = db.query(ItemTrabajo).filter(ItemTrabajo.activo == True)

    if etapa_id:
        query = query.filter(ItemTrabajo.etapa_id == etapa_id)

    return query.offset(skip).limit(limit).all()


def obtener_item(db: Session, item_id: UUID) -> Optional[ItemTrabajo]:
    """Obtiene un ítem de trabajo por ID."""
    return db.query(ItemTrabajo).filter(
        ItemTrabajo.id == item_id,
        ItemTrabajo.activo == True
    ).first()


def crear_item(db: Session, item: ItemTrabajoCreate) -> ItemTrabajo:
    """Crea un nuevo ítem de trabajo."""
    db_item = ItemTrabajo(
        etapa_id=item.etapa_id,
        descripcion=item.descripcion,
        responsable=item.responsable,
        cantidad=item.cantidad,
        unidad=item.unidad,
        estado=item.estado,
        precio_unitario=item.precio_unitario
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def actualizar_item(
    db: Session,
    item_id: UUID,
    item: ItemTrabajoUpdate
) -> Optional[ItemTrabajo]:
    """Actualiza un ítem de trabajo existente."""
    db_item = obtener_item(db, item_id)
    if not db_item:
        return None

    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item


def eliminar_item(db: Session, item_id: UUID) -> bool:
    """Soft delete de ítem de trabajo."""
    item = obtener_item(db, item_id)
    if not item:
        return False

    item.activo = False
    db.commit()
    return True


def marcar_completado(db: Session, item_id: UUID) -> Optional[ItemTrabajo]:
    """Marca un ítem como completado."""
    item = obtener_item(db, item_id)
    if not item:
        return None

    item.estado = EstadoItem.completado
    db.commit()
    db.refresh(item)
    return item


def obtener_items_por_estado(
    db: Session,
    etapa_id: UUID,
    estado: EstadoItem
) -> List[ItemTrabajo]:
    """Obtiene ítems de una etapa filtrados por estado."""
    return db.query(ItemTrabajo).filter(
        ItemTrabajo.etapa_id == etapa_id,
        ItemTrabajo.estado == estado,
        ItemTrabajo.activo == True
    ).all()
