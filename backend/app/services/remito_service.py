"""Servicio de remitos: salida de materiales con descuento de stock."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.remito import Remito, RemitoItem, RemitoDescuento, TipoRemito
from app.models.deposito import Deposito, DepositoMaterial
from app.models.material import Material
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.schemas.remito import (
    RemitoCreate, RemitoUpdate, RemitoItemsUpdate, RemitoAnular,
    RemitoIngresoCreate,
)


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


def _depositos_relacionados(
    db: Session,
    origen: Deposito,
    incluir_todos: bool = False,
) -> List[Deposito]:
    """Devuelve [origen, ...resto] donde 'resto' son los otros depositos
    candidatos para tomar stock. Por defecto solo el grupo del origen
    (padre + hermanos si origen es subdeposito, o hijos si es root).

    Si `incluir_todos=True`, agrega ademas todos los demas depositos
    activos del sistema (luego del grupo del origen, para que el
    descuento siga priorizando lo local).
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

    candidatos: List[Deposito] = [origen, *resto]

    if incluir_todos:
        ids_actuales = {d.id for d in candidatos}
        otros = (
            db.query(Deposito)
            .filter(
                Deposito.activo == True,
                ~Deposito.id.in_(ids_actuales),
            )
            .all()
        )
        candidatos.extend(otros)

    return candidatos


def _descontar_material_cascada(
    db: Session,
    remito_id: UUID,
    origen: Deposito,
    material: Material,
    cantidad: Decimal,
    motivo_prefix: str,
    proyecto_id: Optional[UUID],
    usuario_id: Optional[UUID],
    descontar_de_cualquier_deposito: bool = False,
) -> None:
    """Descuenta `cantidad` de `material` empezando por `origen` y
    siguiendo con los depositos del mismo grupo (padre+hermanos o hijos).
    Si `descontar_de_cualquier_deposito=True`, despues del grupo del
    origen tambien se puede tomar stock de cualquier otro deposito
    activo (ordenado por stock disponible descendente).
    Si despues de recorrer todo queda restante, lo descuenta del `origen`
    dejandolo en negativo. Cada descuento real se registra en
    `RemitoDescuento` para poder revertirlo despues.
    """
    restante = cantidad
    candidatos = _depositos_relacionados(
        db, origen, incluir_todos=descontar_de_cualquier_deposito
    )

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
            deposito_id=dep.id,
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
            deposito_id=origen.id,
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
        # (o hijos si origen es root). Si `descontar_de_cualquier_deposito`
        # esta activo, sigue con todos los demas depositos activos. Si nada
        # alcanza, deja el origen en negativo. Cada descuento real genera
        # un MovimientoStock y un RemitoDescuento para poder revertirlo.
        _descontar_material_cascada(
            db,
            remito_id=remito.id,
            origen=deposito,
            material=material,
            cantidad=item_data.cantidad,
            motivo_prefix=f"Salida por remito {remito.numero_formateado}",
            proyecto_id=data.proyecto_id,
            usuario_id=usuario_id,
            descontar_de_cualquier_deposito=data.descontar_de_cualquier_deposito,
        )

    db.commit()
    db.refresh(remito)
    return remito


