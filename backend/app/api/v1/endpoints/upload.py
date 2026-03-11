from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date
from app.core.deps import get_db, get_usuario_actual, require_staff
from app.models.usuario import Usuario
from app.models.foto import Foto
from app.services import cloudinary_service, proyecto_service

router = APIRouter()


@router.post("/imagen")
async def subir_imagen(
    file: UploadFile = File(...),
    folder: str = Form(default="general"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """
    Sube una imagen a Cloudinary.

    Folders disponibles:
    - proyectos: Fotos de proyectos
    - materiales: Fotos de materiales
    - equipos: Fotos de equipos
    - usuarios: Avatares de usuarios
    - comprobantes: Comprobantes de gastos
    - general: Otros
    """
    result = await cloudinary_service.upload_image(file, folder)
    return result


@router.post("/foto-proyecto")
async def subir_foto_proyecto(
    file: UploadFile = File(...),
    proyecto_id: UUID = Form(...),
    etapa_id: Optional[UUID] = Form(None),
    descripcion: Optional[str] = Form(None),
    visible_cliente: bool = Form(False),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """
    Sube una foto y la asocia a un proyecto/etapa.
    Crea el registro en la base de datos automáticamente.
    """
    # Verificar que el proyecto existe
    proyecto = proyecto_service.obtener_proyecto(db, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Subir imagen
    result = await cloudinary_service.upload_image(file, "proyectos")

    # Crear registro en BD
    db_foto = Foto(
        proyecto_id=proyecto_id,
        etapa_id=etapa_id,
        url=result["url"],
        thumbnail_url=result["thumbnail_url"],
        descripcion=descripcion,
        fecha=date.today(),
        visible_cliente=visible_cliente,
        subido_por_id=usuario.id
    )
    db.add(db_foto)
    db.commit()
    db.refresh(db_foto)

    return {
        "id": str(db_foto.id),
        "url": db_foto.url,
        "thumbnail_url": db_foto.thumbnail_url,
        "proyecto_id": str(db_foto.proyecto_id),
        "etapa_id": str(db_foto.etapa_id) if db_foto.etapa_id else None,
        "descripcion": db_foto.descripcion,
        "fecha": db_foto.fecha.isoformat(),
        "visible_cliente": db_foto.visible_cliente,
        "public_id": result["public_id"]
    }


@router.delete("/imagen/{public_id:path}")
async def eliminar_imagen(
    public_id: str,
    usuario: Usuario = Depends(require_staff)
):
    """Elimina una imagen de Cloudinary por su public_id."""
    success = await cloudinary_service.delete_image(public_id)
    if not success:
        raise HTTPException(status_code=500, detail="Error al eliminar imagen")
    return {"message": "Imagen eliminada correctamente"}
