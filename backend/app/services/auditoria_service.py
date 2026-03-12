"""
Servicio de auditoría para registrar acciones de usuarios.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta

from app.models.auditoria import Auditoria, TipoAccion, ModuloAuditado
from app.models.usuario import Usuario


def registrar_accion(
    db: Session,
    usuario_id: Optional[UUID],
    accion: TipoAccion,
    modulo: ModuloAuditado,
    descripcion: str,
    recurso_id: Optional[UUID] = None,
    recurso_tipo: Optional[str] = None,
    datos_adicionales: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Auditoria:
    """
    Registra una acción de auditoría.

    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario que realizó la acción (None para acciones del sistema)
        accion: Tipo de acción realizada
        modulo: Módulo donde se realizó la acción
        descripcion: Descripción legible de la acción
        recurso_id: ID del recurso afectado
        recurso_tipo: Tipo del recurso afectado (ej: "proyecto", "material")
        datos_adicionales: Datos extra en formato dict
        ip_address: IP del usuario
        user_agent: User Agent del navegador

    Returns:
        Registro de auditoría creado
    """
    auditoria = Auditoria(
        usuario_id=usuario_id,
        accion=accion,
        modulo=modulo,
        descripcion=descripcion,
        recurso_id=recurso_id,
        recurso_tipo=recurso_tipo,
        datos_adicionales=datos_adicionales,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(auditoria)
    db.commit()
    db.refresh(auditoria)
    return auditoria


def get_auditorias(
    db: Session,
    usuario_id: Optional[UUID] = None,
    modulo: Optional[ModuloAuditado] = None,
    accion: Optional[TipoAccion] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    recurso_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Auditoria]:
    """
    Obtiene registros de auditoría con filtros.
    """
    query = db.query(Auditoria)

    if usuario_id:
        query = query.filter(Auditoria.usuario_id == usuario_id)
    if modulo:
        query = query.filter(Auditoria.modulo == modulo)
    if accion:
        query = query.filter(Auditoria.accion == accion)
    if fecha_desde:
        query = query.filter(func.date(Auditoria.created_at) >= fecha_desde)
    if fecha_hasta:
        query = query.filter(func.date(Auditoria.created_at) <= fecha_hasta)
    if recurso_id:
        query = query.filter(Auditoria.recurso_id == recurso_id)

    return query.order_by(Auditoria.created_at.desc()).offset(skip).limit(limit).all()


def get_auditoria_usuario(
    db: Session,
    usuario_id: UUID,
    limit: int = 50
) -> List[Auditoria]:
    """Obtiene los últimos registros de auditoría de un usuario."""
    return db.query(Auditoria).filter(
        Auditoria.usuario_id == usuario_id
    ).order_by(Auditoria.created_at.desc()).limit(limit).all()


def get_auditoria_recurso(
    db: Session,
    recurso_id: UUID,
    limit: int = 50
) -> List[Auditoria]:
    """Obtiene los registros de auditoría de un recurso específico."""
    return db.query(Auditoria).filter(
        Auditoria.recurso_id == recurso_id
    ).order_by(Auditoria.created_at.desc()).limit(limit).all()


def get_resumen_actividad(
    db: Session,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> Dict[str, Any]:
    """
    Obtiene un resumen de actividad del sistema.
    """
    if not fecha_desde:
        fecha_desde = date.today() - timedelta(days=30)
    if not fecha_hasta:
        fecha_hasta = date.today()

    # Total de acciones
    total_acciones = db.query(func.count(Auditoria.id)).filter(
        func.date(Auditoria.created_at) >= fecha_desde,
        func.date(Auditoria.created_at) <= fecha_hasta
    ).scalar()

    # Acciones por tipo
    acciones_por_tipo = db.query(
        Auditoria.accion,
        func.count(Auditoria.id).label('cantidad')
    ).filter(
        func.date(Auditoria.created_at) >= fecha_desde,
        func.date(Auditoria.created_at) <= fecha_hasta
    ).group_by(Auditoria.accion).all()

    # Acciones por módulo
    acciones_por_modulo = db.query(
        Auditoria.modulo,
        func.count(Auditoria.id).label('cantidad')
    ).filter(
        func.date(Auditoria.created_at) >= fecha_desde,
        func.date(Auditoria.created_at) <= fecha_hasta
    ).group_by(Auditoria.modulo).all()

    # Usuarios más activos
    usuarios_activos = db.query(
        Auditoria.usuario_id,
        func.count(Auditoria.id).label('cantidad')
    ).filter(
        func.date(Auditoria.created_at) >= fecha_desde,
        func.date(Auditoria.created_at) <= fecha_hasta,
        Auditoria.usuario_id.isnot(None)
    ).group_by(Auditoria.usuario_id).order_by(
        func.count(Auditoria.id).desc()
    ).limit(10).all()

    # Obtener nombres de usuarios
    usuario_ids = [u[0] for u in usuarios_activos]
    usuarios = db.query(Usuario).filter(Usuario.id.in_(usuario_ids)).all()
    usuario_nombres = {u.id: f"{u.nombre} {u.apellido}" for u in usuarios}

    return {
        "periodo": {
            "desde": fecha_desde.isoformat(),
            "hasta": fecha_hasta.isoformat()
        },
        "total_acciones": total_acciones,
        "acciones_por_tipo": {
            str(a.accion.value): c for a, c in acciones_por_tipo
        },
        "acciones_por_modulo": {
            str(m.modulo.value): c for m, c in acciones_por_modulo
        },
        "usuarios_mas_activos": [
            {
                "usuario_id": str(uid),
                "usuario_nombre": usuario_nombres.get(uid, "Desconocido"),
                "cantidad": cant
            }
            for uid, cant in usuarios_activos
        ]
    }


def get_logins_usuario(
    db: Session,
    usuario_id: UUID,
    limit: int = 20
) -> List[Auditoria]:
    """Obtiene los últimos logins de un usuario."""
    return db.query(Auditoria).filter(
        Auditoria.usuario_id == usuario_id,
        Auditoria.accion == TipoAccion.login
    ).order_by(Auditoria.created_at.desc()).limit(limit).all()


def get_actividad_reciente(
    db: Session,
    limit: int = 20
) -> List[Auditoria]:
    """Obtiene la actividad más reciente del sistema."""
    return db.query(Auditoria).order_by(
        Auditoria.created_at.desc()
    ).limit(limit).all()


# Helper functions para registrar acciones comunes
def registrar_login(
    db: Session,
    usuario_id: UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Auditoria:
    """Registra un login de usuario."""
    return registrar_accion(
        db=db,
        usuario_id=usuario_id,
        accion=TipoAccion.login,
        modulo=ModuloAuditado.auth,
        descripcion="Inicio de sesión",
        ip_address=ip_address,
        user_agent=user_agent
    )


def registrar_logout(
    db: Session,
    usuario_id: UUID,
    ip_address: Optional[str] = None
) -> Auditoria:
    """Registra un logout de usuario."""
    return registrar_accion(
        db=db,
        usuario_id=usuario_id,
        accion=TipoAccion.logout,
        modulo=ModuloAuditado.auth,
        descripcion="Cierre de sesión",
        ip_address=ip_address
    )


def registrar_creacion(
    db: Session,
    usuario_id: UUID,
    modulo: ModuloAuditado,
    recurso_id: UUID,
    recurso_tipo: str,
    descripcion: str,
    datos: Optional[Dict[str, Any]] = None
) -> Auditoria:
    """Registra la creación de un recurso."""
    return registrar_accion(
        db=db,
        usuario_id=usuario_id,
        accion=TipoAccion.crear,
        modulo=modulo,
        descripcion=descripcion,
        recurso_id=recurso_id,
        recurso_tipo=recurso_tipo,
        datos_adicionales=datos
    )


def registrar_actualizacion(
    db: Session,
    usuario_id: UUID,
    modulo: ModuloAuditado,
    recurso_id: UUID,
    recurso_tipo: str,
    descripcion: str,
    datos_anteriores: Optional[Dict[str, Any]] = None,
    datos_nuevos: Optional[Dict[str, Any]] = None
) -> Auditoria:
    """Registra la actualización de un recurso."""
    return registrar_accion(
        db=db,
        usuario_id=usuario_id,
        accion=TipoAccion.actualizar,
        modulo=modulo,
        descripcion=descripcion,
        recurso_id=recurso_id,
        recurso_tipo=recurso_tipo,
        datos_adicionales={
            "anterior": datos_anteriores,
            "nuevo": datos_nuevos
        } if datos_anteriores or datos_nuevos else None
    )


def registrar_eliminacion(
    db: Session,
    usuario_id: UUID,
    modulo: ModuloAuditado,
    recurso_id: UUID,
    recurso_tipo: str,
    descripcion: str,
    datos: Optional[Dict[str, Any]] = None
) -> Auditoria:
    """Registra la eliminación de un recurso."""
    return registrar_accion(
        db=db,
        usuario_id=usuario_id,
        accion=TipoAccion.eliminar,
        modulo=modulo,
        descripcion=descripcion,
        recurso_id=recurso_id,
        recurso_tipo=recurso_tipo,
        datos_adicionales=datos
    )
