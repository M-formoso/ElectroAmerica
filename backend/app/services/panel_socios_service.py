from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date

from app.models.socio import Socio, AporteSocio, RetiroSocio
from app.models.transaccion import Transaccion, TipoTransaccion, EstadoTransaccion
from app.models.tipo_ingreso import TipoIngresoConfig
from app.models.categoria_gasto import CategoriaGasto
from app.schemas.socio import (
    SocioCreate, SocioUpdate,
    AporteSocioCreate, AporteSocioUpdate,
    RetiroSocioCreate, RetiroSocioUpdate,
    TipoIngresoCreate, TipoIngresoUpdate,
    ResumenPanelSocios, PlanillaIngresos, PlanillaGastos,
    SaldoSocio, ItemPlanilla,
)


# ============ SOCIOS ============

def listar_socios(db: Session) -> List[Socio]:
    return db.query(Socio).filter(Socio.activo == True).order_by(Socio.nombre).all()


def obtener_socio(db: Session, socio_id: UUID) -> Optional[Socio]:
    return db.query(Socio).filter(Socio.id == socio_id, Socio.activo == True).first()


def crear_socio(db: Session, data: SocioCreate) -> Socio:
    socio = Socio(**data.model_dump())
    db.add(socio)
    db.commit()
    db.refresh(socio)
    return socio


def actualizar_socio(db: Session, socio_id: UUID, data: SocioUpdate) -> Optional[Socio]:
    socio = obtener_socio(db, socio_id)
    if not socio:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(socio, k, v)
    db.commit()
    db.refresh(socio)
    return socio


def eliminar_socio(db: Session, socio_id: UUID) -> bool:
    socio = obtener_socio(db, socio_id)
    if not socio:
        return False
    socio.activo = False
    db.commit()
    return True


# ============ APORTES ============

