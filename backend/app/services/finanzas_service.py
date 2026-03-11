from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date, timedelta
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa
from app.models.item_trabajo import ItemTrabajo
from app.models.asignacion_material import AsignacionMaterial
from app.models.gasto import Gasto
from app.models.precio_item import PrecioItem
from app.models.categoria_gasto import CategoriaGasto
from app.models.transaccion import (
    Transaccion, TipoTransaccion, EstadoTransaccion, MetodoPago,
    Cuenta, TipoCuenta,
    ClienteProveedor, TipoClienteProveedor,
    Presupuesto
)
from app.schemas.finanzas import (
    ResumenFinancieroProyecto,
    ResumenCostosEtapa,
    ResumenFinancieroGeneral
)
from app.schemas.transaccion import (
    TransaccionCreate, TransaccionUpdate,
    CuentaCreate, CuentaUpdate,
    ClienteProveedorCreate, ClienteProveedorUpdate,
    PresupuestoCreate, PresupuestoUpdate
)


def cargar_precio_item(
    db: Session,
    item_trabajo_id: UUID,
    precio_unitario: Decimal,
    usuario_id: UUID
) -> PrecioItem:
    """Carga o actualiza el precio de un ítem de trabajo."""
    # Cerrar precio anterior si existe
    precio_actual = db.query(PrecioItem).filter(
        PrecioItem.item_trabajo_id == item_trabajo_id,
        PrecioItem.fecha_hasta.is_(None)
    ).first()

    if precio_actual:
        precio_actual.fecha_hasta = datetime.utcnow()

    # Crear nuevo precio
    nuevo_precio = PrecioItem(
        item_trabajo_id=item_trabajo_id,
        precio_unitario=precio_unitario,
        fecha_desde=datetime.utcnow(),
        updated_by=usuario_id
    )
    db.add(nuevo_precio)

    # Actualizar precio en el ítem
    item = db.query(ItemTrabajo).filter(ItemTrabajo.id == item_trabajo_id).first()
    if item:
        item.precio_unitario = precio_unitario

    db.commit()
    db.refresh(nuevo_precio)
    return nuevo_precio


def calcular_costo_etapa(db: Session, etapa_id: UUID) -> dict:
    """Calcula el costo total de una etapa."""
    # Costo de ítems (cantidad × precio_unitario)
    costo_items = db.query(
        func.coalesce(func.sum(ItemTrabajo.cantidad * ItemTrabajo.precio_unitario), 0)
    ).filter(
        ItemTrabajo.etapa_id == etapa_id,
        ItemTrabajo.activo == True
    ).scalar()

    # Costo de materiales asignados a la etapa
    costo_materiales = db.query(
        func.coalesce(func.sum(AsignacionMaterial.cantidad * AsignacionMaterial.precio_unitario), 0)
    ).filter(
        AsignacionMaterial.etapa_id == etapa_id
    ).scalar()

    return {
        "costo_items": Decimal(costo_items or 0),
        "costo_materiales": Decimal(costo_materiales or 0),
        "costo_total": Decimal(costo_items or 0) + Decimal(costo_materiales or 0)
    }


