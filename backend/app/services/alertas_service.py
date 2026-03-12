from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal

from app.models.alerta import Alerta, TipoAlerta, PrioridadAlerta
from app.models.material import Material
from app.models.etapa import Etapa, EstadoEtapa
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.equipo import Equipo, EstadoEquipo
from app.models.cliente import Cliente
from app.models.usuario import Usuario, RolUsuario


# ============ CRUD ALERTAS ============

def get_alertas(
    db: Session,
    usuario_id: Optional[UUID] = None,
    solo_no_leidas: bool = False,
    solo_no_resueltas: bool = True,
    tipo: Optional[TipoAlerta] = None,
    prioridad: Optional[PrioridadAlerta] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Alerta]:
    """Obtiene alertas con filtros."""
    query = db.query(Alerta).filter(Alerta.activo == True)

    if usuario_id:
        # Alertas del usuario o alertas generales (sin usuario asignado)
        query = query.filter(
            (Alerta.usuario_id == usuario_id) | (Alerta.usuario_id.is_(None))
        )

    if solo_no_leidas:
        query = query.filter(Alerta.leida == False)

    if solo_no_resueltas:
        query = query.filter(Alerta.resuelta == False)

    if tipo:
        query = query.filter(Alerta.tipo == tipo.value)

    if prioridad:
        query = query.filter(Alerta.prioridad == prioridad.value)

    return query.order_by(Alerta.created_at.desc()).offset(skip).limit(limit).all()


def get_alerta(db: Session, alerta_id: UUID) -> Optional[Alerta]:
    """Obtiene una alerta por ID."""
    return db.query(Alerta).filter(
        Alerta.id == alerta_id,
        Alerta.activo == True
    ).first()


def crear_alerta(
    db: Session,
    tipo: TipoAlerta,
    titulo: str,
    mensaje: str,
    prioridad: PrioridadAlerta = PrioridadAlerta.MEDIA,
    referencia_tipo: Optional[str] = None,
    referencia_id: Optional[UUID] = None,
    usuario_id: Optional[UUID] = None
) -> Alerta:
    """Crea una nueva alerta."""
    # Verificar si ya existe una alerta similar no resuelta
    existe = db.query(Alerta).filter(
        Alerta.tipo == tipo.value,
        Alerta.referencia_tipo == referencia_tipo,
        Alerta.referencia_id == referencia_id,
        Alerta.resuelta == False,
        Alerta.activo == True
    ).first()

    if existe:
        return existe  # No duplicar alertas

    alerta = Alerta(
        tipo=tipo.value,
        prioridad=prioridad.value,
        titulo=titulo,
        mensaje=mensaje,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        usuario_id=usuario_id
    )
    db.add(alerta)
    db.commit()
    db.refresh(alerta)
    return alerta


def marcar_como_leida(db: Session, alerta_id: UUID) -> Optional[Alerta]:
    """Marca una alerta como leída."""
    alerta = get_alerta(db, alerta_id)
    if alerta:
        alerta.leida = True
        db.commit()
        db.refresh(alerta)
    return alerta


def marcar_todas_leidas(db: Session, usuario_id: UUID) -> int:
    """Marca todas las alertas de un usuario como leídas."""
    result = db.query(Alerta).filter(
        (Alerta.usuario_id == usuario_id) | (Alerta.usuario_id.is_(None)),
        Alerta.leida == False,
        Alerta.activo == True
    ).update({Alerta.leida: True})
    db.commit()
    return result


def resolver_alerta(db: Session, alerta_id: UUID, usuario_id: UUID) -> Optional[Alerta]:
    """Marca una alerta como resuelta."""
    from datetime import datetime
    alerta = get_alerta(db, alerta_id)
    if alerta:
        alerta.resuelta = True
        alerta.resuelto_por_id = usuario_id
        alerta.fecha_resolucion = datetime.now()
        db.commit()
        db.refresh(alerta)
    return alerta


def contar_alertas_no_leidas(db: Session, usuario_id: Optional[UUID] = None) -> int:
    """Cuenta las alertas no leídas."""
    query = db.query(func.count(Alerta.id)).filter(
        Alerta.leida == False,
        Alerta.resuelta == False,
        Alerta.activo == True
    )
    if usuario_id:
        query = query.filter(
            (Alerta.usuario_id == usuario_id) | (Alerta.usuario_id.is_(None))
        )
    return query.scalar() or 0


# ============ VERIFICACIONES AUTOMÁTICAS ============

