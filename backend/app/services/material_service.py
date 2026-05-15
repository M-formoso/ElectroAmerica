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
from app.models.deposito import Deposito, DepositoMaterial
from app.schemas.material import (
    MaterialCreate, MaterialUpdate,
    AsignacionMaterialCreate, IngresoStockCreate,
    TransferenciaADepositoCreate
)


def obtener_materiales(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_stock_bajo: bool = False,
    busqueda: Optional[str] = None,
) -> List[Material]:
    """Obtiene lista de materiales.

    Si `busqueda` esta presente, filtra por nombre o codigo (case-insensitive).
    """
    query = db.query(Material).filter(Material.activo == True)

    if solo_stock_bajo:
        query = query.filter(Material.stock_actual <= Material.stock_minimo)

    if busqueda:
        like = f"%{busqueda.strip()}%"
        query = query.filter(
            (Material.nombre.ilike(like)) | (Material.codigo.ilike(like))
        )

    return query.order_by(Material.nombre).offset(skip).limit(limit).all()


def obtener_material(db: Session, material_id: UUID) -> Optional[Material]:
    """Obtiene un material por ID."""
    return db.query(Material).filter(
        Material.id == material_id,
        Material.activo == True
    ).first()


def crear_material(
    db: Session,
    material: MaterialCreate,
    usuario_id: Optional[UUID] = None,
) -> Material:
    """Crea un nuevo material y, opcionalmente, distribuye stock inicial
    a depositos/subdepositos."""
    db_material = Material(
        codigo=material.codigo,
        nombre=material.nombre,
        descripcion=material.descripcion,
        unidad=material.unidad,
        stock_actual=material.stock_actual,
        stock_minimo=material.stock_minimo,
        precio_unitario=material.precio_unitario,
        ubicacion_almacen=material.ubicacion_almacen
    )
    db.add(db_material)
    db.flush()  # Para obtener el ID

    # Si vienen destinos iniciales, crear el stock en cada deposito.
    # Estos stocks son ADICIONALES al stock global (no se descuentan).
    if material.destinos_iniciales:
        for destino in material.destinos_iniciales:
            deposito = db.query(Deposito).filter(Deposito.id == destino.deposito_id).first()
            if not deposito:
                raise HTTPException(
                    status_code=404,
                    detail=f"Deposito {destino.deposito_id} no encontrado",
                )
            db.add(DepositoMaterial(
                deposito_id=destino.deposito_id,
                material_id=db_material.id,
                stock_actual=destino.cantidad,
                stock_minimo=0,
            ))
            # Trazabilidad: registrar como entrada con destino al deposito.
            if usuario_id:
                db.add(MovimientoStock(
                    material_id=db_material.id,
                    tipo=TipoMovimiento.entrada,
                    cantidad=destino.cantidad,
                    stock_anterior=Decimal(0),
                    stock_nuevo=destino.cantidad,
                    motivo="Carga inicial a deposito",
                    deposito_destino_id=destino.deposito_id,
                    usuario_id=usuario_id,
                ))

    db.commit()
    db.refresh(db_material)
    return db_material


def transferir_a_deposito(
    db: Session,
    material_id: UUID,
    transferencia: TransferenciaADepositoCreate,
    usuario_id: UUID,
) -> MovimientoStock:
    """Transfiere stock del global al deposito/subdeposito indicado.

    Resta del stock_actual del Material y suma al DepositoMaterial
    correspondiente (crea la relacion si no existe). Registra un
    MovimientoStock de tipo transferencia_a_deposito para trazabilidad.
    """
    material = obtener_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    if material.stock_actual < transferencia.cantidad:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Stock global insuficiente. Disponible: "
                f"{material.stock_actual} {material.unidad}"
            ),
        )

    deposito = db.query(Deposito).filter(Deposito.id == transferencia.deposito_id).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    # Buscar/crear la fila de stock en el deposito.
    deposito_material = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == transferencia.deposito_id,
        DepositoMaterial.material_id == material_id,
    ).first()

    if deposito_material is None:
        deposito_material = DepositoMaterial(
            deposito_id=transferencia.deposito_id,
            material_id=material_id,
            stock_actual=Decimal(0),
            stock_minimo=Decimal(0),
        )
        db.add(deposito_material)

    # Aplicar el movimiento.
    stock_anterior = material.stock_actual
    material.stock_actual = stock_anterior - transferencia.cantidad
    deposito_material.stock_actual = (
        Decimal(deposito_material.stock_actual or 0) + transferencia.cantidad
    )

    movimiento = MovimientoStock(
        material_id=material_id,
        tipo=TipoMovimiento.transferencia_a_deposito,
        cantidad=transferencia.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=material.stock_actual,
        motivo=transferencia.motivo or f"Transferencia a {deposito.nombre}",
        deposito_destino_id=transferencia.deposito_id,
        usuario_id=usuario_id,
    )
    db.add(movimiento)

    db.commit()
    db.refresh(movimiento)
    return movimiento


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
        fecha_asignacion=date.today(),
        notas=asignacion.observaciones,
        asignado_por_id=usuario_id
    )
    db.add(db_asignacion)
    db.flush()  # Para obtener el ID

    # Registrar stock anterior y descontar
    stock_anterior = material.stock_actual
    material.stock_actual -= asignacion.cantidad

    # Registrar movimiento
    movimiento = MovimientoStock(
        material_id=asignacion.material_id,
        tipo=TipoMovimiento.salida,
        cantidad=asignacion.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=material.stock_actual,
        motivo=f"Asignado a proyecto",
        proyecto_id=asignacion.proyecto_id,
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

    # Registrar stock anterior y actualizar stock
    stock_anterior = material.stock_actual
    material.stock_actual += ingreso.cantidad

    # Si viene precio, actualizar precio unitario
    if ingreso.precio_unitario:
        material.precio_unitario = ingreso.precio_unitario

    # Registrar movimiento
    movimiento = MovimientoStock(
        material_id=ingreso.material_id,
        tipo=TipoMovimiento.entrada,
        cantidad=ingreso.cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=material.stock_actual,
        motivo=ingreso.motivo,
        usuario_id=usuario_id
    )
    db.add(movimiento)

    db.commit()
    db.refresh(movimiento)
    return movimiento


def obtener_valor_total_inventario(db: Session) -> dict:
    """Calcula el valor total del inventario."""
    resultado = db.query(
        func.sum(Material.stock_actual * Material.precio_unitario),
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


def obtener_ubicaciones(db: Session) -> List[str]:
    """Obtiene las ubicaciones únicas de materiales."""
    result = db.query(Material.ubicacion_almacen).filter(
        Material.activo == True,
        Material.ubicacion_almacen.isnot(None)
    ).distinct().all()
    return [r[0] for r in result if r[0]]