def obtener_resumen_financiero_proyecto(
    db: Session,
    proyecto_id: UUID
) -> Optional[ResumenFinancieroProyecto]:
    """Genera el resumen financiero completo de un proyecto."""
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        return None

    # Calcular costos por etapa
    etapas_resumen = []
    total_costo_items = Decimal(0)
    total_costo_materiales = Decimal(0)

    etapas = db.query(Etapa).filter(
        Etapa.proyecto_id == proyecto_id,
        Etapa.activo == True
    ).all()

    for etapa in etapas:
        costos_etapa = calcular_costo_etapa(db, etapa.id)
        etapas_resumen.append(ResumenCostosEtapa(
            etapa_id=etapa.id,
            nombre_etapa=etapa.nombre,
            costo_items=costos_etapa["costo_items"],
            costo_materiales=costos_etapa["costo_materiales"],
            costo_total=costos_etapa["costo_total"]
        ))
        total_costo_items += costos_etapa["costo_items"]
        total_costo_materiales += costos_etapa["costo_materiales"]

    # Gastos del proyecto
    total_gastos = db.query(
        func.coalesce(func.sum(Gasto.monto), 0)
    ).filter(
        Gasto.proyecto_id == proyecto_id,
        Gasto.activo == True
    ).scalar()
    total_gastos = Decimal(total_gastos or 0)

    # Calcular totales y rentabilidad
    costo_total = total_costo_items + total_costo_materiales + total_gastos

    rentabilidad = None
    porcentaje_rentabilidad = None
    if proyecto.monto_contratado:
        rentabilidad = proyecto.monto_contratado - costo_total
        if proyecto.monto_contratado > 0:
            porcentaje_rentabilidad = (rentabilidad / proyecto.monto_contratado) * 100

    return ResumenFinancieroProyecto(
        proyecto_id=proyecto.id,
        nombre_proyecto=proyecto.nombre,
        monto_contratado=proyecto.monto_contratado,
        costo_items=total_costo_items,
        costo_materiales=total_costo_materiales,
        costo_gastos=total_gastos,
        costo_total=costo_total,
        rentabilidad=rentabilidad,
        porcentaje_rentabilidad=porcentaje_rentabilidad,
        etapas=etapas_resumen
    )


def obtener_resumen_financiero_general(db: Session) -> ResumenFinancieroGeneral:
    """Genera el resumen financiero de todos los proyectos activos."""
    proyectos = db.query(Proyecto).filter(
        Proyecto.activo == True,
        Proyecto.estado.in_([EstadoProyecto.en_ejecucion, EstadoProyecto.planificacion])
    ).all()

    resumenes = []
    total_contratado = Decimal(0)
    total_costos = Decimal(0)

    for proyecto in proyectos:
        resumen = obtener_resumen_financiero_proyecto(db, proyecto.id)
        if resumen:
            resumenes.append(resumen)
            if resumen.monto_contratado:
                total_contratado += resumen.monto_contratado
            total_costos += resumen.costo_total

    return ResumenFinancieroGeneral(
        total_contratado=total_contratado,
        total_costos=total_costos,
        total_rentabilidad=total_contratado - total_costos,
        proyectos_activos=len(proyectos),
        proyectos=resumenes
    )


def actualizar_monto_contratado(
    db: Session,
    proyecto_id: UUID,
    monto: Decimal
) -> Optional[Proyecto]:
    """Actualiza el monto contratado de un proyecto."""
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if proyecto:
        proyecto.monto_contratado = monto
        db.commit()
        db.refresh(proyecto)
    return proyecto


# ============ TRANSACCIONES ============

def get_transacciones(
    db: Session,
    tipo: Optional[TipoTransaccion] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    proyecto_id: Optional[UUID] = None,
    categoria_id: Optional[UUID] = None,
    cuenta_id: Optional[UUID] = None,
    cliente_proveedor_id: Optional[UUID] = None,
    estado: Optional[EstadoTransaccion] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Transaccion]:
    """Obtiene transacciones con filtros."""
    query = db.query(Transaccion).filter(Transaccion.activo == True)

    if tipo:
        query = query.filter(Transaccion.tipo == tipo)
    if fecha_desde:
        query = query.filter(Transaccion.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Transaccion.fecha <= fecha_hasta)
    if proyecto_id:
        query = query.filter(Transaccion.proyecto_id == proyecto_id)
    if categoria_id:
        query = query.filter(Transaccion.categoria_id == categoria_id)
    if cuenta_id:
        query = query.filter(Transaccion.cuenta_id == cuenta_id)
    if cliente_proveedor_id:
        query = query.filter(Transaccion.cliente_proveedor_id == cliente_proveedor_id)
    if estado:
        query = query.filter(Transaccion.estado == estado)

    return query.order_by(Transaccion.fecha.desc(), Transaccion.created_at.desc()).offset(skip).limit(limit).all()