def verificar_stock_minimo(db: Session) -> List[Alerta]:
    """Verifica materiales bajo stock mínimo y crea alertas."""
    alertas_creadas = []

    materiales_bajo_stock = db.query(Material).filter(
        Material.activo == True,
        Material.stock_actual <= Material.stock_minimo,
        Material.stock_minimo > 0
    ).all()

    for material in materiales_bajo_stock:
        # Determinar prioridad según qué tan bajo está el stock
        if material.stock_actual == 0:
            prioridad = PrioridadAlerta.CRITICA
        elif material.stock_actual <= material.stock_minimo * Decimal('0.5'):
            prioridad = PrioridadAlerta.ALTA
        else:
            prioridad = PrioridadAlerta.MEDIA

        alerta = crear_alerta(
            db,
            tipo=TipoAlerta.STOCK_MINIMO,
            titulo=f"Stock bajo: {material.nombre}",
            mensaje=f"El material '{material.nombre}' tiene stock actual de {material.stock_actual} {material.unidad or 'unidades'}. El stock mínimo es {material.stock_minimo}.",
            prioridad=prioridad,
            referencia_tipo="material",
            referencia_id=material.id
        )
        if alerta and not alerta.leida:  # Solo si es nueva
            alertas_creadas.append(alerta)

    return alertas_creadas


def verificar_demoras_etapas(db: Session) -> List[Alerta]:
    """Verifica etapas con demora y crea alertas."""
    alertas_creadas = []
    hoy = date.today()

    etapas_demoradas = db.query(Etapa).join(Proyecto).filter(
        Etapa.activo == True,
        Proyecto.activo == True,
        Proyecto.estado.in_([EstadoProyecto.en_ejecucion.value, EstadoProyecto.planificacion.value]),
        Etapa.estado.in_([EstadoEtapa.pendiente.value, EstadoEtapa.en_progreso.value]),
        Etapa.fecha_fin_est < hoy
    ).all()

    for etapa in etapas_demoradas:
        dias_demora = (hoy - etapa.fecha_fin_est).days

        if dias_demora > 14:
            prioridad = PrioridadAlerta.CRITICA
        elif dias_demora > 7:
            prioridad = PrioridadAlerta.ALTA
        else:
            prioridad = PrioridadAlerta.MEDIA

        alerta = crear_alerta(
            db,
            tipo=TipoAlerta.DEMORA_ETAPA,
            titulo=f"Etapa demorada: {etapa.nombre}",
            mensaje=f"La etapa '{etapa.nombre}' del proyecto '{etapa.proyecto.nombre}' tiene {dias_demora} días de demora. Fecha estimada fin: {etapa.fecha_fin_est}.",
            prioridad=prioridad,
            referencia_tipo="etapa",
            referencia_id=etapa.id
        )
        if alerta and not alerta.leida:
            alertas_creadas.append(alerta)

    return alertas_creadas


def verificar_equipos_mantenimiento(db: Session) -> List[Alerta]:
    """Verifica equipos que requieren mantenimiento."""
    alertas_creadas = []
    hoy = date.today()
    prox_semana = hoy + timedelta(days=7)

    # Por fecha de mantenimiento
    equipos_por_fecha = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.fecha_proximo_mantenimiento.isnot(None),
        Equipo.fecha_proximo_mantenimiento <= prox_semana
    ).all()

    for equipo in equipos_por_fecha:
        if equipo.fecha_proximo_mantenimiento <= hoy:
            prioridad = PrioridadAlerta.ALTA
            msg = f"El equipo '{equipo.nombre}' requiere mantenimiento inmediato (vencido)."
        else:
            prioridad = PrioridadAlerta.MEDIA
            dias = (equipo.fecha_proximo_mantenimiento - hoy).days
            msg = f"El equipo '{equipo.nombre}' requiere mantenimiento en {dias} días."

        alerta = crear_alerta(
            db,
            tipo=TipoAlerta.EQUIPO_MANTENIMIENTO,
            titulo=f"Mantenimiento: {equipo.nombre}",
            mensaje=msg,
            prioridad=prioridad,
            referencia_tipo="equipo",
            referencia_id=equipo.id
        )
        if alerta and not alerta.leida:
            alertas_creadas.append(alerta)

    # Por kilometraje
    equipos_por_km = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.km_actual.isnot(None),
        Equipo.km_proximo_service.isnot(None),
        Equipo.km_actual >= Equipo.km_proximo_service - 500
    ).all()

    for equipo in equipos_por_km:
        if equipo.km_actual >= equipo.km_proximo_service:
            prioridad = PrioridadAlerta.ALTA
            msg = f"El equipo '{equipo.nombre}' superó el kilometraje de service ({equipo.km_actual} km)."
        else:
            prioridad = PrioridadAlerta.MEDIA
            km_restantes = equipo.km_proximo_service - equipo.km_actual
            msg = f"El equipo '{equipo.nombre}' está a {km_restantes} km del próximo service."

        alerta = crear_alerta(
            db,
            tipo=TipoAlerta.EQUIPO_MANTENIMIENTO,
            titulo=f"Service por km: {equipo.nombre}",
            mensaje=msg,
            prioridad=prioridad,
            referencia_tipo="equipo",
            referencia_id=equipo.id
        )
        if alerta and not alerta.leida:
            alertas_creadas.append(alerta)

    return alertas_creadas


