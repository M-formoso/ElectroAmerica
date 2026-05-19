"""Servicio de remitos: salida de materiales con descuento de stock."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.remito import Remito, RemitoItem, RemitoDescuento
from app.models.deposito import Deposito, DepositoMaterial
from app.models.material import Material
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.schemas.remito import RemitoCreate, RemitoUpdate, RemitoItemsUpdate, RemitoAnular


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


def _depositos_relacionados(db: Session, origen: Deposito) -> List[Deposito]:
    """Devuelve [origen, ...resto] donde 'resto' son los otros depositos
    del mismo grupo (padre + hermanos si origen es subdeposito, o hijos
    si origen es root). Sirve para que la salida pueda 'tomar' stock
    de otros lados del mismo grupo logico.
    """
    if origen.parent_id:
        padre = db.query(Deposito).filter(
            Deposito.id == origen.parent_id,
            Deposito.activo == True,
        ).first()
        hermanos = (
            db.query(Deposito)
            .filter(
                Deposito.parent_id == origen.parent_id,
                Deposito.id != origen.id,
                Deposito.activo == True,
            )
            .all()
        )
        resto = (hermanos + [padre]) if padre else hermanos
    else:
        hijos = (
            db.query(Deposito)
            .filter(Deposito.parent_id == origen.id, Deposito.activo == True)
            .all()
        )
        resto = hijos
    return [origen, *resto]


def _descontar_material_cascada(
    db: Session,
    remito_id: UUID,
    origen: Deposito,
    material: Material,
    cantidad: Decimal,
    motivo_prefix: str,
    proyecto_id: Optional[UUID],
    usuario_id: Optional[UUID],
) -> None:
    """Descuenta `cantidad` de `material` empezando por `origen` y
    siguiendo con los depositos del mismo grupo (padre+hermanos o hijos).
    Si despues de recorrerlos queda restante, lo descuenta del `origen`
    dejandolo en negativo. Cada descuento real se registra en
    `RemitoDescuento` para poder revertirlo despues.
    """
    restante = cantidad
    candidatos = _depositos_relacionados(db, origen)

    for dep in candidatos:
        if restante <= 0:
            break
        dm = db.query(DepositoMaterial).filter(
            DepositoMaterial.deposito_id == dep.id,
            DepositoMaterial.material_id == material.id,
            DepositoMaterial.activo == True,
        ).first()
        if not dm or dm.stock_actual <= 0:
            continue
        usar = dm.stock_actual if dm.stock_actual < restante else restante
        stock_anterior = dm.stock_actual
        dm.stock_actual = stock_anterior - usar
        restante = restante - usar
        db.add(MovimientoStock(
            material_id=material.id,
            tipo=TipoMovimiento.salida,
            cantidad=usar,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_anterior - usar,
            motivo=f"{motivo_prefix} (deposito {dep.nombre})",
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
        ))
        db.add(RemitoDescuento(
            remito_id=remito_id,
            deposito_id=dep.id,
            material_id=material.id,
            cantidad=usar,
        ))

    if restante > 0:
        dm_origen = _get_or_create_deposito_material(db, origen.id, material.id)
        stock_anterior = dm_origen.stock_actual
        dm_origen.stock_actual = stock_anterior - restante
        db.add(MovimientoStock(
            material_id=material.id,
            tipo=TipoMovimiento.salida,
            cantidad=restante,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_anterior - restante,
            motivo=f"{motivo_prefix} (deposito {origen.nombre}, sin stock)",
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
        ))
        db.add(RemitoDescuento(
            remito_id=remito_id,
            deposito_id=origen.id,
            material_id=material.id,
            cantidad=restante,
        ))


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
    # Asegurar que se haya leido el numero asignado por la sequence
    # antes de usarlo en los motivos de los MovimientoStock.
    db.refresh(remito)

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

        # Descontar en cascada: primero del origen, despues de hermanos/padre
        # (o hijos si origen es root). Si nada alcanza, deja el origen
        # en negativo. Cada descuento real genera un MovimientoStock y un
        # RemitoDescuento para poder revertirlo.
        _descontar_material_cascada(
            db,
            remito_id=remito.id,
            origen=deposito,
            material=material,
            cantidad=item_data.cantidad,
            motivo_prefix=f"Salida por remito {remito.numero_formateado}",
            proyecto_id=data.proyecto_id,
            usuario_id=usuario_id,
        )

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


def _deposito_path(remito: Remito) -> tuple[str | None, str | None, bool]:
    """Devuelve (nombre_propio, nombre_padre, es_subdeposito) del deposito.

    Cuando el remito sale de un subdeposito, queremos saber tambien el
    nombre del padre para dar contexto en la UI y en el PDF.
    """
    if not remito.deposito:
        return None, None, False
    propio = remito.deposito.nombre
    es_sub = remito.deposito.parent_id is not None
    padre_nombre = remito.deposito.parent.nombre if es_sub and remito.deposito.parent else None
    return propio, padre_nombre, es_sub


def to_response_dict(remito: Remito) -> dict:
    """Helper para construir el dict de RemitoResponse con campos derivados."""
    propio, padre, es_sub = _deposito_path(remito)
    return {
        "id": remito.id,
        "numero": remito.numero,
        "numero_formateado": remito.numero_formateado,
        "fecha": remito.fecha,
        "deposito_id": remito.deposito_id,
        "deposito_nombre": propio,
        "deposito_padre_nombre": padre,
        "es_subdeposito": es_sub,
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
        "anulado": remito.anulado_at is not None,
        "anulado_at": remito.anulado_at,
        "anulado_por_nombre": remito.anulado_por.nombre if remito.anulado_por else None,
        "motivo_anulacion": remito.motivo_anulacion,
        "editado": remito.editado_at is not None,
        "editado_at": remito.editado_at,
        "editado_por_nombre": remito.editado_por.nombre if remito.editado_por else None,
    }


def to_list_dict(remito: Remito) -> dict:
    propio, padre, es_sub = _deposito_path(remito)
    return {
        "id": remito.id,
        "numero": remito.numero,
        "numero_formateado": remito.numero_formateado,
        "fecha": remito.fecha,
        "deposito_id": remito.deposito_id,
        "deposito_nombre": propio,
        "deposito_padre_nombre": padre,
        "es_subdeposito": es_sub,
        "proyecto_id": remito.proyecto_id,
        "proyecto_nombre": remito.proyecto.nombre if remito.proyecto else None,
        "destinatario_texto": remito.destinatario_texto,
        "usuario_nombre": remito.usuario.nombre if remito.usuario else None,
        "cantidad_items": len(remito.items),
        "created_at": remito.created_at,
        "anulado": remito.anulado_at is not None,
        "editado": remito.editado_at is not None,
    }


# ============ Anulacion / Edicion ============

def _revertir_descuentos(db: Session, remito: Remito, usuario_id: Optional[UUID]) -> None:
    """Suma de vuelta a cada DepositoMaterial las cantidades descontadas
    por el remito, y registra un MovimientoStock tipo `devolucion` por
    cada uno. No borra los registros de RemitoDescuento (eso lo decide
    el caller segun corresponda anular o reaplicar).
    """
    if remito.descuentos:
        for desc in remito.descuentos:
            dm = db.query(DepositoMaterial).filter(
                DepositoMaterial.deposito_id == desc.deposito_id,
                DepositoMaterial.material_id == desc.material_id,
                DepositoMaterial.activo == True,
            ).first()
            if not dm:
                # Si el DepositoMaterial fue borrado, lo recreamos en 0
                dm = DepositoMaterial(
                    deposito_id=desc.deposito_id,
                    material_id=desc.material_id,
                    stock_actual=Decimal("0"),
                    stock_minimo=Decimal("0"),
                )
                db.add(dm)
                db.flush()
            stock_anterior = dm.stock_actual
            dm.stock_actual = stock_anterior + desc.cantidad
            db.add(MovimientoStock(
                material_id=desc.material_id,
                tipo=TipoMovimiento.devolucion,
                cantidad=desc.cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_anterior + desc.cantidad,
                motivo=f"Reversion de remito {remito.numero_formateado}",
                proyecto_id=remito.proyecto_id,
                usuario_id=usuario_id,
            ))
    else:
        # Fallback para remitos creados antes de tener RemitoDescuento:
        # asumimos que todo se descontó del deposito de origen.
        for item in remito.items:
            if not item.material_id or item.cantidad <= 0:
                continue
            dm = db.query(DepositoMaterial).filter(
                DepositoMaterial.deposito_id == remito.deposito_id,
                DepositoMaterial.material_id == item.material_id,
                DepositoMaterial.activo == True,
            ).first()
            if not dm:
                continue
            stock_anterior = dm.stock_actual
            dm.stock_actual = stock_anterior + item.cantidad
            db.add(MovimientoStock(
                material_id=item.material_id,
                tipo=TipoMovimiento.devolucion,
                cantidad=item.cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_anterior + item.cantidad,
                motivo=f"Reversion de remito {remito.numero_formateado} (fallback origen)",
                proyecto_id=remito.proyecto_id,
                usuario_id=usuario_id,
            ))


def anular_remito(
    db: Session,
    remito_id: UUID,
    data: "RemitoAnular",
    usuario_id: Optional[UUID],
) -> Remito:
    """Anula un remito: revierte el stock y marca el remito como anulado.
    No borra el remito; sigue visible en el historial con el badge."""
    remito = obtener_remito(db, remito_id)
    if not remito:
        raise HTTPException(status_code=404, detail="Remito no encontrado")
    if remito.anulado_at is not None:
        raise HTTPException(status_code=400, detail="El remito ya esta anulado")

    motivo = (data.motivo or "").strip()
    if not motivo:
        raise HTTPException(status_code=400, detail="El motivo de anulacion es obligatorio")

    _revertir_descuentos(db, remito, usuario_id)
    # Borrar los descuentos viejos (el revert ya creo los movimientos
    # de devolucion). Asi tampoco los re-reverso si alguien intenta
    # anular dos veces.
    for desc in list(remito.descuentos):
        db.delete(desc)

    remito.anulado_at = datetime.utcnow()
    remito.anulado_por_id = usuario_id
    remito.motivo_anulacion = motivo

    db.commit()
    db.refresh(remito)
    return remito


def editar_remito_general(
    db: Session,
    remito_id: UUID,
    data: "RemitoUpdate",
    usuario_id: Optional[UUID],
) -> Remito:
    """Edita los datos generales del remito (fecha, destinatario, etc).
    No toca items ni stock. Marca el remito como editado."""
    remito = obtener_remito(db, remito_id)
    if not remito:
        raise HTTPException(status_code=404, detail="Remito no encontrado")
    if remito.anulado_at is not None:
        raise HTTPException(status_code=400, detail="No se puede editar un remito anulado")

    cambios = data.model_dump(exclude_unset=True)
    for field, value in cambios.items():
        setattr(remito, field, value)

    remito.editado_at = datetime.utcnow()
    remito.editado_por_id = usuario_id

    db.commit()
    db.refresh(remito)
    return remito


def editar_remito_items(
    db: Session,
    remito_id: UUID,
    data: "RemitoItemsUpdate",
    usuario_id: Optional[UUID],
) -> Remito:
    """Reemplaza los items del remito: revierte los descuentos viejos,
    borra items/descuentos anteriores y vuelve a aplicar la cascada con
    los items nuevos. Marca el remito como editado."""
    remito = obtener_remito(db, remito_id)
    if not remito:
        raise HTTPException(status_code=404, detail="Remito no encontrado")
    if remito.anulado_at is not None:
        raise HTTPException(status_code=400, detail="No se puede editar un remito anulado")
    if not data.items:
        raise HTTPException(status_code=400, detail="El remito necesita al menos un item")

    deposito = db.query(Deposito).filter(
        Deposito.id == remito.deposito_id,
        Deposito.activo == True,
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    # 1) Revertir descuentos viejos
    _revertir_descuentos(db, remito, usuario_id)
    for desc in list(remito.descuentos):
        db.delete(desc)
    for item in list(remito.items):
        db.delete(item)
    db.flush()

    # 2) Aplicar los items nuevos
    for item_data in data.items:
        if item_data.cantidad <= 0:
            continue
        material = db.query(Material).filter(Material.id == item_data.material_id).first()
        if not material:
            raise HTTPException(
                status_code=404,
                detail=f"Material {item_data.material_id} no encontrado",
            )
        db.add(RemitoItem(
            remito_id=remito.id,
            material_id=material.id,
            material_codigo=material.codigo,
            material_nombre=material.nombre,
            material_unidad=material.unidad,
            cantidad=item_data.cantidad,
        ))
        _descontar_material_cascada(
            db,
            remito_id=remito.id,
            origen=deposito,
            material=material,
            cantidad=item_data.cantidad,
            motivo_prefix=f"Edicion de remito {remito.numero_formateado}",
            proyecto_id=remito.proyecto_id,
            usuario_id=usuario_id,
        )

    remito.editado_at = datetime.utcnow()
    remito.editado_por_id = usuario_id

    db.commit()
    db.refresh(remito)
    return remito