def get_transaccion(db: Session, transaccion_id: UUID) -> Optional[Transaccion]:
    """Obtiene una transaccion por ID."""
    return db.query(Transaccion).filter(
        Transaccion.id == transaccion_id,
        Transaccion.activo == True
    ).first()


def create_transaccion(
    db: Session,
    transaccion: TransaccionCreate,
    creado_por_id: UUID
) -> Transaccion:
    """Crea una nueva transaccion."""
    db_transaccion = Transaccion(
        **transaccion.model_dump(),
        creado_por_id=creado_por_id
    )
    db.add(db_transaccion)
    db.commit()
    db.refresh(db_transaccion)
    return db_transaccion


def update_transaccion(
    db: Session,
    transaccion_id: UUID,
    transaccion: TransaccionUpdate
) -> Optional[Transaccion]:
    """Actualiza una transaccion."""
    db_transaccion = get_transaccion(db, transaccion_id)
    if not db_transaccion:
        return None

    update_data = transaccion.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transaccion, field, value)

    db.commit()
    db.refresh(db_transaccion)
    return db_transaccion


def delete_transaccion(db: Session, transaccion_id: UUID) -> bool:
    """Elimina (soft delete) una transaccion."""
    db_transaccion = get_transaccion(db, transaccion_id)
    if not db_transaccion:
        return False

    db_transaccion.activo = False
    db.commit()
    return True


def anular_transaccion(db: Session, transaccion_id: UUID) -> Optional[Transaccion]:
    """Anula una transaccion."""
    db_transaccion = get_transaccion(db, transaccion_id)
    if not db_transaccion:
        return None

    db_transaccion.estado = EstadoTransaccion.ANULADA.value
    db.commit()
    db.refresh(db_transaccion)
    return db_transaccion


# ============ CUENTAS ============

def get_cuentas(db: Session, tipo: Optional[str] = None) -> List[Cuenta]:
    """Obtiene todas las cuentas."""
    query = db.query(Cuenta).filter(Cuenta.activo == True)
    if tipo:
        query = query.filter(Cuenta.tipo == tipo)
    return query.all()


def get_cuenta(db: Session, cuenta_id: UUID) -> Optional[Cuenta]:
    """Obtiene una cuenta por ID."""
    return db.query(Cuenta).filter(
        Cuenta.id == cuenta_id,
        Cuenta.activo == True
    ).first()


def create_cuenta(db: Session, cuenta: CuentaCreate) -> Cuenta:
    """Crea una nueva cuenta."""
    db_cuenta = Cuenta(**cuenta.model_dump())
    db.add(db_cuenta)
    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta


def update_cuenta(db: Session, cuenta_id: UUID, cuenta: CuentaUpdate) -> Optional[Cuenta]:
    """Actualiza una cuenta."""
    db_cuenta = get_cuenta(db, cuenta_id)
    if not db_cuenta:
        return None

    update_data = cuenta.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cuenta, field, value)

    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta


def delete_cuenta(db: Session, cuenta_id: UUID) -> bool:
    """Elimina una cuenta."""
    db_cuenta = get_cuenta(db, cuenta_id)
    if not db_cuenta:
        return False
    db_cuenta.activo = False
    db.commit()
    return True