def verificar_limites_credito(db: Session) -> List[Alerta]:
    """Verifica clientes que superaron su límite de crédito."""
    alertas_creadas = []

    clientes = db.query(Cliente).filter(
        Cliente.activo == True,
        Cliente.limite_credito.isnot(None),
        Cliente.saldo_cuenta_corriente > Cliente.limite_credito
    ).all()

    for cliente in clientes:
        exceso = float(cliente.saldo_cuenta_corriente) - float(cliente.limite_credito)
        porcentaje = (float(cliente.saldo_cuenta_corriente) / float(cliente.limite_credito) * 100) - 100

        if porcentaje > 50:
            prioridad = PrioridadAlerta.CRITICA
        elif porcentaje > 25:
            prioridad = PrioridadAlerta.ALTA
        else:
            prioridad = PrioridadAlerta.MEDIA

        alerta = crear_alerta(
            db,
            tipo=TipoAlerta.LIMITE_CREDITO,
            titulo=f"Límite de crédito excedido: {cliente.razon_social}",
            mensaje=f"El cliente '{cliente.razon_social}' excedió su límite de crédito en ${exceso:.2f} ({porcentaje:.1f}% sobre el límite).",
            prioridad=prioridad,
            referencia_tipo="cliente",
            referencia_id=cliente.id
        )
        if alerta and not alerta.leida:
            alertas_creadas.append(alerta)

    return alertas_creadas


def verificar_proyectos_vencidos(db: Session) -> List[Alerta]:
    """Verifica proyectos que pasaron su fecha de fin estimada."""
    alertas_creadas = []
    hoy = date.today()

    proyectos = db.query(Proyecto).filter(
        Proyecto.activo == True,
        Proyecto.estado.in_([EstadoProyecto.en_ejecucion.value, EstadoProyecto.planificacion.value]),
        Proyecto.fecha_fin_estimada.isnot(None),
        Proyecto.fecha_fin_estimada < hoy
    ).all()

    for proyecto in proyectos:
        dias_demora = (hoy - proyecto.fecha_fin_estimada).days

        if dias_demora > 30:
            prioridad = PrioridadAlerta.CRITICA
        elif dias_demora > 14:
            prioridad = PrioridadAlerta.ALTA
        else:
            prioridad = PrioridadAlerta.MEDIA

        alerta = crear_alerta(
            db,
            tipo=TipoAlerta.PROYECTO_VENCIDO,
            titulo=f"Proyecto vencido: {proyecto.nombre}",
            mensaje=f"El proyecto '{proyecto.nombre}' tiene {dias_demora} días de demora sobre la fecha estimada de fin ({proyecto.fecha_fin_estimada}).",
            prioridad=prioridad,
            referencia_tipo="proyecto",
            referencia_id=proyecto.id
        )
        if alerta and not alerta.leida:
            alertas_creadas.append(alerta)

    return alertas_creadas


def ejecutar_todas_verificaciones(db: Session) -> dict:
    """Ejecuta todas las verificaciones y retorna resumen."""
    resultados = {
        "stock_minimo": len(verificar_stock_minimo(db)),
        "demoras_etapas": len(verificar_demoras_etapas(db)),
        "equipos_mantenimiento": len(verificar_equipos_mantenimiento(db)),
        "limites_credito": len(verificar_limites_credito(db)),
        "proyectos_vencidos": len(verificar_proyectos_vencidos(db)),
    }
    resultados["total"] = sum(resultados.values())
    return resultados


# ============ AUTO-RESOLVER ALERTAS ============

def auto_resolver_alertas_stock(db: Session):
    """Resuelve automáticamente alertas de stock cuando ya no aplican."""
    alertas = db.query(Alerta).filter(
        Alerta.tipo == TipoAlerta.STOCK_MINIMO.value,
        Alerta.resuelta == False,
        Alerta.activo == True
    ).all()

    for alerta in alertas:
        if alerta.referencia_id:
            material = db.query(Material).filter(Material.id == alerta.referencia_id).first()
            if material and material.stock_actual > material.stock_minimo:
                alerta.resuelta = True
                alerta.fecha_resolucion = func.now()

    db.commit()
