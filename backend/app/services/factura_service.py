from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from calendar import month_name

from fastapi import HTTPException

from app.models.factura import Factura, EstadoFactura
from app.models.cliente import Cliente
from app.models.proyecto import Proyecto
from app.models.transaccion import (
    Transaccion, TipoTransaccion, EstadoTransaccion, MetodoPago,
)
from app.models.tipo_ingreso import TipoIngresoConfig
from app.schemas.factura import (
    FacturaCreate, FacturaUpdate, MarcarPagadaRequest,
    EmpresaFacturasResumen, EmpresaQuickCreate, FacturaMesItem,
)


# ============ HELPERS ============

def _to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _serializar_factura(f: Factura) -> dict:
    return {
        "id": f.id,
        "cliente_id": f.cliente_id,
        "proyecto_id": f.proyecto_id,
        "descripcion": f.descripcion,
        "fecha_inscripcion": f.fecha_inscripcion,
        "monto": _to_float(f.monto),
        "fecha_pago": f.fecha_pago,
        "estado": f.estado.value if hasattr(f.estado, "value") else str(f.estado),
        "transaccion_id": f.transaccion_id,
        "creado_por_id": f.creado_por_id,
        "observaciones": f.observaciones,
        "cliente_nombre": (
            f.cliente.nombre_fantasia or f.cliente.razon_social
        ) if f.cliente else None,
        "proyecto_nombre": f.proyecto.nombre if f.proyecto else None,
    }


def _generar_codigo_cliente(db: Session) -> str:
    """Genera un codigo unico para un cliente empresa nuevo."""
    ultimo = (
        db.query(Cliente)
        .filter(Cliente.codigo.like("EMP-%"))
        .order_by(Cliente.codigo.desc())
        .first()
    )
    if not ultimo:
        return "EMP-0001"
    try:
        n = int(ultimo.codigo.split("-")[1]) + 1
    except (IndexError, ValueError):
        n = 1
    return f"EMP-{n:04d}"


# ============ EMPRESAS (clientes con tipo=empresa) ============

def listar_empresas_con_resumen(db: Session) -> List[EmpresaFacturasResumen]:
    """Lista clientes tipo empresa con resumen de sus facturas."""
    clientes = (
        db.query(Cliente)
        .filter(Cliente.activo == True, Cliente.tipo == 'empresa')
        .order_by(Cliente.razon_social)
        .all()
    )

    resumenes: List[EmpresaFacturasResumen] = []
    for c in clientes:
        facturas = (
            db.query(Factura)
            .filter(Factura.cliente_id == c.id, Factura.activo == True)
            .all()
        )
        cantidad_pendientes = sum(
            1 for f in facturas
            if (f.estado.value if hasattr(f.estado, "value") else f.estado) == "pendiente"
        )
        total_pendiente = sum(
            _to_float(f.monto) for f in facturas
            if (f.estado.value if hasattr(f.estado, "value") else f.estado) == "pendiente"
        )
        total_pagado = sum(
            _to_float(f.monto) for f in facturas
            if (f.estado.value if hasattr(f.estado, "value") else f.estado) == "pagada"
        )
        resumenes.append(EmpresaFacturasResumen(
            id=c.id,
            nombre=c.nombre_fantasia or c.razon_social,
            cuit=c.cuit,
            email=c.email,
            telefono=c.telefono,
            cantidad_facturas=len(facturas),
            cantidad_pendientes=cantidad_pendientes,
            total_pendiente=total_pendiente,
            total_pagado=total_pagado,
        ))
    return resumenes