def get_saldo_cuenta(db: Session, cuenta_id: UUID) -> dict:
    """Calcula el saldo de una cuenta."""
    cuenta = get_cuenta(db, cuenta_id)
    if not cuenta:
        return {"error": "Cuenta no encontrada"}

    # Sumar ingresos
    total_ingresos = db.query(func.coalesce(func.sum(Transaccion.monto), 0)).filter(
        Transaccion.cuenta_id == cuenta_id,
        Transaccion.tipo == TipoTransaccion.INGRESO.value,
        Transaccion.estado == EstadoTransaccion.CONFIRMADA.value,
        Transaccion.activo == True
    ).scalar() or Decimal(0)

    # Sumar egresos
    total_egresos = db.query(func.coalesce(func.sum(Transaccion.monto), 0)).filter(
        Transaccion.cuenta_id == cuenta_id,
        Transaccion.tipo == TipoTransaccion.EGRESO.value,
        Transaccion.estado == EstadoTransaccion.CONFIRMADA.value,
        Transaccion.activo == True
    ).scalar() or Decimal(0)

    saldo_inicial = Decimal(str(cuenta.saldo_inicial or 0))
    saldo_actual = saldo_inicial + total_ingresos - total_egresos

    return {
        "cuenta_id": str(cuenta_id),
        "nombre": cuenta.nombre,
        "tipo": cuenta.tipo.value,
        "saldo_inicial": float(saldo_inicial),
        "total_ingresos": float(total_ingresos),
        "total_egresos": float(total_egresos),
        "saldo_actual": float(saldo_actual)
    }


# ============ CLIENTES/PROVEEDORES ============

def get_clientes_proveedores(db: Session, tipo: Optional[str] = None) -> List[ClienteProveedor]:
    """Obtiene clientes/proveedores."""
    query = db.query(ClienteProveedor).filter(ClienteProveedor.activo == True)
    if tipo:
        query = query.filter(ClienteProveedor.tipo == tipo)
    return query.order_by(ClienteProveedor.razon_social).all()


def get_cliente_proveedor(db: Session, cliente_proveedor_id: UUID) -> Optional[ClienteProveedor]:
    """Obtiene un cliente/proveedor por ID."""
    return db.query(ClienteProveedor).filter(
        ClienteProveedor.id == cliente_proveedor_id,
        ClienteProveedor.activo == True
    ).first()


def create_cliente_proveedor(db: Session, cliente_proveedor: ClienteProveedorCreate) -> ClienteProveedor:
    """Crea un cliente/proveedor."""
    db_cp = ClienteProveedor(**cliente_proveedor.model_dump())
    db.add(db_cp)
    db.commit()
    db.refresh(db_cp)
    return db_cp


def update_cliente_proveedor(
    db: Session,
    cliente_proveedor_id: UUID,
    cliente_proveedor: ClienteProveedorUpdate
) -> Optional[ClienteProveedor]:
    """Actualiza un cliente/proveedor."""
    db_cp = get_cliente_proveedor(db, cliente_proveedor_id)
    if not db_cp:
        return None

    update_data = cliente_proveedor.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cp, field, value)

    db.commit()
    db.refresh(db_cp)
    return db_cp


def delete_cliente_proveedor(db: Session, cliente_proveedor_id: UUID) -> bool:
    """Elimina un cliente/proveedor."""
    db_cp = get_cliente_proveedor(db, cliente_proveedor_id)
    if not db_cp:
        return False
    db_cp.activo = False
    db.commit()
    return True


def get_cuenta_corriente(db: Session, cliente_proveedor_id: UUID) -> dict:
    """Obtiene el estado de cuenta corriente de un cliente/proveedor."""
    cp = get_cliente_proveedor(db, cliente_proveedor_id)
    if not cp:
        return {"error": "Cliente/Proveedor no encontrado"}

    # Transacciones del cliente/proveedor
    transacciones = db.query(Transaccion).filter(
        Transaccion.cliente_proveedor_id == cliente_proveedor_id,
        Transaccion.estado == EstadoTransaccion.CONFIRMADA.value,
        Transaccion.activo == True
    ).order_by(Transaccion.fecha.desc()).all()

    # Calcular saldo
    total_ingresos = sum(float(t.monto) for t in transacciones if t.tipo == TipoTransaccion.INGRESO.value)
    total_egresos = sum(float(t.monto) for t in transacciones if t.tipo == TipoTransaccion.EGRESO.value)

    return {
        "cliente_proveedor": {
            "id": str(cp.id),
            "razon_social": cp.razon_social,
            "tipo": cp.tipo.value
        },
        "total_ingresos": total_ingresos,
        "total_egresos": total_egresos,
        "saldo": total_ingresos - total_egresos,
        "transacciones": [
            {
                "id": str(t.id),
                "fecha": t.fecha.isoformat(),
                "tipo": t.tipo.value,
                "concepto": t.concepto,
                "monto": float(t.monto)
            }
            for t in transacciones[:50]
        ]
    }


