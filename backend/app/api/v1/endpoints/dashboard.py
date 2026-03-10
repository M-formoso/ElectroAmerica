from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date, timedelta
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa, EstadoEtapa
from app.models.material import Material
from app.models.equipo import Equipo, EstadoEquipo
from app.models.gasto import Gasto
from app.models.foto import Foto
from app.services import finanzas_service

router = APIRouter()


@router.get("/resumen")
def resumen_general(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Resumen general del día para el dashboard."""

    # Proyectos activos
    proyectos_activos = db.query(Proyecto).filter(
        Proyecto.activo == True,
        Proyecto.estado.in_([EstadoProyecto.en_ejecucion, EstadoProyecto.planificacion])
    ).count()

    # Proyectos por estado
    proyectos_por_estado_query = db.query(
        Proyecto.estado,
        func.count(Proyecto.id)
    ).filter(Proyecto.activo == True).group_by(Proyecto.estado).all()

    proyectos_por_estado = {
        estado.value: count for estado, count in proyectos_por_estado_query
    }

    # Materiales con stock bajo
    materiales_stock_bajo = db.query(Material).filter(
        Material.activo == True,
        Material.stock_actual <= Material.stock_minimo
    ).count()

    # Equipos por estado
    equipos_disponibles = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado == EstadoEquipo.disponible
    ).count()

    equipos_asignados = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado == EstadoEquipo.asignado
    ).count()

    equipos_mantenimiento = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado == EstadoEquipo.mantenimiento
    ).count()

    # Gastos del mes actual
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)
    gastos_mes = db.query(func.coalesce(func.sum(Gasto.monto), 0)).filter(
        Gasto.activo == True,
        Gasto.fecha >= primer_dia_mes
    ).scalar()

    # Gastos del mes anterior
    primer_dia_mes_anterior = (primer_dia_mes - timedelta(days=1)).replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes - timedelta(days=1)
    gastos_mes_anterior = db.query(func.coalesce(func.sum(Gasto.monto), 0)).filter(
        Gasto.activo == True,
        Gasto.fecha >= primer_dia_mes_anterior,
        Gasto.fecha <= ultimo_dia_mes_anterior
    ).scalar()

    # Calcular variación
    variacion = 0
    if gastos_mes_anterior and float(gastos_mes_anterior) > 0:
        variacion = round(
            ((float(gastos_mes) - float(gastos_mes_anterior)) / float(gastos_mes_anterior)) * 100,
            2
        )

    return {
        "proyectos": {
            "activos": proyectos_activos,
            "por_estado": proyectos_por_estado
        },
        "materiales": {
            "stock_bajo": materiales_stock_bajo
        },
        "equipos": {
            "disponibles": equipos_disponibles,
            "asignados": equipos_asignados,
            "mantenimiento": equipos_mantenimiento
        },
        "gastos": {
            "mes_actual": float(gastos_mes or 0),
            "mes_anterior": float(gastos_mes_anterior or 0),
            "variacion_porcentaje": variacion
        }
    }


@router.get("/alertas")
def obtener_alertas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene las alertas activas del sistema."""
    alertas = []

    # Materiales con stock bajo
    materiales_bajo = db.query(Material).filter(
        Material.activo == True,
        Material.stock_actual <= Material.stock_minimo
    ).all()

    for material in materiales_bajo:
        alertas.append({
            "tipo": "stock_bajo",
            "severidad": "warning",
            "mensaje": f"Stock bajo: {material.nombre} ({float(material.stock_actual)} {material.unidad})",
            "recurso_id": str(material.id),
            "recurso_tipo": "material"
        })

    # Etapas demoradas
    hoy = date.today()
    etapas_demoradas = db.query(Etapa).filter(
        Etapa.activo == True,
        Etapa.fecha_fin_est < hoy,
        Etapa.estado.notin_([EstadoEtapa.completada])
    ).all()

    for etapa in etapas_demoradas:
        dias_demora = (hoy - etapa.fecha_fin_est).days
        alertas.append({
            "tipo": "etapa_demorada",
            "severidad": "error" if dias_demora > 7 else "warning",
            "mensaje": f"Etapa demorada ({dias_demora} días): {etapa.nombre}",
            "recurso_id": str(etapa.id),
            "recurso_tipo": "etapa",
            "proyecto_id": str(etapa.proyecto_id)
        })

    # Equipos en mantenimiento
    equipos_mant = db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado == EstadoEquipo.mantenimiento
    ).all()

    for equipo in equipos_mant:
        alertas.append({
            "tipo": "equipo_mantenimiento",
            "severidad": "info",
            "mensaje": f"Equipo en mantenimiento: {equipo.nombre}",
            "recurso_id": str(equipo.id),
            "recurso_tipo": "equipo"
        })

    return alertas


@router.get("/proyectos-activos")
def proyectos_activos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Estado de todos los proyectos activos."""
    hoy = date.today()

    proyectos = db.query(Proyecto).filter(
        Proyecto.activo == True,
        Proyecto.estado.in_([EstadoProyecto.en_ejecucion, EstadoProyecto.planificacion])
    ).all()

    return [
        {
            "id": str(p.id),
            "nombre": p.nombre,
            "estado": p.estado.value,
            "porcentaje_avance": float(p.porcentaje_avance),
            "fecha_fin_estimada": p.fecha_fin_estimada.isoformat() if p.fecha_fin_estimada else None,
            "dias_restantes": (p.fecha_fin_estimada - hoy).days if p.fecha_fin_estimada else None
        }
        for p in proyectos
    ]


@router.get("/financiero")
def resumen_financiero(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """
    Resumen financiero para el dashboard.
    Solo admin y supervisor.
    """
    return finanzas_service.obtener_resumen_financiero_general(db)


@router.get("/ultimas-fotos")
def ultimas_fotos(
    limit: int = Query(6, le=20),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Últimas fotos subidas al sistema."""
    fotos = db.query(Foto).filter(
        Foto.activo == True
    ).order_by(Foto.created_at.desc()).limit(limit).all()

    return [
        {
            "id": str(f.id),
            "url": f.url,
            "descripcion": f.descripcion,
            "fecha": f.fecha.isoformat(),
            "proyecto_id": str(f.proyecto_id),
            "proyecto_nombre": f.proyecto.nombre if f.proyecto else None
        }
        for f in fotos
    ]


@router.get("/actividad-reciente")
def actividad_reciente(
    limit: int = Query(10, le=30),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Actividad reciente del sistema."""
    actividades = []

    # Últimos gastos
    gastos = db.query(Gasto).filter(Gasto.activo == True).order_by(
        Gasto.created_at.desc()
    ).limit(5).all()

    for g in gastos:
        actividades.append({
            "tipo": "gasto",
            "mensaje": f"Gasto registrado: {g.descripcion[:50]}",
            "monto": float(g.monto),
            "fecha": g.created_at.isoformat(),
            "usuario": g.creador.nombre if g.creador else None
        })

    # Últimas fotos
    fotos = db.query(Foto).filter(Foto.activo == True).order_by(
        Foto.created_at.desc()
    ).limit(5).all()

    for f in fotos:
        actividades.append({
            "tipo": "foto",
            "mensaje": f"Foto subida: {f.descripcion or 'Sin descripción'}",
            "fecha": f.created_at.isoformat(),
            "proyecto": f.proyecto.nombre if f.proyecto else None
        })

    # Ordenar por fecha
    actividades.sort(key=lambda x: x['fecha'], reverse=True)

    return actividades[:limit]