def crear_empresa_rapida(db: Session, data: EmpresaQuickCreate) -> Cliente:
    """Crea rapidamente un Cliente con tipo=empresa desde el modulo facturas."""
    cliente = Cliente(
        codigo=_generar_codigo_cliente(db),
        tipo='empresa',
        razon_social=data.razon_social,
        nombre_fantasia=data.nombre_fantasia,
        cuit=data.cuit,
        email=data.email,
        telefono=data.telefono,
        condicion_iva='responsable_inscripto',
        fecha_alta=date.today(),
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def eliminar_empresa(db: Session, cliente_id: UUID) -> bool:
    """Soft delete de una empresa. Falla si tiene facturas activas."""
    cliente = db.query(Cliente).filter(
        Cliente.id == cliente_id, Cliente.activo == True
    ).first()
    if not cliente:
        return False

    facturas_activas = db.query(Factura).filter(
        Factura.cliente_id == cliente_id, Factura.activo == True
    ).count()
    if facturas_activas > 0:
        raise HTTPException(
            status_code=400,
            detail=f"La empresa tiene {facturas_activas} factura(s) cargada(s). Eliminalas antes de quitar la empresa."
        )

    cliente.activo = False
    db.commit()
    return True


# ============ FACTURAS ============

def listar_facturas(
    db: Session,
    cliente_id: Optional[UUID] = None,
    proyecto_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[Factura]:
    q = db.query(Factura).filter(Factura.activo == True)
    if cliente_id:
        q = q.filter(Factura.cliente_id == cliente_id)
    if proyecto_id:
        q = q.filter(Factura.proyecto_id == proyecto_id)
    if estado:
        q = q.filter(Factura.estado == estado)
    if fecha_desde:
        q = q.filter(Factura.fecha_inscripcion >= fecha_desde)
    if fecha_hasta:
        q = q.filter(Factura.fecha_inscripcion <= fecha_hasta)
    return q.order_by(Factura.fecha_inscripcion.desc()).all()


def obtener_factura(db: Session, factura_id: UUID) -> Optional[Factura]:
    return db.query(Factura).filter(
        Factura.id == factura_id, Factura.activo == True
    ).first()


def crear_factura(db: Session, data: FacturaCreate, creado_por_id: UUID) -> Factura:
    # Validar cliente y proyecto existen
    cliente = db.query(Cliente).filter(
        Cliente.id == data.cliente_id, Cliente.activo == True
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente/empresa no encontrado")

    proyecto = db.query(Proyecto).filter(Proyecto.id == data.proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto/obra no encontrado")

    factura = Factura(**data.model_dump(), creado_por_id=creado_por_id)
    db.add(factura)
    db.commit()
    db.refresh(factura)
    return factura


def actualizar_factura(
    db: Session, factura_id: UUID, data: FacturaUpdate
) -> Optional[Factura]:
    factura = obtener_factura(db, factura_id)
    if not factura:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(factura, k, v)
    db.commit()
    db.refresh(factura)
    return factura


def eliminar_factura(db: Session, factura_id: UUID) -> bool:
    factura = obtener_factura(db, factura_id)
    if not factura:
        return False

    # Si tiene transaccion asociada, anularla
    if factura.transaccion_id:
        tx = db.query(Transaccion).filter(Transaccion.id == factura.transaccion_id).first()
        if tx:
            tx.estado = EstadoTransaccion.ANULADA.value
            tx.activo = False

    factura.activo = False
    db.commit()
    return True


def _obtener_tipo_ingreso_cobro_obra(db: Session) -> Optional[TipoIngresoConfig]:
    """Busca la planilla 'Cobro factura obras' (case-insensitive) o cualquiera con 'factura' + 'obra'."""
    tipo = db.query(TipoIngresoConfig).filter(
        TipoIngresoConfig.activo == True,
        func.lower(TipoIngresoConfig.nombre) == "cobro factura obras",
    ).first()
    if tipo:
        return tipo
    # Fallback: cualquier planilla cuyo nombre contenga 'factura'
    return db.query(TipoIngresoConfig).filter(
        TipoIngresoConfig.activo == True,
        func.lower(TipoIngresoConfig.nombre).like("%factura%"),
    ).first()


def marcar_pagada(
    db: Session,
    factura_id: UUID,
    data: MarcarPagadaRequest,
    creado_por_id: UUID,
) -> Optional[Factura]:
    """Marca una factura como pagada y genera la Transaccion INGRESO correspondiente."""
    factura = obtener_factura(db, factura_id)
    if not factura:
        return None

    estado_actual = factura.estado.value if hasattr(factura.estado, "value") else factura.estado
    if estado_actual == "pagada":
        raise HTTPException(status_code=400, detail="La factura ya esta pagada")

    tipo_ingreso = _obtener_tipo_ingreso_cobro_obra(db)

    concepto = f"Cobro factura - {factura.proyecto.nombre if factura.proyecto else 'Obra'}"
    if factura.cliente:
        concepto += f" - {factura.cliente.nombre_fantasia or factura.cliente.razon_social}"

    tx = Transaccion(
        tipo=TipoTransaccion.INGRESO.value,
        tipo_ingreso_id=tipo_ingreso.id if tipo_ingreso else None,
        concepto=concepto[:300],
        descripcion=factura.descripcion,
        monto=factura.monto,
        fecha=data.fecha_pago,
        metodo_pago=MetodoPago.TRANSFERENCIA.value,
        estado=EstadoTransaccion.CONFIRMADA.value,
        proyecto_id=factura.proyecto_id,
        creado_por_id=creado_por_id,
    )
    db.add(tx)
    db.flush()

    factura.estado = EstadoFactura.PAGADA.value
    factura.fecha_pago = data.fecha_pago
    factura.transaccion_id = tx.id
    if data.observaciones:
        factura.observaciones = data.observaciones

    db.commit()
    db.refresh(factura)
    return factura


def marcar_pendiente(db: Session, factura_id: UUID) -> Optional[Factura]:
    """Revierte una factura a estado pendiente y anula la transaccion asociada."""
    factura = obtener_factura(db, factura_id)
    if not factura:
        return None

    if factura.transaccion_id:
        tx = db.query(Transaccion).filter(Transaccion.id == factura.transaccion_id).first()
        if tx:
            tx.estado = EstadoTransaccion.ANULADA.value
            tx.activo = False

    factura.estado = EstadoFactura.PENDIENTE.value
    factura.fecha_pago = None
    factura.transaccion_id = None

    db.commit()
    db.refresh(factura)
    return factura


def listar_pendientes(db: Session) -> List[Factura]:
    """Todas las facturas pendientes de todas las empresas, ordenadas por fecha."""
    return (
        db.query(Factura)
        .filter(Factura.activo == True, Factura.estado == "pendiente")
        .order_by(Factura.fecha_inscripcion.asc())
        .all()
    )


def agrupar_por_mes(
    db: Session,
    cliente_id: Optional[UUID] = None,
    anio: Optional[int] = None,
) -> List[FacturaMesItem]:
    """
    Agrupa facturas por mes usando fecha_pago cuando existe, o fecha_inscripcion
    cuando estan pendientes. Sirve para el resumen mensual.
    """
    q = db.query(Factura).filter(Factura.activo == True)
    if cliente_id:
        q = q.filter(Factura.cliente_id == cliente_id)
    facturas = q.all()

    buckets: dict[tuple, list[Factura]] = {}
    for f in facturas:
        fecha_ref = f.fecha_pago or f.fecha_inscripcion
        if anio and fecha_ref.year != anio:
            continue
        key = (fecha_ref.year, fecha_ref.month)
        buckets.setdefault(key, []).append(f)

    resultado: List[FacturaMesItem] = []
    for (y, m), lista in sorted(buckets.items(), reverse=True):
        resultado.append(FacturaMesItem(
            anio=y,
            mes=m,
            label=f"{MESES_ES[m - 1]} {y}",
            total=sum(_to_float(f.monto) for f in lista),
            cantidad=len(lista),
            facturas=[_serializar_factura(f) for f in lista],
        ))
    return resultado