# ============ PRESUPUESTOS ============

def get_presupuestos(db: Session, proyecto_id: Optional[UUID] = None) -> List[Presupuesto]:
    """Obtiene presupuestos."""
    query = db.query(Presupuesto).filter(Presupuesto.activo == True)
    if proyecto_id:
        query = query.filter(Presupuesto.proyecto_id == proyecto_id)
    return query.all()


def get_presupuesto(db: Session, presupuesto_id: UUID) -> Optional[Presupuesto]:
    """Obtiene un presupuesto por ID."""
    return db.query(Presupuesto).filter(
        Presupuesto.id == presupuesto_id,
        Presupuesto.activo == True
    ).first()


def create_presupuesto(db: Session, presupuesto: PresupuestoCreate) -> Presupuesto:
    """Crea un presupuesto."""
    db_presupuesto = Presupuesto(**presupuesto.model_dump())
    db.add(db_presupuesto)
    db.commit()
    db.refresh(db_presupuesto)
    return db_presupuesto


def update_presupuesto(
    db: Session,
    presupuesto_id: UUID,
    presupuesto: PresupuestoUpdate
) -> Optional[Presupuesto]:
    """Actualiza un presupuesto."""
    db_p = get_presupuesto(db, presupuesto_id)
    if not db_p:
        return None

    update_data = presupuesto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_p, field, value)

    db.commit()
    db.refresh(db_p)
    return db_p


def delete_presupuesto(db: Session, presupuesto_id: UUID) -> bool:
    """Elimina un presupuesto."""
    db_p = get_presupuesto(db, presupuesto_id)
    if not db_p:
        return False
    db_p.activo = False
    db.commit()
    return True


# ============ BALANCES Y REPORTES ============

