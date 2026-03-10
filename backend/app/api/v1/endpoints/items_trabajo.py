from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario, RolUsuario
from app.models.item_trabajo import EstadoItem
from app.schemas.item_trabajo import ItemTrabajoCreate, ItemTrabajoUpdate, ItemTrabajoResponse
from app.services import item_trabajo_service, etapa_service

router = APIRouter()


@router.get("/", response_model=List[ItemTrabajoResponse])
def listar_items(
    etapa_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista ítems de trabajo, opcionalmente filtrados por etapa."""
    items = item_trabajo_service.obtener_items(db, etapa_id, skip, limit)

    # Ocultar precio_unitario si no es admin/supervisor
    if usuario.rol not in [RolUsuario.administrador, RolUsuario.supervisor]:
        for item in items:
            item.precio_unitario = None

    return items


@router.post("/", response_model=ItemTrabajoResponse, status_code=status.HTTP_201_CREATED)
def crear_item(
    item: ItemTrabajoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Crea un nuevo ítem de trabajo."""
    # Verificar que la etapa existe
    etapa = etapa_service.obtener_etapa(db, item.etapa_id)
    if not etapa:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")

    # Solo admin/supervisor pueden establecer precio
    if usuario.rol not in [RolUsuario.administrador, RolUsuario.supervisor]:
        item.precio_unitario = None

    return item_trabajo_service.crear_item(db, item)


@router.get("/{item_id}", response_model=ItemTrabajoResponse)
def obtener_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene un ítem de trabajo por ID."""
    item = item_trabajo_service.obtener_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    # Ocultar precio si no es admin/supervisor
    if usuario.rol not in [RolUsuario.administrador, RolUsuario.supervisor]:
        item.precio_unitario = None

    return item


@router.put("/{item_id}", response_model=ItemTrabajoResponse)
def actualizar_item(
    item_id: UUID,
    item: ItemTrabajoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Actualiza un ítem de trabajo."""
    # Solo admin/supervisor pueden actualizar precio
    if usuario.rol not in [RolUsuario.administrador, RolUsuario.supervisor]:
        item.precio_unitario = None

    db_item = item_trabajo_service.actualizar_item(db, item_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Elimina un ítem de trabajo (soft delete)."""
    if not item_trabajo_service.eliminar_item(db, item_id):
        raise HTTPException(status_code=404, detail="Ítem no encontrado")


@router.post("/{item_id}/completar", response_model=ItemTrabajoResponse)
def marcar_completado(
    item_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Marca un ítem como completado."""
    item = item_trabajo_service.marcar_completado(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return item
