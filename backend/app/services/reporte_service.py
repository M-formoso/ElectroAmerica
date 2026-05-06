from sqlalchemy.orm import Session
from sqlalchemy import or_
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

        items_data = []
        for item in items:
            porcentaje_item = 0
            if item.cantidad_estimada and float(item.cantidad_estimada) > 0:
                porcentaje_item = (float(item.cantidad_ejecutada) / float(item.cantidad_estimada)) * 100

            items_data.append({
                "id": str(item.id),
                "nombre": item.nombre,
                "descripcion": item.descripcion,
                "unidad": item.unidad,
                "cantidad_estimada": float(item.cantidad_estimada),
                "cantidad_ejecutada": float(item.cantidad_ejecutada),
                "porcentaje": round(porcentaje_item, 1),
                "precio_unitario": float(item.precio_unitario) if item.precio_unitario else None,
            })

        etapas_data.append({
            "id": str(etapa.id),
            "nombre": etapa.nombre,
            "descripcion": etapa.descripcion,
            "estado": etapa.estado.value,
            "porcentaje_avance": float(etapa.porcentaje_avance),
            "fecha_inicio_est": etapa.fecha_inicio_est.isoformat() if etapa.fecha_inicio_est else None,
            "fecha_fin_est": etapa.fecha_fin_est.isoformat() if etapa.fecha_fin_est else None,
            "fecha_inicio_real": etapa.fecha_inicio_real.isoformat() if etapa.fecha_inicio_real else None,
            "fecha_fin_real": etapa.fecha_fin_real.isoformat() if etapa.fecha_fin_real else None,
            "items": items_data,
            "items_total": len(items),
        })

    # Materiales utilizados en el período
    materiales = db.query(AsignacionMaterial).filter(
        AsignacionMaterial.proyecto_id == proyecto_id,
        AsignacionMaterial.fecha_asignacion >= fecha_desde,
        AsignacionMaterial.fecha_asignacion <= fecha_hasta,
        AsignacionMaterial.activo == True
    ).all()

    materiales_data = []
    for m in materiales:
        costo = None
        if m.material and m.material.precio_unitario:
            costo = float(m.cantidad) * float(m.material.precio_unitario)

        materiales_data.append({
            "nombre": m.material.nombre if m.material else "N/A",
            "codigo": m.material.codigo if m.material else "",
            "cantidad": float(m.cantidad),
            "unidad": m.material.unidad if m.material else "",
            "fecha": m.fecha_asignacion.isoformat(),
            "etapa": m.etapa.nombre if m.etapa else "General",
            "notas": m.notas,
            "costo_estimado": costo,
        })

    total_costo_materiales = sum(m["costo_estimado"] or 0 for m in materiales_data)

    # Equipos asignados en el período
    equipos = db.query(AsignacionEquipo).filter(
        AsignacionEquipo.proyecto_id == proyecto_id,
        AsignacionEquipo.fecha_asignacion <= fecha_hasta,
        or_(
            AsignacionEquipo.fecha_devolucion_real >= fecha_desde,
            AsignacionEquipo.fecha_devolucion_real.is_(None)
        ),
        AsignacionEquipo.activo == True
    ).all()

    equipos_data = []
    for e in equipos:
        equipos_data.append({
            "nombre": e.equipo.nombre if e.equipo else "N/A",
            "codigo": e.equipo.codigo if e.equipo else "",
            "tipo": e.equipo.tipo.value if e.equipo else "",
            "marca": e.equipo.marca if e.equipo else "",
            "modelo": e.equipo.modelo if e.equipo else "",
            "fecha_asignacion": e.fecha_asignacion.isoformat(),
            "fecha_devolucion_est": e.fecha_devolucion_est.isoformat() if e.fecha_devolucion_est else None,
            "fecha_devolucion_real": e.fecha_devolucion_real.isoformat() if e.fecha_devolucion_real else None,
            "notas": e.notas,
        })

    # Gastos del período
    gastos = db.query(Gasto).filter(
        Gasto.proyecto_id == proyecto_id,
        Gasto.fecha >= fecha_desde,
        Gasto.fecha <= fecha_hasta,
        Gasto.activo == True
    ).order_by(Gasto.fecha.desc()).all()

    total_gastos = sum(float(g.monto) for g in gastos)

    gastos_data = []
    gastos_por_categoria = {}
    for g in gastos:
        categoria_nombre = g.categoria.nombre if g.categoria else "Sin categoría"
        gastos_data.append({
            "id": str(g.id),
            "fecha": g.fecha.isoformat(),
            "categoria": categoria_nombre,
            "descripcion": g.descripcion,
            "monto": float(g.monto),
            "comprobante_url": g.comprobante_url,
            "numero_comprobante": g.numero_comprobante,
        })

        if categoria_nombre not in gastos_por_categoria:
            gastos_por_categoria[categoria_nombre] = 0
        gastos_por_categoria[categoria_nombre] += float(g.monto)

    # Fotos del período
    fotos = db.query(Foto).filter(
        Foto.proyecto_id == proyecto_id,
        Foto.fecha >= fecha_desde,
        Foto.fecha <= fecha_hasta,
        Foto.activo == True
    ).order_by(Foto.fecha.desc()).all()

    fotos_data = []
    for f in fotos:
        fotos_data.append({
            "id": str(f.id),
            "url": f.url,
            "thumbnail_url": f.thumbnail_url,
            "descripcion": f.descripcion,
            "fecha": f.fecha.isoformat(),
            "etapa": f.etapa.nombre if f.etapa else "General",
            "visible_cliente": f.visible_cliente,
        })

    # Cliente y supervisor
    cliente_data = None
    if proyecto.cliente:
        cliente_data = {
            "nombre": proyecto.cliente.nombre_display,
            "email": proyecto.cliente.email,
            "telefono": proyecto.cliente.telefono,
        }

    supervisor_data = None
    if proyecto.supervisor:
        supervisor_data = {
            "nombre": f"{proyecto.supervisor.nombre} {proyecto.supervisor.apellido}",
            "email": proyecto.supervisor.email,
            "telefono": proyecto.supervisor.telefono,
        }

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
            "fecha_fin_real": proyecto.fecha_fin_real.isoformat() if proyecto.fecha_fin_real else None,
            "monto_contratado": float(proyecto.monto_contratado) if proyecto.monto_contratado else None,
            "cliente": cliente_data,
            "supervisor": supervisor_data,
        },
        "periodo": {
            "desde": fecha_desde.isoformat(),
            "hasta": fecha_hasta.isoformat(),
        },
        "resumen": {
            "total_etapas": len(etapas_data),
            "etapas_completadas": len([e for e in etapas_data if e["estado"] == "completada"]),
            "total_materiales_asignados": len(materiales_data),
            "costo_materiales": total_costo_materiales,
            "total_equipos_usados": len(equipos_data),
            "total_gastos": total_gastos,
            "gastos_por_categoria": gastos_por_categoria,
            "total_fotos": len(fotos_data),
        },
        "etapas": etapas_data,
        "materiales": materiales_data,
        "equipos": equipos_data,
        "gastos": gastos_data,
        "fotos": fotos_data,
    }


def guardar_reporte(
    db: Session,
    proyecto_id: UUID,
    fecha_desde: date,
    fecha_hasta: date,
    pdf_url: Optional[str],
    excel_url: Optional[str],
    usuario_id: UUID,
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
        generado_por_id=usuario_id
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
