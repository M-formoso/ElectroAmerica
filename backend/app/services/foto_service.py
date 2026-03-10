from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.models.foto import Foto
from app.schemas.foto import FotoCreate, FotoUpdate


def obtener_fotos(
    db: Session,
    proyecto_id: Optional[UUID] = None,
    etapa_id: Optional[UUID] = None,
    solo_visible_cliente: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[Foto]:
    """Obtiene lista de fotos con filtros."""
    query = db.query(Foto).filter(Foto.activo == True)

    if proyecto_id:
        query = query.filter(Foto.proyecto_id == proyecto_id)
    if etapa_id:
        query = query.filter(Foto.etapa_id == etapa_id)
    if solo_visible_cliente:
        query = query.filter(Foto.visible_cliente == True)

    return query.order_by(Foto.fecha.desc()).offset(skip).limit(limit).all()


def obtener_foto(db: Session, foto_id: UUID) -> Optional[Foto]:
    """Obtiene una foto por ID."""
    return db.query(Foto).filter(
        Foto.id == foto_id,
        Foto.activo == True
    ).first()


def crear_foto(db: Session, foto: FotoCreate, usuario_id: UUID) -> Foto:
    """Crea una nueva foto."""
    db_foto = Foto(
        proyecto_id=foto.proyecto_id,
        etapa_id=foto.etapa_id,
        url=foto.url,
        thumbnail_url=foto.thumbnail_url,
        descripcion=foto.descripcion,
        fecha=foto.fecha,
        visible_cliente=foto.visible_cliente,
        created_by=usuario_id
    )
    db.add(db_foto)
    db.commit()
    db.refresh(db_foto)
    return db_foto


def actualizar_foto(
    db: Session,
    foto_id: UUID,
    foto: FotoUpdate
) -> Optional[Foto]:
    """Actualiza una foto existente."""
    db_foto = obtener_foto(db, foto_id)
    if not db_foto:
        return None

    update_data = foto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_foto, field, value)

    db.commit()
    db.refresh(db_foto)
    return db_foto


def eliminar_foto(db: Session, foto_id: UUID) -> bool:
    """Soft delete de foto."""
    foto = obtener_foto(db, foto_id)
    if not foto:
        return False

    foto.activo = False
    db.commit()
    return True


def marcar_visible_cliente(db: Session, foto_id: UUID, visible: bool) -> Optional[Foto]:
    """Marca una foto como visible/no visible para el cliente."""
    foto = obtener_foto(db, foto_id)
    if not foto:
        return None

    foto.visible_cliente = visible
    db.commit()
    db.refresh(foto)
    return foto


def obtener_ultimas_fotos(db: Session, limit: int = 10) -> List[Foto]:
    """Obtiene las últimas fotos subidas."""
    return db.query(Foto).filter(
        Foto.activo == True
    ).order_by(Foto.created_at.desc()).limit(limit).all()
