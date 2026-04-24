"""
Endpoints para gestionar actividades de proyecto y avances.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario, RolUsuario
from app.services.pdf_service import generar_pdf_resumen_actividades
from app.schemas.proyecto_actividad import (
    ProyectoActividadCreate,
    ProyectoActividadUpdate,
    ProyectoActividadResponse,
    ProyectoActividadListResponse,
    AvanceActividadCreate,
    AvanceActividadUpdate,
    AvanceActividadResponse,
    AsignarActividadesRequest,
    AsignarHerramientasRequest,
    ProyectoHerramientaResponse,
    ResumenActividadesProyecto,
)
from app.services.proyecto_actividad_service import ProyectoActividadService
from app.services import proyecto_service

router = APIRouter()


# ============ Actividades de Proyecto ============

@router.get("/{proyecto_id}/actividades", response_model=List[ProyectoActividadListResponse])
def listar_actividades_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista todas las actividades de un proyecto con su avance."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    service = ProyectoActividadService(db)
    actividades = service.obtener_actividades_proyecto(proyecto_id)

    # Transformar respuesta
    result = []
    for actividad in actividades:
        result.append(ProyectoActividadListResponse(
            id=actividad.id,
            actividad_tipo_id=actividad.actividad_tipo_id,
            actividad_codigo=actividad.actividad_tipo.codigo if actividad.actividad_tipo else "",
            actividad_nombre=actividad.actividad_tipo.nombre if actividad.actividad_tipo else "",
            actividad_categoria=actividad.actividad_tipo.categoria if actividad.actividad_tipo else "",
            unidad_trabajo=actividad.actividad_tipo.unidad_trabajo if actividad.actividad_tipo else "",
            cantidad_planificada=actividad.cantidad_planificada,
            cantidad_ejecutada=actividad.cantidad_ejecutada,
            porcentaje_avance=actividad.porcentaje_avance,
            orden=actividad.orden
        ))

    return result


@router.post("/{proyecto_id}/actividades", response_model=ProyectoActividadResponse, status_code=status.HTTP_201_CREATED)
def asignar_actividad(
    proyecto_id: UUID,
    actividad_data: ProyectoActividadCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Asigna una actividad tipo a un proyecto."""
    try:
        service = ProyectoActividadService(db)
        actividad = service.crear_actividad_proyecto(proyecto_id, actividad_data)

        return ProyectoActividadResponse(
            id=actividad.id,
            proyecto_id=actividad.proyecto_id,
            actividad_tipo_id=actividad.actividad_tipo_id,
            cantidad_planificada=actividad.cantidad_planificada,
            cantidad_ejecutada=actividad.cantidad_ejecutada,
            orden=actividad.orden,
            observaciones=actividad.observaciones,
            materiales_calculados=actividad.materiales_calculados,
            porcentaje_avance=actividad.porcentaje_avance,
            cantidad_pendiente=actividad.cantidad_pendiente,
            activo=actividad.activo,
            created_at=actividad.created_at,
            actividad_codigo=actividad.actividad_tipo.codigo if actividad.actividad_tipo else None,
            actividad_nombre=actividad.actividad_tipo.nombre if actividad.actividad_tipo else None,
            actividad_categoria=actividad.actividad_tipo.categoria if actividad.actividad_tipo else None,
            unidad_trabajo=actividad.actividad_tipo.unidad_trabajo if actividad.actividad_tipo else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{proyecto_id}/actividades/bulk", response_model=List[ProyectoActividadResponse], status_code=status.HTTP_201_CREATED)
def asignar_actividades_bulk(
    proyecto_id: UUID,
    request: AsignarActividadesRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Asigna múltiples actividades tipo a un proyecto."""
    try:
        service = ProyectoActividadService(db)
        actividades = []
        for actividad_data in request.actividades:
            actividad = service.crear_actividad_proyecto(proyecto_id, actividad_data)
            actividades.append(actividad)

        return [
            ProyectoActividadResponse(
                id=a.id,
                proyecto_id=a.proyecto_id,
                actividad_tipo_id=a.actividad_tipo_id,
                cantidad_planificada=a.cantidad_planificada,
                cantidad_ejecutada=a.cantidad_ejecutada,
                orden=a.orden,
                observaciones=a.observaciones,
                materiales_calculados=a.materiales_calculados,
                porcentaje_avance=a.porcentaje_avance,
                cantidad_pendiente=a.cantidad_pendiente,
                activo=a.activo,
                created_at=a.created_at,
                actividad_codigo=a.actividad_tipo.codigo if a.actividad_tipo else None,
                actividad_nombre=a.actividad_tipo.nombre if a.actividad_tipo else None,
                actividad_categoria=a.actividad_tipo.categoria if a.actividad_tipo else None,
                unidad_trabajo=a.actividad_tipo.unidad_trabajo if a.actividad_tipo else None
            )
            for a in actividades
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{proyecto_id}/actividades/{actividad_id}", response_model=ProyectoActividadResponse)
def obtener_actividad_proyecto(
    proyecto_id: UUID,
    actividad_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Obtiene detalle de una actividad de proyecto."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    service = ProyectoActividadService(db)
    actividad = service.obtener_actividad(actividad_id)

    if not actividad or actividad.proyecto_id != proyecto_id:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    return ProyectoActividadResponse(
        id=actividad.id,
        proyecto_id=actividad.proyecto_id,
        actividad_tipo_id=actividad.actividad_tipo_id,
        cantidad_planificada=actividad.cantidad_planificada,
        cantidad_ejecutada=actividad.cantidad_ejecutada,
        orden=actividad.orden,
        observaciones=actividad.observaciones,
        materiales_calculados=actividad.materiales_calculados,
        porcentaje_avance=actividad.porcentaje_avance,
        cantidad_pendiente=actividad.cantidad_pendiente,
        activo=actividad.activo,
        created_at=actividad.created_at,
        actividad_codigo=actividad.actividad_tipo.codigo if actividad.actividad_tipo else None,
        actividad_nombre=actividad.actividad_tipo.nombre if actividad.actividad_tipo else None,
        actividad_categoria=actividad.actividad_tipo.categoria if actividad.actividad_tipo else None,
        unidad_trabajo=actividad.actividad_tipo.unidad_trabajo if actividad.actividad_tipo else None
    )


@router.put("/{proyecto_id}/actividades/{actividad_id}", response_model=ProyectoActividadResponse)
def actualizar_actividad_proyecto(
    proyecto_id: UUID,
    actividad_id: UUID,
    actividad_data: ProyectoActividadUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza una actividad de proyecto (cantidad, orden, observaciones)."""
    try:
        service = ProyectoActividadService(db)
        actividad = service.actualizar_actividad(actividad_id, actividad_data)

        if actividad.proyecto_id != proyecto_id:
            raise HTTPException(status_code=400, detail="La actividad no pertenece a este proyecto")

        return ProyectoActividadResponse(
            id=actividad.id,
            proyecto_id=actividad.proyecto_id,
            actividad_tipo_id=actividad.actividad_tipo_id,
            cantidad_planificada=actividad.cantidad_planificada,
            cantidad_ejecutada=actividad.cantidad_ejecutada,
            orden=actividad.orden,
            observaciones=actividad.observaciones,
            materiales_calculados=actividad.materiales_calculados,
            porcentaje_avance=actividad.porcentaje_avance,
            cantidad_pendiente=actividad.cantidad_pendiente,
            activo=actividad.activo,
            created_at=actividad.created_at,
            actividad_codigo=actividad.actividad_tipo.codigo if actividad.actividad_tipo else None,
            actividad_nombre=actividad.actividad_tipo.nombre if actividad.actividad_tipo else None,
            actividad_categoria=actividad.actividad_tipo.categoria if actividad.actividad_tipo else None,
            unidad_trabajo=actividad.actividad_tipo.unidad_trabajo if actividad.actividad_tipo else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{proyecto_id}/actividades/{actividad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_actividad_proyecto(
    proyecto_id: UUID,
    actividad_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina una actividad de proyecto."""
    service = ProyectoActividadService(db)
    actividad = service.obtener_actividad(actividad_id)

    if not actividad or actividad.proyecto_id != proyecto_id:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    if not service.eliminar_actividad(actividad_id):
        raise HTTPException(status_code=400, detail="No se pudo eliminar la actividad")


# ============ Avances ============

@router.get("/{proyecto_id}/actividades/{actividad_id}/avances", response_model=List[AvanceActividadResponse])
def listar_avances(
    proyecto_id: UUID,
    actividad_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista los avances de una actividad."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    service = ProyectoActividadService(db)
    actividad = service.obtener_actividad(actividad_id)

    if not actividad or actividad.proyecto_id != proyecto_id:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    avances = service.obtener_avances_actividad(actividad_id)

    return [
        AvanceActividadResponse(
            id=a.id,
            proyecto_actividad_id=a.proyecto_actividad_id,
            fecha=a.fecha,
            cantidad=a.cantidad,
            observaciones=a.observaciones,
            materiales_consumidos=a.materiales_consumidos,
            registrado_por_id=a.registrado_por_id,
            registrado_por_nombre=a.registrado_por.nombre if a.registrado_por else None,
            created_at=a.created_at
        )
        for a in avances
    ]


@router.post("/{proyecto_id}/actividades/{actividad_id}/avances", response_model=AvanceActividadResponse, status_code=status.HTTP_201_CREATED)
def registrar_avance(
    proyecto_id: UUID,
    actividad_id: UUID,
    avance_data: AvanceActividadCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Registra un avance en una actividad (operarios, supervisores, admin)."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    try:
        service = ProyectoActividadService(db)
        actividad = service.obtener_actividad(actividad_id)

        if not actividad or actividad.proyecto_id != proyecto_id:
            raise HTTPException(status_code=404, detail="Actividad no encontrada")

        avance = service.registrar_avance(actividad_id, avance_data, usuario.id)

        return AvanceActividadResponse(
            id=avance.id,
            proyecto_actividad_id=avance.proyecto_actividad_id,
            fecha=avance.fecha,
            cantidad=avance.cantidad,
            observaciones=avance.observaciones,
            materiales_consumidos=avance.materiales_consumidos,
            registrado_por_id=avance.registrado_por_id,
            registrado_por_nombre=usuario.nombre,
            created_at=avance.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{proyecto_id}/actividades/{actividad_id}/avances/{avance_id}", response_model=AvanceActividadResponse)
def actualizar_avance(
    proyecto_id: UUID,
    actividad_id: UUID,
    avance_id: UUID,
    avance_data: AvanceActividadUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Actualiza un registro de avance."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    try:
        service = ProyectoActividadService(db)
        avance = service.actualizar_avance(avance_id, avance_data)

        return AvanceActividadResponse(
            id=avance.id,
            proyecto_actividad_id=avance.proyecto_actividad_id,
            fecha=avance.fecha,
            cantidad=avance.cantidad,
            observaciones=avance.observaciones,
            materiales_consumidos=avance.materiales_consumidos,
            registrado_por_id=avance.registrado_por_id,
            registrado_por_nombre=avance.registrado_por.nombre if avance.registrado_por else None,
            created_at=avance.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{proyecto_id}/actividades/{actividad_id}/avances/{avance_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_avance(
    proyecto_id: UUID,
    actividad_id: UUID,
    avance_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina un avance (solo admin/supervisor)."""
    service = ProyectoActividadService(db)

    if not service.eliminar_avance(avance_id):
        raise HTTPException(status_code=404, detail="Avance no encontrado")


# ============ Resumen ============

@router.get("/{proyecto_id}/resumen-actividades", response_model=ResumenActividadesProyecto)
def obtener_resumen_actividades(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Obtiene un resumen de actividades y materiales del proyecto."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    service = ProyectoActividadService(db)
    return service.obtener_resumen_proyecto(proyecto_id)


@router.get("/{proyecto_id}/resumen-actividades/pdf")
def descargar_resumen_pdf(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Descarga el resumen de actividades y materiales en PDF."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    # Obtener datos del proyecto
    proyecto = proyecto_service.obtener_proyecto(db, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Obtener actividades y resumen
    service = ProyectoActividadService(db)
    actividades = service.obtener_actividades_proyecto(proyecto_id)
    resumen = service.obtener_resumen_proyecto(proyecto_id)

    # Preparar datos para el PDF
    datos = {
        'proyecto': {
            'nombre': proyecto.nombre,
            'ubicacion': proyecto.ubicacion,
            'fecha_inicio': proyecto.fecha_inicio.strftime('%d/%m/%Y') if proyecto.fecha_inicio else None,
            'cliente_nombre': proyecto.cliente.nombre if proyecto.cliente else None,
        },
        'actividades': [
            {
                'actividad_codigo': a.actividad_tipo.codigo if a.actividad_tipo else '',
                'actividad_nombre': a.actividad_tipo.nombre if a.actividad_tipo else '',
                'actividad_categoria': a.actividad_tipo.categoria if a.actividad_tipo else '',
                'unidad_trabajo': a.actividad_tipo.unidad_trabajo if a.actividad_tipo else '',
                'cantidad_planificada': float(a.cantidad_planificada),
                'cantidad_ejecutada': float(a.cantidad_ejecutada),
                'porcentaje_avance': float(a.porcentaje_avance),
            }
            for a in actividades
        ],
        'resumen': {
            'total_actividades': resumen.total_actividades,
            'actividades_completadas': resumen.actividades_completadas,
            'actividades_en_progreso': resumen.actividades_en_progreso,
            'actividades_pendientes': resumen.actividades_pendientes,
            'porcentaje_avance_global': float(resumen.porcentaje_avance_global),
        },
        'materiales_totales': [
            {
                'material_nombre': m.material_nombre,
                'cantidad_total': float(m.cantidad_total),
                'unidad': m.unidad,
            }
            for m in resumen.materiales_totales
        ]
    }

    # Generar PDF
    pdf_bytes = generar_pdf_resumen_actividades(datos)

    # Nombre del archivo
    nombre_limpio = proyecto.nombre.replace(' ', '_').replace('/', '-')[:30]
    filename = f"resumen_actividades_{nombre_limpio}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# ============ Herramientas ============

@router.get("/{proyecto_id}/herramientas", response_model=List[ProyectoHerramientaResponse])
def listar_herramientas_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista las herramientas asignadas a un proyecto."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    service = ProyectoActividadService(db)
    herramientas = service.obtener_herramientas_proyecto(proyecto_id)

    return [
        ProyectoHerramientaResponse(
            id=h.id,
            proyecto_id=h.proyecto_id,
            herramienta_id=h.herramienta_id,
            herramienta_nombre=h.herramienta.nombre if h.herramienta else None,
            herramienta_codigo=None,  # Herramienta no tiene campo codigo
            fecha_asignacion=h.fecha_asignacion,
            observaciones=h.observaciones,
            activo=h.activo
        )
        for h in herramientas
    ]


@router.post("/{proyecto_id}/herramientas/bulk", response_model=List[ProyectoHerramientaResponse], status_code=status.HTTP_201_CREATED)
def asignar_herramientas_bulk(
    proyecto_id: UUID,
    request: AsignarHerramientasRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Asigna múltiples herramientas a un proyecto."""
    try:
        service = ProyectoActividadService(db)
        herramientas = service.asignar_herramientas_bulk(proyecto_id, request.herramientas_ids)

        return [
            ProyectoHerramientaResponse(
                id=h.id,
                proyecto_id=h.proyecto_id,
                herramienta_id=h.herramienta_id,
                herramienta_nombre=h.herramienta.nombre if h.herramienta else None,
                herramienta_codigo=None,  # Herramienta no tiene campo codigo
                fecha_asignacion=h.fecha_asignacion,
                observaciones=h.observaciones,
                activo=h.activo
            )
            for h in herramientas
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{proyecto_id}/herramientas/{herramienta_id}", status_code=status.HTTP_204_NO_CONTENT)
def desasignar_herramienta(
    proyecto_id: UUID,
    herramienta_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Desasigna una herramienta de un proyecto."""
    service = ProyectoActividadService(db)

    if not service.desasignar_herramienta(proyecto_id, herramienta_id):
        raise HTTPException(status_code=404, detail="Herramienta no asignada a este proyecto")
