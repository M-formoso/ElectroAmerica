from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.schemas.material import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    AsignacionMaterialCreate, AsignacionMaterialResponse,
    IngresoStockCreate, MovimientoStockResponse,
    ValorInventarioResponse
)
from app.services import material_service

router = APIRouter()


@router.get("/", response_model=List[MaterialResponse])
def listar_materiales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista materiales."""
    return material_service.obtener_materiales(db, skip, limit)


@router.get("/stock-bajo", response_model=List[MaterialResponse])
def listar_materiales_stock_bajo(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista materiales con stock bajo (igual o menor al mínimo)."""
    return material_service.obtener_materiales(db, solo_stock_bajo=True)


@router.get("/ubicaciones")
def listar_ubicaciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista las ubicaciones únicas de materiales."""
    return {"ubicaciones": material_service.obtener_ubicaciones(db)}


@router.get("/valor-total", response_model=ValorInventarioResponse)
def obtener_valor_inventario(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene el valor total del inventario (solo admin/supervisor)."""
    return material_service.obtener_valor_total_inventario(db)


@router.post("/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def crear_material(
    material: MaterialCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Crea un nuevo material (solo admin/supervisor)."""
    return material_service.crear_material(db, material)


@router.get("/{material_id}", response_model=MaterialResponse)
def obtener_material(
    material_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene un material por ID."""
    material = material_service.obtener_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return material


@router.put("/{material_id}", response_model=MaterialResponse)
def actualizar_material(
    material_id: UUID,
    material: MaterialUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza un material (solo admin/supervisor)."""
    db_material = material_service.actualizar_material(db, material_id, material)
    if not db_material:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return db_material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_material(
    material_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina un material (soft delete, solo admin/supervisor)."""
    if not material_service.eliminar_material(db, material_id):
        raise HTTPException(status_code=404, detail="Material no encontrado")


@router.get("/{material_id}/movimientos", response_model=List[MovimientoStockResponse])
def listar_movimientos(
    material_id: UUID,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista el historial de movimientos de un material."""
    return material_service.obtener_movimientos_material(db, material_id, limit)


@router.post("/asignar", response_model=AsignacionMaterialResponse, status_code=status.HTTP_201_CREATED)
def asignar_material(
    asignacion: AsignacionMaterialCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Asigna material a un proyecto (descuenta del stock)."""
    db_asignacion = material_service.asignar_material_a_proyecto(db, asignacion, usuario.id)

    return AsignacionMaterialResponse(
        id=db_asignacion.id,
        material_id=db_asignacion.material_id,
        proyecto_id=db_asignacion.proyecto_id,
        etapa_id=db_asignacion.etapa_id,
        cantidad=db_asignacion.cantidad,
        precio_unitario=db_asignacion.material.precio_unitario if db_asignacion.material else None,
        fecha=db_asignacion.fecha_asignacion,
        observaciones=db_asignacion.notas,
        material_nombre=db_asignacion.material.nombre if db_asignacion.material else None,
        created_at=db_asignacion.created_at
    )


@router.post("/ingreso", response_model=MovimientoStockResponse, status_code=status.HTTP_201_CREATED)
def registrar_ingreso(
    ingreso: IngresoStockCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Registra un ingreso de stock (compra) - solo admin/supervisor."""
    return material_service.registrar_ingreso_stock(db, ingreso, usuario.id)
