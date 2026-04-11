from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from uuid import UUID
from datetime import date
import json

from app.models.asignacion_diaria import AsignacionDiaria, EstadoAsignacion
from app.models.actividad_tipo import ActividadTipo, MaterialActividadTipo
from app.models.material import Material
from app.models.usuario import Usuario
from app.models.proyecto import Proyecto
from app.models.etapa import Etapa
from app.models.equipo import Equipo
from app.schemas.asignacion_diaria import (
    AsignacionDiariaCreate, AsignacionDiariaUpdate,
    AsignacionMasivaRequest, FiltrosAsignacion
)


# ============== ASIGNACIONES DIARIAS ==============

def get_asignacion(db: Session, asignacion_id: UUID) -> Optional[AsignacionDiaria]:
    """Obtiene una asignación por ID."""
    return db.query(AsignacionDiaria).filter(
        AsignacionDiaria.id == asignacion_id,
        AsignacionDiaria.activo == True
    ).first()


def get_asignaciones(
    db: Session,
    fecha: Optional[date] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    operario_id: Optional[UUID] = None,
    proyecto_id: Optional[UUID] = None,
    estado: Optional[EstadoAsignacion] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AsignacionDiaria]:
    """Obtiene asignaciones con filtros."""
    query = db.query(AsignacionDiaria).filter(AsignacionDiaria.activo == True)

    if fecha:
        query = query.filter(AsignacionDiaria.fecha == fecha)
    if fecha_desde:
        query = query.filter(AsignacionDiaria.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(AsignacionDiaria.fecha <= fecha_hasta)
    if operario_id:
        query = query.filter(AsignacionDiaria.operario_id == operario_id)
    if proyecto_id:
        query = query.filter(AsignacionDiaria.proyecto_id == proyecto_id)
    if estado:
        query = query.filter(AsignacionDiaria.estado == estado)

    return query.order_by(
        AsignacionDiaria.fecha.desc(),
        AsignacionDiaria.prioridad.desc()
    ).offset(skip).limit(limit).all()


def get_asignaciones_operario_fecha(
    db: Session,
    operario_id: UUID,
    fecha: date
) -> List[AsignacionDiaria]:
    """Obtiene las asignaciones de un operario para una fecha específica."""
    return db.query(AsignacionDiaria).filter(
        AsignacionDiaria.operario_id == operario_id,
        AsignacionDiaria.fecha == fecha,
        AsignacionDiaria.activo == True
    ).all()


def get_asignaciones_pendientes_operario(
    db: Session,
    operario_id: UUID
) -> List[AsignacionDiaria]:
    """Obtiene las asignaciones pendientes de un operario (planificadas o confirmadas)."""
    return db.query(AsignacionDiaria).filter(
        AsignacionDiaria.operario_id == operario_id,
        AsignacionDiaria.activo == True,
        AsignacionDiaria.estado.in_([EstadoAsignacion.planificada, EstadoAsignacion.confirmada])
    ).order_by(AsignacionDiaria.fecha, AsignacionDiaria.prioridad.desc()).all()


def create_asignacion(
    db: Session,
    asignacion: AsignacionDiariaCreate,
    creado_por_id: UUID
) -> AsignacionDiaria:
    """Crea una nueva asignación diaria."""
    # Convertir tareas y materiales a JSON
    tareas_json = [t.model_dump() for t in asignacion.tareas_planificadas] if asignacion.tareas_planificadas else None
    materiales_json = [m.model_dump() for m in asignacion.materiales_planificados] if asignacion.materiales_planificados else None

    # Convertir UUIDs a strings en el JSON
    if tareas_json:
        for t in tareas_json:
            if t.get('item_id'):
                t['item_id'] = str(t['item_id'])
            if t.get('actividad_tipo_id'):
                t['actividad_tipo_id'] = str(t['actividad_tipo_id'])

    if materiales_json:
        for m in materiales_json:
            if m.get('material_id'):
                m['material_id'] = str(m['material_id'])

    db_asignacion = AsignacionDiaria(
        fecha=asignacion.fecha,
        operario_id=asignacion.operario_id,
        proyecto_id=asignacion.proyecto_id,
        etapa_id=asignacion.etapa_id,
        vehiculo_id=asignacion.vehiculo_id,
        prioridad=asignacion.prioridad.value,
        notas=asignacion.notas,
        tareas_planificadas=tareas_json,
        materiales_planificados=materiales_json,
        creado_por_id=creado_por_id
    )
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion


def create_asignaciones_masivas(
    db: Session,
    request: AsignacionMasivaRequest,
    creado_por_id: UUID
) -> List[AsignacionDiaria]:
    """Crea múltiples asignaciones para una fecha."""
    asignaciones_creadas = []

    for item in request.asignaciones:
        asignacion_data = AsignacionDiariaCreate(
            fecha=request.fecha,
            operario_id=item.operario_id,
            proyecto_id=item.proyecto_id,
            etapa_id=item.etapa_id,
            vehiculo_id=item.vehiculo_id,
            prioridad=item.prioridad,
            notas=item.notas,
            tareas_planificadas=item.tareas_planificadas,
            materiales_planificados=item.materiales_planificados
        )
        asignacion = create_asignacion(db, asignacion_data, creado_por_id)
        asignaciones_creadas.append(asignacion)

    return asignaciones_creadas


def update_asignacion(
    db: Session,
    asignacion_id: UUID,
    asignacion: AsignacionDiariaUpdate
) -> Optional[AsignacionDiaria]:
    """Actualiza una asignación."""
    db_asignacion = get_asignacion(db, asignacion_id)
    if not db_asignacion:
        return None

    update_data = asignacion.model_dump(exclude_unset=True)

    # Procesar tareas y materiales si vienen en el update
    if 'tareas_planificadas' in update_data and update_data['tareas_planificadas']:
        tareas_json = [t.model_dump() if hasattr(t, 'model_dump') else t for t in update_data['tareas_planificadas']]
        for t in tareas_json:
            if t.get('item_id'):
                t['item_id'] = str(t['item_id'])
            if t.get('actividad_tipo_id'):
                t['actividad_tipo_id'] = str(t['actividad_tipo_id'])
        update_data['tareas_planificadas'] = tareas_json

    if 'materiales_planificados' in update_data and update_data['materiales_planificados']:
        materiales_json = [m.model_dump() if hasattr(m, 'model_dump') else m for m in update_data['materiales_planificados']]
        for m in materiales_json:
            if m.get('material_id'):
                m['material_id'] = str(m['material_id'])
        update_data['materiales_planificados'] = materiales_json

    if 'prioridad' in update_data and update_data['prioridad']:
        update_data['prioridad'] = update_data['prioridad'].value if hasattr(update_data['prioridad'], 'value') else update_data['prioridad']

    for field, value in update_data.items():
        if value is not None:
            setattr(db_asignacion, field, value)

    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion


def confirmar_asignacion(db: Session, asignacion_id: UUID) -> Optional[AsignacionDiaria]:
    """El operario confirma que vio/acepta la asignación."""
    db_asignacion = get_asignacion(db, asignacion_id)
    if not db_asignacion:
        return None

    if db_asignacion.estado == EstadoAsignacion.planificada:
        db_asignacion.estado = EstadoAsignacion.confirmada
        db.commit()
        db.refresh(db_asignacion)

    return db_asignacion


def cancelar_asignacion(db: Session, asignacion_id: UUID) -> Optional[AsignacionDiaria]:
    """Cancela una asignación."""
    db_asignacion = get_asignacion(db, asignacion_id)
    if not db_asignacion:
        return None

    db_asignacion.estado = EstadoAsignacion.cancelada
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion


def delete_asignacion(db: Session, asignacion_id: UUID) -> bool:
    """Elimina una asignación (soft delete)."""
    db_asignacion = get_asignacion(db, asignacion_id)
    if not db_asignacion:
        return False

    db_asignacion.activo = False
    db.commit()
    return True


# ============== HELPERS ==============

def enrich_asignacion_response(db: Session, asignacion: AsignacionDiaria) -> dict:
    """Enriquece una asignación con datos relacionados."""
    operario = db.query(Usuario).filter(Usuario.id == asignacion.operario_id).first()
    proyecto = db.query(Proyecto).filter(Proyecto.id == asignacion.proyecto_id).first()
    etapa = db.query(Etapa).filter(Etapa.id == asignacion.etapa_id).first() if asignacion.etapa_id else None
    vehiculo = db.query(Equipo).filter(Equipo.id == asignacion.vehiculo_id).first() if asignacion.vehiculo_id else None

    return {
        **asignacion.__dict__,
        "operario_nombre": f"{operario.nombre} {operario.apellido}" if operario else None,
        "proyecto_nombre": proyecto.nombre if proyecto else None,
        "etapa_nombre": etapa.nombre if etapa else None,
        "vehiculo_nombre": vehiculo.nombre if vehiculo else None,
        "vehiculo_patente": vehiculo.patente if vehiculo else None,
        "jornada_id": asignacion.jornada.id if asignacion.jornada else None,
        "jornada_estado": asignacion.jornada.estado.value if asignacion.jornada else None
    }


def get_resumen_asignaciones_dia(db: Session, fecha: date) -> dict:
    """Obtiene un resumen de las asignaciones de un día."""
    asignaciones = get_asignaciones(db, fecha=fecha, limit=1000)

    por_estado = {}
    por_proyecto = {}
    operarios = set()
    vehiculos = set()

    for a in asignaciones:
        # Por estado
        estado = a.estado.value
        por_estado[estado] = por_estado.get(estado, 0) + 1

        # Por proyecto
        if a.proyecto_id not in por_proyecto:
            proyecto = db.query(Proyecto).filter(Proyecto.id == a.proyecto_id).first()
            por_proyecto[a.proyecto_id] = {
                "proyecto_id": str(a.proyecto_id),
                "nombre": proyecto.nombre if proyecto else "Desconocido",
                "cantidad": 0
            }
        por_proyecto[a.proyecto_id]["cantidad"] += 1

        # Operarios y vehículos únicos
        operarios.add(a.operario_id)
        if a.vehiculo_id:
            vehiculos.add(a.vehiculo_id)

    return {
        "fecha": fecha,
        "total_asignaciones": len(asignaciones),
        "por_estado": por_estado,
        "por_proyecto": list(por_proyecto.values()),
        "operarios_asignados": len(operarios),
        "vehiculos_asignados": len(vehiculos)
    }
