from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.herramienta import Herramienta, PrestamoHerramienta, EstadoHerramienta, EstadoPrestamo
from app.schemas.herramienta import (
    HerramientaCreate, HerramientaUpdate, HerramientaResponse, HerramientaConPrestamoResponse,
    PrestamoCreate, PrestamoDevolucion, PrestamoUpdate, PrestamoResponse
)
from app.services import cloudinary_service

router = APIRouter()


# ============ Herramientas CRUD ============

@router.get("/", response_model=List[HerramientaConPrestamoResponse])
def listar_herramientas(
    estado: Optional[EstadoHerramienta] = None,
    estado_prestamo: Optional[EstadoPrestamo] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=200),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista herramientas con filtros opcionales."""
    query = db.query(Herramienta).filter(Herramienta.activo == True)

    if estado:
        query = query.filter(Herramienta.estado == estado)
    if estado_prestamo:
        query = query.filter(Herramienta.estado_prestamo == estado_prestamo)

    herramientas = query.order_by(Herramienta.nombre).offset(skip).limit(limit).all()

    result = []
    for h in herramientas:
        prestamo_activo = h.prestamo_activo
        result.append(HerramientaConPrestamoResponse(
            id=h.id,
            nombre=h.nombre,
            descripcion=h.descripcion,
            estado=h.estado,
            estado_prestamo=h.estado_prestamo,
            activo=h.activo,
            created_at=h.created_at,
            foto_url=h.foto_url,
            foto_public_id=h.foto_public_id,
            retirado_por=prestamo_activo.retirado_por if prestamo_activo else None,
            fecha_retiro=prestamo_activo.fecha_retiro if prestamo_activo else None
        ))

    return result


@router.post("/", response_model=HerramientaResponse, status_code=status.HTTP_201_CREATED)
def crear_herramienta(
    herramienta: HerramientaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Crea una nueva herramienta (solo admin/supervisor)."""
    db_herramienta = Herramienta(
        nombre=herramienta.nombre,
        descripcion=herramienta.descripcion,
        estado=herramienta.estado,
        estado_prestamo=EstadoPrestamo.disponible
    )
    db.add(db_herramienta)
    db.commit()
    db.refresh(db_herramienta)
    return db_herramienta


@router.get("/{herramienta_id}", response_model=HerramientaConPrestamoResponse)
def obtener_herramienta(
    herramienta_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene una herramienta por ID."""
    herramienta = db.query(Herramienta).filter(
        Herramienta.id == herramienta_id,
        Herramienta.activo == True
    ).first()

    if not herramienta:
        raise HTTPException(status_code=404, detail="Herramienta no encontrada")

    prestamo_activo = herramienta.prestamo_activo
    return HerramientaConPrestamoResponse(
        id=herramienta.id,
        nombre=herramienta.nombre,
        descripcion=herramienta.descripcion,
        estado=herramienta.estado,
        estado_prestamo=herramienta.estado_prestamo,
        activo=herramienta.activo,
        created_at=herramienta.created_at,
        foto_url=herramienta.foto_url,
        foto_public_id=herramienta.foto_public_id,
        retirado_por=prestamo_activo.retirado_por if prestamo_activo else None,
        fecha_retiro=prestamo_activo.fecha_retiro if prestamo_activo else None
    )


@router.put("/{herramienta_id}", response_model=HerramientaResponse)
def actualizar_herramienta(
    herramienta_id: UUID,
    herramienta: HerramientaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza una herramienta (solo admin/supervisor)."""
    db_herramienta = db.query(Herramienta).filter(
        Herramienta.id == herramienta_id,
        Herramienta.activo == True
    ).first()

    if not db_herramienta:
        raise HTTPException(status_code=404, detail="Herramienta no encontrada")

    update_data = herramienta.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_herramienta, field, value)

    db.commit()
    db.refresh(db_herramienta)
    return db_herramienta


