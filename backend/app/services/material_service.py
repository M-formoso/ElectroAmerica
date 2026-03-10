from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from fastapi import HTTPException
from app.models.material import Material
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.models.asignacion_material import AsignacionMaterial
from app.schemas.material import (
    MaterialCreate, MaterialUpdate,
    AsignacionMaterialCreate, IngresoStockCreate
)


def obtener_materiales(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    categoria: Optional[str] = None,
    solo_stock_bajo: bool = False
) -> List[Material]:
    """Obtiene lista de materiales."""
    query = db.query(Material).filter(Material.activo == True)

    if categoria:
        query = query.filter(Material.categoria == categoria)
    if solo_stock_bajo:
        query = query.filter(Material.stock_actual <= Material.stock_minimo)

    return query.order_by(Material.nombre).offset(skip).limit(limit).all()


def obtener_material(db: Session, material_id: UUID) -> Optional[Material]:
    """Obtiene un material por ID."""
    return db.query(Material).filter(
        Material.id == material_id,
        Material.activo == True
    ).first()


def crear_material(db: Session, material: MaterialCreate) -> Material:
    """Crea un nuevo material."""
    db_material = Material(
        nombre=material.nombre,
        codigo=material.codigo,
        categoria=material.categoria,
        unidad=material.unidad,
        stock_actual=material.stock_actual,
        stock_minimo=material.stock_minimo,
        precio_costo=material.precio_costo,
        proveedor=material.proveedor
    )
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


def actualizar_material(
    db: Session,
    material_id: UUID,
    material: MaterialUpdate
) -> Optional[Material]:
    """Actualiza un material existente."""
    db_material = obtener_material(db, material_id)
    if not db_material:
        return None

    update_data = material.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_material, field, value)

    db.commit()
    db.refresh(db_material)
    return db_material


def eliminar_material(db: Session, material_id: UUID) -> bool:
    """Soft delete de material."""
    material = obtener_material(db, material_id)
    if not material:
        return False

    material.activo = False
    db.commit()
    return True


def asignar_material_a_proyecto(
    db: Session,
    asignacion: AsignacionMaterialCreate,
    usuario_id: UUID
) -> AsignacionMaterial:
    """Asigna material a un proyecto, descuenta del stock y registra movimiento."""
    material = obtener_material(db, asignacion.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    if material.stock_actual < asignacion.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponible: {material.stock_actual} {material.unidad}"
        )

    # Crear asignación
    db_asignacion = AsignacionMaterial(
        material_id=asignacion.material_id,
        proyecto_id=asignacion.proyecto_id,
        etapa_id=asignacion.etapa_id,
        cantidad=asignacion.cantidad,
        precio_unitario=material.precio_costo,
        fecha=date.today(),
        observaciones=asignacion.observaciones,
        created_by=usuario_id
    )
    db.add(db_asignacion)
    db.flush()  # Para obtener el ID

    # Descontar stock
    material.stock_actual -= asignacion.cantidad

    # Registrar movimiento
    movimiento = MovimientoStock(
        material_id=asignacion.material_id,
        tipo=TipoMovimiento.egreso,
        cantidad=asignacion.cantidad,
        referencia_tipo="asignacion",
        referencia_id=db_asignacion.id,
        observaciones=f"Asignado a proyecto",
        usuario_id=usuario_id
    )
    db.add(movimiento)

    db.commit()
    db.refresh(db_asignacion)

    return db_asignacion


def registrar_ingreso_stock(
    db: Session,
    ingreso: IngresoStockCreate,
    usuario_id: UUID
) -> MovimientoStock:
    """Registra una compra/ingreso de material al stock."""
    material = obtener_material(db, ingreso.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    # Actualizar stock
    material.stock_actual += ingreso.cantidad

    # Si viene precio, actualizar precio costo
    if ingreso.precio_unitario:
        material.precio_costo = ingreso.precio_unitario

    if ingreso.proveedor:
        material.proveedor = ingreso.proveedor

    # Registrar movimiento
    movimiento = MovimientoStock(
        material_id=ingreso.material_id,
        tipo=TipoMovimiento.ingreso,
        cantidad=ingreso.cantidad,
        referencia_tipo="compra",
        observaciones=ingreso.observaciones,
        usuario_id=usuario_id
    )
    db.add(movimiento)

    db.commit()
    db.refresh(movimiento)
    return movimiento


def obtener_valor_total_inventario(db: Session) -> dict:
    """Calcula el valor total del inventario."""
    resultado = db.query(
        func.sum(Material.stock_actual * Material.precio_costo),
        func.count(Material.id)
    ).filter(Material.activo == True).first()

    items_bajo = db.query(Material).filter(
        Material.activo == True,
        Material.stock_actual <= Material.stock_minimo
    ).count()

    return {
        "valor_total": Decimal(resultado[0] or 0),
        "total_items": resultado[1] or 0,
        "items_stock_bajo": items_bajo
    }


def obtener_movimientos_material(
    db: Session,
    material_id: UUID,
    limit: int = 50
) -> List[MovimientoStock]:
    """Obtiene el historial de movimientos de un material."""
    return db.query(MovimientoStock).filter(
        MovimientoStock.material_id == material_id
    ).order_by(MovimientoStock.created_at.desc()).limit(limit).all()


def obtener_categorias(db: Session) -> List[str]:
    """Obtiene las categorías únicas de materiales."""
    result = db.query(Material.categoria).filter(
        Material.activo == True,
        Material.categoria.isnot(None)
    ).distinct().all()
    return [r[0] for r in result if r[0]]
