from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.deps import get_db, get_usuario_actual, require_staff
from app.models.usuario import Usuario
from app.schemas.foto import FotoCreate, FotoUpdate, FotoResponse
from app.services import foto_service, proyecto_service

router = APIRouter()


@router.get("/", response_model=List[FotoResponse])
def listar_fotos(
    proyecto_id: Optional[UUID] = None,
    etapa_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista fotos con filtros opcionales."""
    return foto_service.obtener_fotos(db, proyecto_id, etapa_id, skip=skip, limit=limit)


@router.get("/ultimas", response_model=List[FotoResponse])
def ultimas_fotos(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene las últimas fotos subidas."""
    return foto_service.obtener_ultimas_fotos(db, limit)


@router.post("/", response_model=FotoResponse, status_code=status.HTTP_201_CREATED)
def crear_foto(
    foto: FotoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Crea una nueva foto (después de subir a Cloudinary)."""
    # Verificar que el proyecto existe
    proyecto = proyecto_service.obtener_proyecto(db, foto.proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return foto_service.crear_foto(db, foto, usuario.id)


@router.get("/{foto_id}", response_model=FotoResponse)
def obtener_foto(
    foto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene una foto por ID."""
    foto = foto_service.obtener_foto(db, foto_id)
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return foto


@router.put("/{foto_id}", response_model=FotoResponse)
def actualizar_foto(
    foto_id: UUID,
    foto: FotoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Actualiza una foto (descripción, visibilidad)."""
    db_foto = foto_service.actualizar_foto(db, foto_id, foto)
    if not db_foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return db_foto


@router.delete("/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_foto(
    foto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Elimina una foto (soft delete)."""
    if not foto_service.eliminar_foto(db, foto_id):
        raise HTTPException(status_code=404, detail="Foto no encontrada")


@router.put("/{foto_id}/visibilidad")
def cambiar_visibilidad(
    foto_id: UUID,
    visible: bool,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Cambia la visibilidad de una foto para el cliente."""
    foto = foto_service.marcar_visible_cliente(db, foto_id, visible)
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")

    return {
        "foto_id": str(foto.id),
        "visible_cliente": foto.visible_cliente
    }
