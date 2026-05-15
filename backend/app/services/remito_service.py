"""Servicio de remitos: salida de materiales con descuento de stock."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.remito import Remito, RemitoItem
from app.models.deposito import Deposito, DepositoMaterial
from app.models.material import Material
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.schemas.remito import RemitoCreate


def _get_or_create_deposito_material(
    db: Session, deposito_id: UUID, material_id: UUID
) -> DepositoMaterial:
    """Devuelve el DepositoMaterial. Si no existe lo crea con stock 0
    (para permitir descontar y dejarlo en negativo cuando hace falta)."""
    dm = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == deposito_id,
        DepositoMaterial.material_id == material_id,
        DepositoMaterial.activo == True,
    ).first()
    if dm:
        return dm
    dm = DepositoMaterial(
        deposito_id=deposito_id,
        material_id=material_id,
        stock_actual=Decimal("0"),
        stock_minimo=Decimal("0"),
    )
    db.add(dm)
    db.flush()
    return dm


def crear_remito(
    db: Session,
    data: RemitoCreate,
    usuario_id: Optional[UUID],
) -> Remito:
    """Crea un remito y descuenta del stock del deposito indicado.

    No bloquea por stock insuficiente: el stock puede quedar negativo.
    Si el deposito es subdeposito, el padre baja en consecuencia porque
    su consolidado suma los hijos.
    """
    deposito = db.query(Deposito).filter(
        Deposito.id == data.deposito_id,
        Deposito.activo == True,
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    if not data.items:
        raise HTTPException(status_code=400, detail="El remito necesita al menos un item")

    remito = Remito(
        fecha=data.fecha,
        deposito_id=data.deposito_id,
        proyecto_id=data.proyecto_id,
        destinatario_texto=data.destinatario_texto,
        responsable_retira=data.responsable_retira,
        direccion_entrega=data.direccion_entrega,
        transportista=data.transportista,
        observaciones=data.observaciones,
        usuario_id=usuario_id,
    )
    db.add(remito)
    db.flush()

    for item_data in data.items:
        if item_data.cantidad <= 0:
            continue
        material = db.query(Material).filter(Material.id == item_data.material_id).first()
        if not material:
            raise HTTPException(
                status_code=404,
                detail=f"Material {item_data.material_id} no encontrado",
            )

        # Snapshot del material en el item
        db.add(RemitoItem(
            remito_id=remito.id,
            material_id=material.id,
            material_codigo=material.codigo,
            material_nombre=material.nombre,
            material_unidad=material.unidad,
            cantidad=item_data.cantidad,
        ))

        # Descontar stock del deposito (queda negativo si no alcanza)
        dm = _get_or_create_deposito_material(db, deposito.id, material.id)
        stock_anterior = dm.stock_actual
        dm.stock_actual = stock_anterior - item_data.cantidad

        # Trazabilidad: movimiento de salida
        db.add(MovimientoStock(
            material_id=material.id,
            tipo=TipoMovimiento.salida,
            cantidad=item_data.cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_anterior - item_data.cantidad,
            motivo=f"Salida por remito (deposito {deposito.nombre})",
            proyecto_id=data.proyecto_id,
            usuario_id=usuario_id,
        ))

    db.commit()
    db.refresh(remito)
    return remito


def obtener_remito(db: Session, remito_id: UUID) -> Optional[Remito]:
    return db.query(Remito).filter(
        Remito.id == remito_id,
        Remito.activo == True,
    ).first()


def listar_remitos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    deposito_id: Optional[UUID] = None,
    proyecto_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    busqueda: Optional[str] = None,
) -> List[Remito]:
    query = db.query(Remito).filter(Remito.activo == True)

    if deposito_id:
        query = query.filter(Remito.deposito_id == deposito_id)
    if proyecto_id:
        query = query.filter(Remito.proyecto_id == proyecto_id)
    if fecha_desde:
        query = query.filter(Remito.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Remito.fecha <= fecha_hasta)
    if busqueda:
        like = f"%{busqueda.strip()}%"
        # Buscar por destinatario o responsable
        query = query.filter(
            (Remito.destinatario_texto.ilike(like))
            | (Remito.responsable_retira.ilike(like))
        )

    return (
        query.order_by(Remito.numero.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def to_response_dict(remito: Remito) -> dict:
    """Helper para construir el dict de RemitoResponse con campos derivados."""
    return {
        "id": remito.id,
        "numero": remito.numero,
        "numero_formateado": remito.numero_formateado,
        "fecha": remito.fecha,
        "deposito_id": remito.deposito_id,
        "deposito_nombre": remito.deposito.nombre if remito.deposito else None,
        "proyecto_id": remito.proyecto_id,
        "proyecto_nombre": remito.proyecto.nombre if remito.proyecto else None,
        "destinatario_texto": remito.destinatario_texto,
        "responsable_retira": remito.responsable_retira,
        "direccion_entrega": remito.direccion_entrega,
        "transportista": remito.transportista,
        "observaciones": remito.observaciones,
        "usuario_id": remito.usuario_id,
        "usuario_nombre": remito.usuario.nombre if remito.usuario else None,
        "items": [
            {
                "id": it.id,
                "material_id": it.material_id,
                "material_codigo": it.material_codigo,
                "material_nombre": it.material_nombre,
                "material_unidad": it.material_unidad,
                "cantidad": it.cantidad,
            }
            for it in remito.items
        ],
        "created_at": remito.created_at,
    }


def to_list_dict(remito: Remito) -> dict:
    return {
        "id": remito.id,
        "numero": remito.numero,
        "numero_formateado": remito.numero_formateado,
        "fecha": remito.fecha,
        "deposito_id": remito.deposito_id,
        "deposito_nombre": remito.deposito.nombre if remito.deposito else None,
        "proyecto_id": remito.proyecto_id,
        "proyecto_nombre": remito.proyecto.nombre if remito.proyecto else None,
        "destinatario_texto": remito.destinatario_texto,
        "usuario_nombre": remito.usuario.nombre if remito.usuario else None,
        "cantidad_items": len(remito.items),
        "created_at": remito.created_at,
    }