@router.delete("/{herramienta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_herramienta(
    herramienta_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina una herramienta (soft delete, solo admin/supervisor)."""
    db_herramienta = db.query(Herramienta).filter(
        Herramienta.id == herramienta_id,
        Herramienta.activo == True
    ).first()

    if not db_herramienta:
        raise HTTPException(status_code=404, detail="Herramienta no encontrada")

    if db_herramienta.estado_prestamo == EstadoPrestamo.en_uso:
        raise HTTPException(status_code=400, detail="No se puede eliminar una herramienta en uso")

    db_herramienta.activo = False
    db.commit()


@router.post("/{herramienta_id}/foto", response_model=HerramientaResponse)
async def subir_foto_herramienta(
    herramienta_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Sube o reemplaza la foto de una herramienta."""
    db_herramienta = db.query(Herramienta).filter(
        Herramienta.id == herramienta_id,
        Herramienta.activo == True
    ).first()
    if not db_herramienta:
        raise HTTPException(status_code=404, detail="Herramienta no encontrada")

    foto_anterior = db_herramienta.foto_public_id

    result = await cloudinary_service.upload_image(file, folder="herramientas")

    db_herramienta.foto_url = result["url"]
    db_herramienta.foto_public_id = result["public_id"]
    db.commit()
    db.refresh(db_herramienta)

    if foto_anterior and foto_anterior != result["public_id"]:
        try:
            await cloudinary_service.delete_image(foto_anterior)
        except Exception:
            pass

    return db_herramienta


@router.delete("/{herramienta_id}/foto", response_model=HerramientaResponse)
async def quitar_foto_herramienta(
    herramienta_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Quita la foto de una herramienta."""
    db_herramienta = db.query(Herramienta).filter(
        Herramienta.id == herramienta_id,
        Herramienta.activo == True
    ).first()
    if not db_herramienta:
        raise HTTPException(status_code=404, detail="Herramienta no encontrada")

    public_id = db_herramienta.foto_public_id
    db_herramienta.foto_url = None
    db_herramienta.foto_public_id = None
    db.commit()
    db.refresh(db_herramienta)

    if public_id:
        try:
            await cloudinary_service.delete_image(public_id)
        except Exception:
            pass

    return db_herramienta


# ============ Préstamos ============

@router.post("/prestamos", response_model=PrestamoResponse, status_code=status.HTTP_201_CREATED)
def registrar_prestamo(
    prestamo: PrestamoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Registra un nuevo préstamo de herramienta."""
    herramienta = db.query(Herramienta).filter(
        Herramienta.id == prestamo.herramienta_id,
        Herramienta.activo == True
    ).first()

    if not herramienta:
        raise HTTPException(status_code=404, detail="Herramienta no encontrada")

    if herramienta.estado_prestamo == EstadoPrestamo.en_uso:
        raise HTTPException(status_code=400, detail="La herramienta ya está en uso")

    if herramienta.estado == EstadoHerramienta.rota:
        raise HTTPException(status_code=400, detail="No se puede prestar una herramienta rota")

    db_prestamo = PrestamoHerramienta(
        herramienta_id=prestamo.herramienta_id,
        retirado_por=prestamo.retirado_por,
        fecha_retiro=prestamo.fecha_retiro,
        registrado_por_id=usuario.id
    )

    herramienta.estado_prestamo = EstadoPrestamo.en_uso

    db.add(db_prestamo)
    db.commit()
    db.refresh(db_prestamo)
    return db_prestamo


@router.post("/prestamos/{prestamo_id}/devolver", response_model=PrestamoResponse)
def registrar_devolucion(
    prestamo_id: UUID,
    devolucion: PrestamoDevolucion,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Registra la devolución de una herramienta."""
    prestamo = db.query(PrestamoHerramienta).filter(
        PrestamoHerramienta.id == prestamo_id,
        PrestamoHerramienta.activo == True
    ).first()

    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")

    if prestamo.fecha_devolucion:
        raise HTTPException(status_code=400, detail="Este préstamo ya fue devuelto")

    prestamo.fecha_devolucion = devolucion.fecha_devolucion
    prestamo.notas_devolucion = devolucion.notas_devolucion

    # Actualizar estado de la herramienta
    prestamo.herramienta.estado_prestamo = EstadoPrestamo.disponible

    db.commit()
    db.refresh(prestamo)
    return prestamo


@router.get("/{herramienta_id}/historial", response_model=List[PrestamoResponse])
def obtener_historial_prestamos(
    herramienta_id: UUID,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene el historial de préstamos de una herramienta."""
    herramienta = db.query(Herramienta).filter(
        Herramienta.id == herramienta_id,
        Herramienta.activo == True
    ).first()

    if not herramienta:
        raise HTTPException(status_code=404, detail="Herramienta no encontrada")

    prestamos = db.query(PrestamoHerramienta).filter(
        PrestamoHerramienta.herramienta_id == herramienta_id,
        PrestamoHerramienta.activo == True
    ).order_by(PrestamoHerramienta.fecha_retiro.desc()).limit(limit).all()

    return prestamos


@router.put("/prestamos/{prestamo_id}", response_model=PrestamoResponse)
def actualizar_prestamo(
    prestamo_id: UUID,
    prestamo_update: PrestamoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza un préstamo (solo admin/supervisor)."""
    prestamo = db.query(PrestamoHerramienta).filter(
        PrestamoHerramienta.id == prestamo_id,
        PrestamoHerramienta.activo == True
    ).first()

    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")

    update_data = prestamo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prestamo, field, value)

    db.commit()
    db.refresh(prestamo)
    return prestamo


@router.delete("/prestamos/{prestamo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_prestamo(
    prestamo_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina un préstamo (soft delete, solo admin/supervisor)."""
    prestamo = db.query(PrestamoHerramienta).filter(
        PrestamoHerramienta.id == prestamo_id,
        PrestamoHerramienta.activo == True
    ).first()

    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")

    # Si era el préstamo activo, liberar la herramienta
    if not prestamo.fecha_devolucion:
        prestamo.herramienta.estado_prestamo = EstadoPrestamo.disponible

    prestamo.activo = False
    db.commit()
