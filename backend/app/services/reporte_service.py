from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.models.proyecto import Proyecto
from app.models.etapa import Etapa
from app.models.item_trabajo import ItemTrabajo
from app.models.asignacion_material import AsignacionMaterial
from app.models.asignacion_equipo import AsignacionEquipo
from app.models.gasto import Gasto
from app.models.foto import Foto
from app.models.reporte import Reporte


def obtener_datos_reporte(
    db: Session,
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date
) -> Optional[dict]:
    """Recopila todos los datos necesarios para generar el reporte."""
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        return None

    # Etapas con sus ítems
    etapas = db.query(Etapa).filter(
        Etapa.proyecto_id == proyecto_id,
        Etapa.activo == True
    ).order_by(Etapa.orden).all()

    etapas_data = []
    for etapa in etapas:
        items = db.query(ItemTrabajo).filter(
            ItemTrabajo.etapa_id == etapa.id,
            ItemTrabajo.activo == True
        ).all()

        items_completados = len([i for i in items if i.estado.value == 'completado'])

        etapas_data.append({
            "id": str(etapa.id),
            "nombre": etapa.nombre,
            "estado": etapa.estado.value,
            "porcentaje_avance": float(etapa.porcentaje_avance),
            "items_total": len(items),
            "items_completados": items_completados,
        })

    # Materiales utilizados en el período
    materiales = db.query(AsignacionMaterial).filter(
        AsignacionMaterial.proyecto_id == proyecto_id,
        AsignacionMaterial.fecha >= fecha_desde,
        AsignacionMaterial.fecha <= fecha_hasta
    ).all()

    materiales_data = [
        {
            "nombre": m.material.nombre if m.material else "N/A",
            "cantidad": float(m.cantidad),
            "unidad": m.material.unidad if m.material else "",
            "fecha": m.fecha.isoformat(),
        }
        for m in materiales
    ]

    # Equipos asignados en el período
    from sqlalchemy import or_
    equipos = db.query(AsignacionEquipo).filter(
        AsignacionEquipo.proyecto_id == proyecto_id,
        AsignacionEquipo.fecha_desde <= fecha_hasta,
        or_(
            AsignacionEquipo.fecha_hasta >= fecha_desde,
            AsignacionEquipo.fecha_hasta.is_(None)
        )
    ).all()

    equipos_data = [
        {
            "nombre": e.equipo.nombre if e.equipo else "N/A",
            "tipo": e.equipo.tipo.value if e.equipo else "",
            "fecha_desde": e.fecha_desde.isoformat(),
            "fecha_hasta": e.fecha_hasta.isoformat() if e.fecha_hasta else "En uso",
        }
        for e in equipos
    ]

    # Gastos del período
    gastos = db.query(Gasto).filter(
        Gasto.proyecto_id == proyecto_id,
        Gasto.fecha >= fecha_desde,
        Gasto.fecha <= fecha_hasta,
        Gasto.activo == True
    ).all()

    total_gastos = sum(float(g.monto) for g in gastos)

    gastos_data = [
        {
            "fecha": g.fecha.isoformat(),
            "categoria": g.categoria,
            "descripcion": g.descripcion,
            "monto": float(g.monto),
        }
        for g in gastos
    ]

    # Fotos del período
    fotos = db.query(Foto).filter(
        Foto.proyecto_id == proyecto_id,
        Foto.fecha >= fecha_desde,
        Foto.fecha <= fecha_hasta,
        Foto.activo == True
    ).order_by(Foto.fecha.desc()).limit(10).all()

    fotos_data = [
        {
            "url": f.url,
            "descripcion": f.descripcion,
            "fecha": f.fecha.isoformat(),
        }
        for f in fotos
    ]

    return {
        "proyecto": {
            "id": str(proyecto.id),
            "nombre": proyecto.nombre,
            "descripcion": proyecto.descripcion,
            "ubicacion": proyecto.ubicacion,
            "estado": proyecto.estado.value,
            "porcentaje_avance": float(proyecto.porcentaje_avance),
            "fecha_inicio": proyecto.fecha_inicio.isoformat() if proyecto.fecha_inicio else None,
            "fecha_fin_estimada": proyecto.fecha_fin_estimada.isoformat() if proyecto.fecha_fin_estimada else None,
        },
        "periodo": {
            "desde": fecha_desde.isoformat(),
            "hasta": fecha_hasta.isoformat(),
        },
        "etapas": etapas_data,
        "materiales": materiales_data,
        "equipos": equipos_data,
        "gastos": gastos_data,
        "total_gastos": total_gastos,
        "fotos": fotos_data,
    }


def guardar_reporte(
    db: Session,
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date,
    pdf_url: Optional[str],
    excel_url: Optional[str],
    usuario_id: Optional[UUID],
    tipo: str = "personalizado"
) -> Reporte:
    """Guarda un reporte en la base de datos."""
    reporte = Reporte(
        proyecto_id=proyecto_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo=tipo,
        pdf_url=pdf_url,
        excel_url=excel_url,
        created_by=usuario_id
    )
    db.add(reporte)
    db.commit()
    db.refresh(reporte)
    return reporte


def obtener_reportes_proyecto(
    db: Session,
    proyecto_id: UUID,
    limit: int = 20
) -> List[Reporte]:
    """Obtiene los reportes de un proyecto."""
    return db.query(Reporte).filter(
        Reporte.proyecto_id == proyecto_id,
        Reporte.activo == True
    ).order_by(Reporte.created_at.desc()).limit(limit).all()


def obtener_ultimo_reporte_semanal(
    db: Session,
    proyecto_id: UUID
) -> Optional[Reporte]:
    """Obtiene el último reporte semanal de un proyecto."""
    return db.query(Reporte).filter(
        Reporte.proyecto_id == proyecto_id,
        Reporte.tipo == "semanal",
        Reporte.activo == True
    ).order_by(Reporte.created_at.desc()).first()


def compartir_reporte_cliente(db: Session, reporte_id: UUID) -> Optional[Reporte]:
    """Marca un reporte como compartido con el cliente."""
    reporte = db.query(Reporte).filter(Reporte.id == reporte_id).first()
    if reporte:
        reporte.compartido_cliente = True
        db.commit()
        db.refresh(reporte)
    return reporte
