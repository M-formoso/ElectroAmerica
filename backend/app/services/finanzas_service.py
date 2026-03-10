from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa
from app.models.item_trabajo import ItemTrabajo
from app.models.asignacion_material import AsignacionMaterial
from app.models.gasto import Gasto
from app.models.precio_item import PrecioItem
from app.schemas.finanzas import (
    ResumenFinancieroProyecto,
    ResumenCostosEtapa,
    ResumenFinancieroGeneral
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