def get_balance_general(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date,
    proyecto_id: Optional[UUID] = None
) -> dict:
    """Genera balance general del periodo."""
    base_filters = [
        Transaccion.fecha >= fecha_desde,
        Transaccion.fecha <= fecha_hasta,
        Transaccion.estado == EstadoTransaccion.CONFIRMADA.value,
        Transaccion.activo == True
    ]
    if proyecto_id:
        base_filters.append(Transaccion.proyecto_id == proyecto_id)

    # Total ingresos
    total_ingresos = db.query(func.coalesce(func.sum(Transaccion.monto), 0)).filter(
        *base_filters,
        Transaccion.tipo == TipoTransaccion.INGRESO.value
    ).scalar() or Decimal(0)

    # Total egresos
    total_egresos = db.query(func.coalesce(func.sum(Transaccion.monto), 0)).filter(
        *base_filters,
        Transaccion.tipo == TipoTransaccion.EGRESO.value
    ).scalar() or Decimal(0)

    # Por categoria - Ingresos
    ingresos_por_categoria = db.query(
        CategoriaGasto.nombre,
        func.sum(Transaccion.monto).label('total')
    ).join(
        CategoriaGasto, Transaccion.categoria_id == CategoriaGasto.id, isouter=True
    ).filter(
        *base_filters,
        Transaccion.tipo == TipoTransaccion.INGRESO.value
    ).group_by(CategoriaGasto.nombre).all()

    # Por categoria - Egresos
    egresos_por_categoria = db.query(
        CategoriaGasto.nombre,
        func.sum(Transaccion.monto).label('total')
    ).join(
        CategoriaGasto, Transaccion.categoria_id == CategoriaGasto.id, isouter=True
    ).filter(
        *base_filters,
        Transaccion.tipo == TipoTransaccion.EGRESO.value
    ).group_by(CategoriaGasto.nombre).all()

    # Por metodo de pago
    ingresos_por_metodo = db.query(
        Transaccion.metodo_pago,
        func.sum(Transaccion.monto).label('total')
    ).filter(
        *base_filters,
        Transaccion.tipo == TipoTransaccion.INGRESO.value
    ).group_by(Transaccion.metodo_pago).all()

    egresos_por_metodo = db.query(
        Transaccion.metodo_pago,
        func.sum(Transaccion.monto).label('total')
    ).filter(
        *base_filters,
        Transaccion.tipo == TipoTransaccion.EGRESO.value
    ).group_by(Transaccion.metodo_pago).all()

    # Cantidad de transacciones
    cant_ingresos = db.query(func.count(Transaccion.id)).filter(
        *base_filters,
        Transaccion.tipo == TipoTransaccion.INGRESO.value
    ).scalar() or 0

    cant_egresos = db.query(func.count(Transaccion.id)).filter(
        *base_filters,
        Transaccion.tipo == TipoTransaccion.EGRESO.value
    ).scalar() or 0

    return {
        "fecha_desde": fecha_desde.isoformat(),
        "fecha_hasta": fecha_hasta.isoformat(),
        "total_ingresos": float(total_ingresos),
        "total_egresos": float(total_egresos),
        "balance": float(total_ingresos - total_egresos),
        "cantidad_ingresos": cant_ingresos,
        "cantidad_egresos": cant_egresos,
        "ingresos_por_categoria": [
            {"categoria": c or "Sin categoria", "total": float(t)}
            for c, t in ingresos_por_categoria
        ],
        "egresos_por_categoria": [
            {"categoria": c or "Sin categoria", "total": float(t)}
            for c, t in egresos_por_categoria
        ],
        "ingresos_por_metodo_pago": [
            {"metodo": m.value if m else "otro", "total": float(t)}
            for m, t in ingresos_por_metodo
        ],
        "egresos_por_metodo_pago": [
            {"metodo": m.value if m else "otro", "total": float(t)}
            for m, t in egresos_por_metodo
        ]
    }


def get_flujo_caja(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date,
    cuenta_id: Optional[UUID] = None
) -> List[dict]:
    """Genera flujo de caja diario."""
    flujo = []
    saldo_acumulado = Decimal(0)

    # Si hay cuenta, obtener saldo inicial
    if cuenta_id:
        cuenta = get_cuenta(db, cuenta_id)
        if cuenta:
            saldo_acumulado = Decimal(str(cuenta.saldo_inicial or 0))

    current_date = fecha_desde
    while current_date <= fecha_hasta:
        base_filters = [
            Transaccion.fecha == current_date,
            Transaccion.estado == EstadoTransaccion.CONFIRMADA.value,
            Transaccion.activo == True
        ]
        if cuenta_id:
            base_filters.append(Transaccion.cuenta_id == cuenta_id)

        ingresos = db.query(func.coalesce(func.sum(Transaccion.monto), 0)).filter(
            *base_filters,
            Transaccion.tipo == TipoTransaccion.INGRESO.value
        ).scalar() or Decimal(0)

        egresos = db.query(func.coalesce(func.sum(Transaccion.monto), 0)).filter(
            *base_filters,
            Transaccion.tipo == TipoTransaccion.EGRESO.value
        ).scalar() or Decimal(0)

        saldo_inicial = saldo_acumulado
        saldo_acumulado = saldo_acumulado + ingresos - egresos

        # Solo agregar dias con movimiento o el primero/ultimo
        if ingresos > 0 or egresos > 0 or current_date == fecha_desde or current_date == fecha_hasta:
            flujo.append({
                "fecha": current_date.isoformat(),
                "saldo_inicial": float(saldo_inicial),
                "ingresos": float(ingresos),
                "egresos": float(egresos),
                "saldo_final": float(saldo_acumulado)
            })

        current_date += timedelta(days=1)

    return flujo