def listar_aportes(
    db: Session,
    socio_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[AporteSocio]:
    q = db.query(AporteSocio).filter(AporteSocio.activo == True)
    if socio_id:
        q = q.filter(AporteSocio.socio_id == socio_id)
    if fecha_desde:
        q = q.filter(AporteSocio.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(AporteSocio.fecha <= fecha_hasta)
    return q.order_by(AporteSocio.fecha.desc()).all()


def obtener_aporte(db: Session, aporte_id: UUID) -> Optional[AporteSocio]:
    return db.query(AporteSocio).filter(
        AporteSocio.id == aporte_id, AporteSocio.activo == True
    ).first()


def crear_aporte(db: Session, data: AporteSocioCreate, creado_por_id: UUID) -> AporteSocio:
    aporte = AporteSocio(**data.model_dump(), creado_por_id=creado_por_id)
    db.add(aporte)
    db.commit()
    db.refresh(aporte)
    return aporte


def actualizar_aporte(
    db: Session, aporte_id: UUID, data: AporteSocioUpdate
) -> Optional[AporteSocio]:
    aporte = obtener_aporte(db, aporte_id)
    if not aporte:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(aporte, k, v)
    db.commit()
    db.refresh(aporte)
    return aporte


def eliminar_aporte(db: Session, aporte_id: UUID) -> bool:
    aporte = obtener_aporte(db, aporte_id)
    if not aporte:
        return False
    aporte.activo = False
    db.commit()
    return True


# ============ RETIROS ============

def listar_retiros(
    db: Session,
    socio_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[RetiroSocio]:
    q = db.query(RetiroSocio).filter(RetiroSocio.activo == True)
    if socio_id:
        q = q.filter(RetiroSocio.socio_id == socio_id)
    if fecha_desde:
        q = q.filter(RetiroSocio.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(RetiroSocio.fecha <= fecha_hasta)
    return q.order_by(RetiroSocio.fecha.desc()).all()


def obtener_retiro(db: Session, retiro_id: UUID) -> Optional[RetiroSocio]:
    return db.query(RetiroSocio).filter(
        RetiroSocio.id == retiro_id, RetiroSocio.activo == True
    ).first()


def crear_retiro(db: Session, data: RetiroSocioCreate, creado_por_id: UUID) -> RetiroSocio:
    retiro = RetiroSocio(**data.model_dump(), creado_por_id=creado_por_id)
    db.add(retiro)
    db.commit()
    db.refresh(retiro)
    return retiro


def actualizar_retiro(
    db: Session, retiro_id: UUID, data: RetiroSocioUpdate
) -> Optional[RetiroSocio]:
    retiro = obtener_retiro(db, retiro_id)
    if not retiro:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(retiro, k, v)
    db.commit()
    db.refresh(retiro)
    return retiro


def eliminar_retiro(db: Session, retiro_id: UUID) -> bool:
    retiro = obtener_retiro(db, retiro_id)
    if not retiro:
        return False
    retiro.activo = False
    db.commit()
    return True


# ============ TIPOS DE INGRESO (planillas dinamicas) ============

def listar_tipos_ingreso(db: Session) -> List[TipoIngresoConfig]:
    return db.query(TipoIngresoConfig).filter(
        TipoIngresoConfig.activo == True
    ).order_by(TipoIngresoConfig.orden, TipoIngresoConfig.nombre).all()


def obtener_tipo_ingreso(db: Session, tipo_id: UUID) -> Optional[TipoIngresoConfig]:
    return db.query(TipoIngresoConfig).filter(
        TipoIngresoConfig.id == tipo_id, TipoIngresoConfig.activo == True
    ).first()


def crear_tipo_ingreso(db: Session, data: TipoIngresoCreate) -> TipoIngresoConfig:
    tipo = TipoIngresoConfig(**data.model_dump())
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo


def actualizar_tipo_ingreso(
    db: Session, tipo_id: UUID, data: TipoIngresoUpdate
) -> Optional[TipoIngresoConfig]:
    tipo = obtener_tipo_ingreso(db, tipo_id)
    if not tipo:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(tipo, k, v)
    db.commit()
    db.refresh(tipo)
    return tipo


def eliminar_tipo_ingreso(db: Session, tipo_id: UUID) -> bool:
    tipo = obtener_tipo_ingreso(db, tipo_id)
    if not tipo:
        return False
    tipo.activo = False
    db.commit()
    return True


# ============ RESUMEN PANEL ============

def _to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


def _enum_value(v) -> Optional[str]:
    if v is None:
        return None
    return v.value if hasattr(v, "value") else str(v)


def obtener_resumen_panel(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date,
) -> ResumenPanelSocios:
    """
    Arma el resumen completo del panel de socios para el periodo dado.
    Las planillas de ingreso se leen dinamicamente de tipos_ingreso.
    """
    tipos_ingreso = listar_tipos_ingreso(db)

    # Transacciones confirmadas del periodo
    txs = db.query(Transaccion).filter(
        Transaccion.activo == True,
        Transaccion.estado == EstadoTransaccion.CONFIRMADA.value,
        Transaccion.fecha >= fecha_desde,
        Transaccion.fecha <= fecha_hasta,
    ).all()

    # --- Planillas de ingresos ---
    ingresos_por_tipo: dict[Optional[UUID], list[Transaccion]] = {}
    for t in txs:
        if _enum_value(t.tipo) != TipoTransaccion.INGRESO.value:
            continue
        ingresos_por_tipo.setdefault(t.tipo_ingreso_id, []).append(t)

    # Aportes de socios (tabla separada) se incluyen dentro de la planilla
    # marcada con es_aporte_socio=True.
    aportes = db.query(AporteSocio).filter(
        AporteSocio.activo == True,
        AporteSocio.fecha >= fecha_desde,
        AporteSocio.fecha <= fecha_hasta,
    ).all()
    aportes_items = [
        ItemPlanilla(
            id=a.id,
            concepto=a.concepto or "Aporte de socio",
            monto=_to_float(a.monto),
            fecha=a.fecha,
            referencia=f"{a.socio.nombre} {a.socio.apellido or ''}".strip() if a.socio else None,
        )
        for a in aportes
    ]

    tipo_aporte = next((t for t in tipos_ingreso if t.es_aporte_socio), None)

    planillas_ingresos: List[PlanillaIngresos] = []
    ids_conocidos = set()
    for tipo in tipos_ingreso:
        items = [
            ItemPlanilla(
                id=t.id,
                concepto=t.concepto,
                monto=_to_float(t.monto),
                fecha=t.fecha,
                referencia=t.proyecto.nombre if t.proyecto else None,
            )
            for t in ingresos_por_tipo.get(tipo.id, [])
        ]
        ids_conocidos.add(tipo.id)

        if tipo_aporte and tipo.id == tipo_aporte.id:
            items = items + aportes_items

        planillas_ingresos.append(PlanillaIngresos(
            tipo_id=tipo.id,
            nombre=tipo.nombre,
            color=tipo.color,
            total=sum(i.monto for i in items),
            cantidad=len(items),
            items=items,
        ))

    # Si el tipo aporte esta desactivado pero hay aportes, los mostramos aparte.
    if not tipo_aporte and aportes_items:
        planillas_ingresos.append(PlanillaIngresos(
            tipo_id=None,
            nombre="Aportes de socios",
            color="#10B981",
            total=sum(i.monto for i in aportes_items),
            cantidad=len(aportes_items),
            items=aportes_items,
        ))

    # Ingresos sin tipo asignado (huerfanos): "Sin clasificar"
    sin_tipo = ingresos_por_tipo.get(None, [])
    if sin_tipo:
        items_st = [
            ItemPlanilla(
                id=t.id, concepto=t.concepto, monto=_to_float(t.monto),
                fecha=t.fecha,
                referencia=t.proyecto.nombre if t.proyecto else None,
            )
            for t in sin_tipo
        ]
        planillas_ingresos.append(PlanillaIngresos(
            tipo_id=None,
            nombre="Sin clasificar",
            color="#94A3B8",
            total=sum(i.monto for i in items_st),
            cantidad=len(items_st),
            items=items_st,
        ))

    total_ingresos = sum(p.total for p in planillas_ingresos)

    # --- Planillas de gastos ---
    gastos = [t for t in txs if _enum_value(t.tipo) == TipoTransaccion.EGRESO.value]
    gastos_por_cat: dict[Optional[UUID], list[Transaccion]] = {}
    for g in gastos:
        gastos_por_cat.setdefault(g.categoria_id, []).append(g)

    categorias_map = {
        c.id: c.nombre
        for c in db.query(CategoriaGasto).filter(CategoriaGasto.activo == True).all()
    }

    planillas_gastos: List[PlanillaGastos] = []
    for cat_id, lista in gastos_por_cat.items():
        nombre = categorias_map.get(cat_id, "Sin categoria")
        items = [
            ItemPlanilla(
                id=t.id,
                concepto=t.concepto,
                monto=_to_float(t.monto),
                fecha=t.fecha,
                referencia=t.proyecto.nombre if t.proyecto else None,
            )
            for t in lista
        ]
        planillas_gastos.append(PlanillaGastos(
            categoria_id=cat_id,
            categoria=nombre,
            total=sum(i.monto for i in items),
            cantidad=len(items),
            items=items,
        ))
    planillas_gastos.sort(key=lambda p: p.total, reverse=True)
    total_gastos = sum(p.total for p in planillas_gastos)

    # --- Ganancia y distribucion por socio ---
    ganancia = total_ingresos - total_gastos

    socios = listar_socios(db)
    total_participacion = sum(_to_float(s.porcentaje_participacion) for s in socios) or 100.0

    retiros_periodo = listar_retiros(db, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    retiros_por_socio: dict[UUID, list[RetiroSocio]] = {}
    for r in retiros_periodo:
        retiros_por_socio.setdefault(r.socio_id, []).append(r)

    saldos: List[SaldoSocio] = []
    for socio in socios:
        pct = _to_float(socio.porcentaje_participacion) / total_participacion * 100
        ganancia_asignada = ganancia * (pct / 100)

        retiros_socio = retiros_por_socio.get(socio.id, [])
        total_retiros = sum(_to_float(r.monto) for r in retiros_socio)

        retiros_items = [
            ItemPlanilla(
                id=r.id,
                concepto=r.concepto or "Retiro",
                monto=_to_float(r.monto),
                fecha=r.fecha,
                referencia=r.cuenta.nombre if r.cuenta else None,
            )
            for r in retiros_socio
        ]

        saldos.append(SaldoSocio(
            socio_id=socio.id,
            nombre=f"{socio.nombre} {socio.apellido or ''}".strip(),
            porcentaje_participacion=_to_float(socio.porcentaje_participacion),
            ganancia_asignada=ganancia_asignada,
            total_retiros=total_retiros,
            saldo_disponible=ganancia_asignada - total_retiros,
            retiros=retiros_items,
        ))

    return ResumenPanelSocios(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        total_ingresos=total_ingresos,
        planillas_ingresos=planillas_ingresos,
        total_gastos=total_gastos,
        planillas_gastos=planillas_gastos,
        ganancia=ganancia,
        socios=saldos,
    )


# ============ SEEDS ============

_CATEGORIAS_ADICIONALES = [
    ("Sueldos", "Sueldos, jornales y cargas sociales", "#0EA5E9"),
    ("Impuestos", "Impuestos municipales, provinciales y nacionales", "#DC2626"),
    ("IVA", "IVA a pagar / retenciones", "#F59E0B"),
    ("Vehiculos", "Mantenimiento, patente y seguro de vehiculos", "#7C3AED"),
    ("Gastos diarios", "Gastos varios del dia a dia", "#64748B"),
]


def inicializar_categorias_socios(db: Session) -> None:
    """Crea las categorias de gasto adicionales requeridas por el panel de socios."""
    for nombre, descripcion, color in _CATEGORIAS_ADICIONALES:
        existe = db.query(CategoriaGasto).filter(CategoriaGasto.nombre == nombre).first()
        if not existe:
            db.add(CategoriaGasto(nombre=nombre, descripcion=descripcion, color=color))
    db.commit()


def inicializar_socios_default(db: Session) -> None:
    """Crea Socio A y Socio B por defecto si no hay socios."""
    if db.query(Socio).count() > 0:
        return
    db.add(Socio(nombre="Socio A", porcentaje_participacion=50))
    db.add(Socio(nombre="Socio B", porcentaje_participacion=50))
    db.commit()


_TIPOS_INGRESO_DEFAULT = [
    ("Cobro factura obras", "#22C55E", 1, False),
    ("Cobro factura ventas", "#3B82F6", 2, False),
    ("Aportes de socios", "#8B5CF6", 3, True),
    ("Otros ingresos", "#94A3B8", 4, False),
]


def inicializar_tipos_ingreso_default(db: Session) -> None:
    """Crea las 4 planillas de ingreso por defecto si no hay ninguna."""
    if db.query(TipoIngresoConfig).count() > 0:
        return
    for nombre, color, orden, es_aporte in _TIPOS_INGRESO_DEFAULT:
        db.add(TipoIngresoConfig(
            nombre=nombre, color=color, orden=orden, es_aporte_socio=es_aporte
        ))
    db.commit()