def crear_remito_ingreso(
    db: Session,
    data: RemitoIngresoCreate,
    usuario_id: Optional[UUID],
) -> Remito:
    """Crea un remito de INGRESO.

    - Si data.deposito_id esta seteado: suma stock al deposito.
    - Si data.deposito_id es None: suma stock al global (Material.stock_actual).
      El remito queda sin deposito asociado.

    Cada item registra un MovimientoStock tipo entrada. Si hay deposito,
    tambien registra un RemitoDescuento para poder revertirlo.
    """
    deposito = None
    if data.deposito_id:
        deposito = db.query(Deposito).filter(
            Deposito.id == data.deposito_id,
            Deposito.activo == True,
        ).first()
        if not deposito:
            raise HTTPException(status_code=404, detail="Deposito no encontrado")

    if not data.items:
        raise HTTPException(status_code=400, detail="El remito necesita al menos un item")

    remito = Remito(
        tipo=TipoRemito.ingreso,
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

        db.add(RemitoItem(
            remito_id=remito.id,
            material_id=material.id,
            material_codigo=material.codigo,
            material_nombre=material.nombre,
            material_unidad=material.unidad,
            cantidad=item_data.cantidad,
        ))

        if deposito:
            # Suma al stock del deposito
            dm = _get_or_create_deposito_material(db, deposito.id, material.id)
            stock_anterior = dm.stock_actual
            dm.stock_actual = stock_anterior + item_data.cantidad
            destino_label = f"deposito {deposito.nombre}"
            mov_deposito_id = deposito.id
        else:
            # Suma al stock global del material
            stock_anterior = material.stock_actual
            material.stock_actual = stock_anterior + item_data.cantidad
            destino_label = "stock global"
            mov_deposito_id = None

        db.add(MovimientoStock(
            material_id=material.id,
            tipo=TipoMovimiento.entrada,
            cantidad=item_data.cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_anterior + item_data.cantidad,
            motivo=f"Ingreso por remito {remito.numero_formateado} ({destino_label})",
            proyecto_id=data.proyecto_id,
            deposito_id=mov_deposito_id,
            usuario_id=usuario_id,
        ))

        # Solo guardo RemitoDescuento si hay deposito (la reversion para
        # ingreso global se hace tocando Material.stock_actual directamente
        # en _revertir_descuentos via los RemitoItem si no hay descuentos).
        if deposito:
            db.add(RemitoDescuento(
                remito_id=remito.id,
                deposito_id=deposito.id,
                material_id=material.id,
                cantidad=item_data.cantidad,
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
    tipo: Optional[str] = None,
) -> List[Remito]:
    query = db.query(Remito).filter(Remito.activo == True)

    if tipo in ("egreso", "ingreso"):
        query = query.filter(Remito.tipo == tipo)
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


def _deposito_path(remito: Remito) -> tuple[str | None, str | None, bool, bool]:
    """Devuelve (nombre_propio, nombre_padre, es_subdeposito, eliminado) del deposito.

    Cuando el remito sale de un subdeposito, queremos saber tambien el
    nombre del padre para dar contexto en la UI y en el PDF. Si el
    deposito ya fue borrado (activo=False), `eliminado=True` para que
    el frontend lo distinga.
    """
    if not remito.deposito:
        return None, None, False, False
    propio = remito.deposito.nombre
    es_sub = remito.deposito.parent_id is not None
    padre_nombre = remito.deposito.parent.nombre if es_sub and remito.deposito.parent else None
    eliminado = not remito.deposito.activo
    return propio, padre_nombre, es_sub, eliminado


def to_response_dict(remito: Remito) -> dict:
    """Helper para construir el dict de RemitoResponse con campos derivados."""
    propio, padre, es_sub, eliminado = _deposito_path(remito)
    return {
        "id": remito.id,
        "tipo": remito.tipo.value if hasattr(remito.tipo, "value") else str(remito.tipo or "egreso"),
        "numero": remito.numero,
        "numero_formateado": remito.numero_formateado,
        "fecha": remito.fecha,
        "deposito_id": remito.deposito_id,
        "deposito_nombre": propio,
        "deposito_padre_nombre": padre,
        "es_subdeposito": es_sub,
        "deposito_eliminado": eliminado,
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
    propio, padre, es_sub, eliminado = _deposito_path(remito)
    return {
        "id": remito.id,
        "tipo": remito.tipo.value if hasattr(remito.tipo, "value") else str(remito.tipo or "egreso"),
        "numero": remito.numero,
        "numero_formateado": remito.numero_formateado,
        "fecha": remito.fecha,
        "deposito_id": remito.deposito_id,
        "deposito_nombre": propio,
        "deposito_padre_nombre": padre,
        "es_subdeposito": es_sub,
        "deposito_eliminado": eliminado,
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
    """Revierte el efecto del remito sobre el stock.

    - En remitos de EGRESO: cada RemitoDescuento representa lo que se
      sacó; al revertir, se suma de vuelta al deposito de origen.
    - En remitos de INGRESO: cada RemitoDescuento representa lo que se
      sumó; al revertir, se resta del deposito de destino (puede dejarlo
      en negativo si ya se consumió).
    """
    es_ingreso = remito.tipo == TipoRemito.ingreso

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
            if es_ingreso:
                dm.stock_actual = stock_anterior - desc.cantidad
                tipo_mov = TipoMovimiento.salida
                signo = -1
            else:
                dm.stock_actual = stock_anterior + desc.cantidad
                tipo_mov = TipoMovimiento.devolucion
                signo = 1
            db.add(MovimientoStock(
                material_id=desc.material_id,
                tipo=tipo_mov,
                cantidad=desc.cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_anterior + signo * desc.cantidad,
                motivo=f"Reversion de remito {remito.numero_formateado}",
                proyecto_id=remito.proyecto_id,
                deposito_id=desc.deposito_id,
                usuario_id=usuario_id,
            ))
    else:
        # Fallback: remitos sin RemitoDescuento.
        # - Egresos viejos: asumimos que se descontó del deposito de origen
        #   (suma de vuelta).
        # - Ingresos sin deposito (al stock global): resta del
        #   Material.stock_actual.
        for item in remito.items:
            if not item.material_id or item.cantidad <= 0:
                continue
            material = db.query(Material).filter(Material.id == item.material_id).first()
            if not material:
                continue

            if es_ingreso and not remito.deposito_id:
                # Ingreso global: restar del stock global
                stock_anterior = material.stock_actual
                material.stock_actual = stock_anterior - item.cantidad
                db.add(MovimientoStock(
                    material_id=item.material_id,
                    tipo=TipoMovimiento.salida,
                    cantidad=item.cantidad,
                    stock_anterior=stock_anterior,
                    stock_nuevo=stock_anterior - item.cantidad,
                    motivo=f"Reversion de remito {remito.numero_formateado} (ingreso global)",
                    proyecto_id=remito.proyecto_id,
                    deposito_id=None,
                    usuario_id=usuario_id,
                ))
                continue

            if not remito.deposito_id:
                continue
            dm = db.query(DepositoMaterial).filter(
                DepositoMaterial.deposito_id == remito.deposito_id,
                DepositoMaterial.material_id == item.material_id,
                DepositoMaterial.activo == True,
            ).first()
            if not dm:
                continue
            stock_anterior = dm.stock_actual
            if es_ingreso:
                dm.stock_actual = stock_anterior - item.cantidad
                tipo_mov = TipoMovimiento.salida
                signo = -1
            else:
                dm.stock_actual = stock_anterior + item.cantidad
                tipo_mov = TipoMovimiento.devolucion
                signo = 1
            db.add(MovimientoStock(
                material_id=item.material_id,
                tipo=tipo_mov,
                cantidad=item.cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_anterior + signo * item.cantidad,
                motivo=f"Reversion de remito {remito.numero_formateado} (fallback origen)",
                proyecto_id=remito.proyecto_id,
                deposito_id=remito.deposito_id,
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


def borrar_remito(
    db: Session,
    remito_id: UUID,
    usuario_id: Optional[UUID],
) -> None:
    """Elimina definitivamente el remito del historial. Si no estaba
    anulado, primero revierte el stock que habia descontado. Es un soft
    delete (activo=False) pero el listado ya filtra por activo, asi que
    desaparece de la UI.
    """
    remito = obtener_remito(db, remito_id)
    if not remito:
        raise HTTPException(status_code=404, detail="Remito no encontrado")

    if remito.anulado_at is None:
        # Todavia tiene stock descontado, hay que devolverlo
        _revertir_descuentos(db, remito, usuario_id)
        for desc in list(remito.descuentos):
            db.delete(desc)

    remito.activo = False
    db.commit()


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

    es_ingreso = remito.tipo == TipoRemito.ingreso

    # 1) Revertir el efecto viejo (resta para egresos al reverso, etc.)
    _revertir_descuentos(db, remito, usuario_id)
    for desc in list(remito.descuentos):
        db.delete(desc)
    for item in list(remito.items):
        db.delete(item)
    db.flush()

    # 2) Aplicar los items nuevos segun el tipo
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
        if es_ingreso:
            # Suma directa al deposito de destino
            dm = _get_or_create_deposito_material(db, deposito.id, material.id)
            stock_anterior = dm.stock_actual
            dm.stock_actual = stock_anterior + item_data.cantidad
            db.add(MovimientoStock(
                material_id=material.id,
                tipo=TipoMovimiento.entrada,
                cantidad=item_data.cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_anterior + item_data.cantidad,
                motivo=f"Edicion de remito {remito.numero_formateado} (deposito {deposito.nombre})",
                proyecto_id=remito.proyecto_id,
                deposito_id=deposito.id,
                usuario_id=usuario_id,
            ))
            db.add(RemitoDescuento(
                remito_id=remito.id,
                deposito_id=deposito.id,
                material_id=material.id,
                cantidad=item_data.cantidad,
            ))
        else:
            _descontar_material_cascada(
                db,
                remito_id=remito.id,
                origen=deposito,
                material=material,
                cantidad=item_data.cantidad,
                motivo_prefix=f"Edicion de remito {remito.numero_formateado}",
                proyecto_id=remito.proyecto_id,
                usuario_id=usuario_id,
                descontar_de_cualquier_deposito=data.descontar_de_cualquier_deposito,
            )

    remito.editado_at = datetime.utcnow()
    remito.editado_por_id = usuario_id

    db.commit()
    db.refresh(remito)
    return remito
