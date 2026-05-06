from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa
from app.models.usuario import RolUsuario
from app.models.cliente import Cliente
from app.models.proyecto_actividad import ProyectoActividad, ProyectoHerramienta
from app.schemas.proyecto import ProyectoCreate, ProyectoUpdate
from app.schemas.proyecto_actividad import ProyectoActividadCreate


def obtener_proyectos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    estado: Optional[EstadoProyecto] = None,
    cliente_id: Optional[UUID] = None,
    solo_activos: bool = True
) -> List[Proyecto]:
    """Obtiene lista de proyectos con filtros opcionales."""
    query = db.query(Proyecto)

    if solo_activos:
        query = query.filter(Proyecto.activo == True)
    if estado:
        query = query.filter(Proyecto.estado == estado)
    if cliente_id:
        query = query.filter(Proyecto.cliente_id == cliente_id)

    return query.order_by(Proyecto.created_at.desc()).offset(skip).limit(limit).all()


def obtener_proyecto(db: Session, proyecto_id: UUID) -> Optional[Proyecto]:
    """Obtiene un proyecto por ID."""
    return db.query(Proyecto).filter(
        Proyecto.id == proyecto_id,
        Proyecto.activo == True
    ).first()


def crear_proyecto(
    db: Session,
    proyecto: ProyectoCreate,
    usuario_id: UUID
) -> Proyecto:
    """Crea un nuevo proyecto con actividades y herramientas opcionales."""
    db_proyecto = Proyecto(
        nombre=proyecto.nombre,
        descripcion=proyecto.descripcion,
        cliente_id=proyecto.cliente_id,
        ubicacion=proyecto.ubicacion,
        fecha_inicio=proyecto.fecha_inicio,
        fecha_fin_estimada=proyecto.fecha_fin_estimada,
        estado=proyecto.estado,
        monto_contratado=proyecto.monto_contratado,
        supervisor_id=usuario_id
    )
    db.add(db_proyecto)
    db.commit()
    db.refresh(db_proyecto)

    # Asignar actividades tipo si se proporcionaron
    if proyecto.actividades_tipo_ids:
        from app.services.proyecto_actividad_service import ProyectoActividadService
        actividad_service = ProyectoActividadService(db)
        actividad_service.asignar_actividades_bulk(db_proyecto.id, proyecto.actividades_tipo_ids)

    # Asignar herramientas si se proporcionaron
    if proyecto.herramientas_ids:
        from app.services.proyecto_actividad_service import ProyectoActividadService
        herramienta_service = ProyectoActividadService(db)
        herramienta_service.asignar_herramientas_bulk(db_proyecto.id, proyecto.herramientas_ids)

    db.refresh(db_proyecto)
    return db_proyecto


def actualizar_proyecto(
    db: Session,
    proyecto_id: UUID,
    proyecto: ProyectoUpdate
) -> Optional[Proyecto]:
    """Actualiza un proyecto existente."""
    db_proyecto = obtener_proyecto(db, proyecto_id)
    if not db_proyecto:
        return None

    update_data = proyecto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_proyecto, field, value)

    db.commit()
    db.refresh(db_proyecto)
    return db_proyecto


def eliminar_proyecto(db: Session, proyecto_id: UUID) -> bool:
    """Soft delete de proyecto."""
    proyecto = obtener_proyecto(db, proyecto_id)
    if not proyecto:
        return False

    proyecto.activo = False
    db.commit()
    return True


def recalcular_avance_proyecto(db: Session, proyecto_id: UUID) -> Decimal:
    """
    Recalcula el porcentaje de avance global del proyecto
    en base al promedio de sus etapas.
    """
    resultado = db.query(func.avg(Etapa.porcentaje_avance)).filter(
        Etapa.proyecto_id == proyecto_id,
        Etapa.activo == True
    ).scalar()

    avance = Decimal(resultado or 0).quantize(Decimal('0.01'))

    db.query(Proyecto).filter(Proyecto.id == proyecto_id).update({
        "porcentaje_avance": avance
    })
    db.commit()

    return avance


def obtener_estadisticas_proyecto(db: Session, proyecto_id: UUID) -> dict:
    """Obtiene estadísticas de un proyecto."""
    proyecto = obtener_proyecto(db, proyecto_id)
    if not proyecto:
        return {}

    total_etapas = len([e for e in proyecto.etapas if e.activo])
    etapas_completadas = len([
        e for e in proyecto.etapas
        if e.activo and e.estado.value == 'completada'
    ])

    return {
        "total_etapas": total_etapas,
        "etapas_completadas": etapas_completadas,
        "porcentaje_avance": float(proyecto.porcentaje_avance)
    }


def verificar_acceso_proyecto(
    db: Session,
    proyecto_id: UUID,
    usuario_id: UUID,
    rol: RolUsuario
) -> bool:
    """Verifica si un usuario tiene acceso a un proyecto."""
    proyecto = obtener_proyecto(db, proyecto_id)
    if not proyecto:
        return False

    # Admin y supervisor tienen acceso a todo
    if rol in [RolUsuario.administrador, RolUsuario.supervisor, RolUsuario.operario]:
        return True

    # Cliente solo a sus proyectos: cliente_id en proyectos es FK a clientes,
    # asi que tenemos que buscar el Cliente asociado al usuario.
    if rol == RolUsuario.cliente:
        cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario_id).first()
        if not cliente:
            return False
        return proyecto.cliente_id == cliente.id

    return False