def get_resumen_mensual(db: Session, mes: int, anio: int) -> dict:
    """Genera resumen financiero mensual."""
    # Fechas del mes
    fecha_inicio = date(anio, mes, 1)
    if mes == 12:
        fecha_fin = date(anio + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin = date(anio, mes + 1, 1) - timedelta(days=1)

    # Mes anterior para comparacion
    if mes == 1:
        mes_ant = 12
        anio_ant = anio - 1
    else:
        mes_ant = mes - 1
        anio_ant = anio

    fecha_inicio_ant = date(anio_ant, mes_ant, 1)
    if mes_ant == 12:
        fecha_fin_ant = date(anio_ant + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin_ant = date(anio_ant, mes_ant + 1, 1) - timedelta(days=1)

    # Balance actual
    balance_actual = get_balance_general(db, fecha_inicio, fecha_fin)

    # Balance anterior
    balance_anterior = get_balance_general(db, fecha_inicio_ant, fecha_fin_ant)

    # Variacion
    balance_act = balance_actual["balance"]
    balance_ant = balance_anterior["balance"]
    if balance_ant != 0:
        variacion = ((balance_act - balance_ant) / abs(balance_ant)) * 100
    else:
        variacion = 100 if balance_act > 0 else -100 if balance_act < 0 else 0

    # Saldos de cuentas
    cuentas = get_cuentas(db)
    cuentas_con_saldo = []
    for cuenta in cuentas:
        saldo = get_saldo_cuenta(db, cuenta.id)
        cuentas_con_saldo.append(saldo)

    return {
        "periodo": f"{mes:02d}/{anio}",
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "ingresos_totales": balance_actual["total_ingresos"],
        "egresos_totales": balance_actual["total_egresos"],
        "balance": balance_actual["balance"],
        "cantidad_ingresos": balance_actual["cantidad_ingresos"],
        "cantidad_egresos": balance_actual["cantidad_egresos"],
        "variacion_vs_anterior": round(variacion, 2),
        "top_categorias_ingreso": sorted(
            balance_actual["ingresos_por_categoria"],
            key=lambda x: x["total"],
            reverse=True
        )[:5],
        "top_categorias_egreso": sorted(
            balance_actual["egresos_por_categoria"],
            key=lambda x: x["total"],
            reverse=True
        )[:5],
        "cuentas": cuentas_con_saldo
    }


def get_dashboard_finanzas(db: Session) -> dict:
    """Obtiene datos para el dashboard de finanzas."""
    hoy = date.today()
    inicio_mes = date(hoy.year, hoy.month, 1)

    # Balance del mes actual
    balance_mes = get_balance_general(db, inicio_mes, hoy)

    # Saldos de cuentas
    cuentas = get_cuentas(db)
    saldo_total = sum(
        get_saldo_cuenta(db, c.id).get("saldo_actual", 0)
        for c in cuentas
    )

    # Ultimas transacciones
    ultimas = get_transacciones(db, limit=10)

    # Transacciones pendientes
    pendientes = db.query(Transaccion).filter(
        Transaccion.estado == EstadoTransaccion.PENDIENTE.value,
        Transaccion.activo == True
    ).count()

    return {
        "saldo_total_cuentas": saldo_total,
        "ingresos_mes": balance_mes["total_ingresos"],
        "egresos_mes": balance_mes["total_egresos"],
        "balance_mes": balance_mes["balance"],
        "transacciones_pendientes": pendientes,
        "ultimas_transacciones": [
            {
                "id": str(t.id),
                "tipo": t.tipo.value,
                "concepto": t.concepto,
                "monto": float(t.monto),
                "fecha": t.fecha.isoformat(),
                "estado": t.estado.value
            }
            for t in ultimas
        ],
        "cuentas": [get_saldo_cuenta(db, c.id) for c in cuentas[:5]]
    }
