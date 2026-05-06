from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual
from app.models.usuario import Usuario, RolUsuario
from app.models.cliente import Cliente
from app.models.proyecto import Proyecto
from app.models.etapa import Etapa
from app.models.foto import Foto
from app.models.reporte import Reporte
from app.schemas.proyecto import ProyectoClienteResponse
from app.schemas.etapa import EtapaClienteResponse
from app.schemas.foto import FotoClienteResponse

router = APIRouter()


def verificar_cliente(usuario: Usuario):
    """Verifica que el usuario sea un cliente."""
    if usuario.rol != RolUsuario.cliente:
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido solo para clientes"
        )
    return usuario


def _obtener_cliente_id_de_usuario(db: Session, usuario_id: UUID) -> UUID:
    """Obtiene el id del Cliente asociado al usuario del portal."""
    cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario_id).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="No hay un cliente asociado a este usuario"
        )
    return cliente.id


def verificar_proyecto_cliente(db: Session, proyecto_id: UUID, cliente_id: UUID) -> Proyecto:
    """Verifica que el proyecto pertenezca al cliente."""
    proyecto = db.query(Proyecto).filter(
        Proyecto.id == proyecto_id,
        Proyecto.cliente_id == cliente_id,
        Proyecto.activo == True
    ).first()

    if not proyecto:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )
    return proyecto


@router.get("/mis-proyectos", response_model=List[ProyectoClienteResponse])
def mis_proyectos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """
    Lista los proyectos asignados al cliente autenticado.
    NO incluye información financiera.
    """
    verificar_cliente(usuario)
    cliente_id = _obtener_cliente_id_de_usuario(db, usuario.id)

    proyectos = db.query(Proyecto).filter(
        Proyecto.cliente_id == cliente_id,
        Proyecto.activo == True
    ).order_by(Proyecto.fecha_inicio.desc()).all()

    return proyectos


@router.get("/proyecto/{proyecto_id}", response_model=ProyectoClienteResponse)
def detalle_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """
    Detalle de un proyecto del cliente.
    NO incluye información financiera.
    """
    verificar_cliente(usuario)
    cliente_id = _obtener_cliente_id_de_usuario(db, usuario.id)
    proyecto = verificar_proyecto_cliente(db, proyecto_id, cliente_id)
    return proyecto


@router.get("/proyecto/{proyecto_id}/etapas", response_model=List[EtapaClienteResponse])
def etapas_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """
    Lista las etapas de un proyecto del cliente.
    NO incluye costos ni precios.
    """
    verificar_cliente(usuario)
    cliente_id = _obtener_cliente_id_de_usuario(db, usuario.id)
    verificar_proyecto_cliente(db, proyecto_id, cliente_id)

    etapas = db.query(Etapa).filter(
        Etapa.proyecto_id == proyecto_id,
        Etapa.activo == True
    ).order_by(Etapa.orden).all()

    return etapas


@router.get("/proyecto/{proyecto_id}/fotos", response_model=List[FotoClienteResponse])
def fotos_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """
    Lista las fotos AUTORIZADAS de un proyecto del cliente.
    Solo muestra fotos con visible_cliente=True.
    """
    verificar_cliente(usuario)
    cliente_id = _obtener_cliente_id_de_usuario(db, usuario.id)
    verificar_proyecto_cliente(db, proyecto_id, cliente_id)

    fotos = db.query(Foto).filter(
        Foto.proyecto_id == proyecto_id,
        Foto.visible_cliente == True,
        Foto.activo == True
    ).order_by(Foto.fecha.desc()).all()

    return fotos


@router.get("/proyecto/{proyecto_id}/reporte")
def ultimo_reporte(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """
    Obtiene el último reporte compartido con el cliente.
    Solo reportes marcados como compartido_cliente=True.
    """
    verificar_cliente(usuario)
    cliente_id = _obtener_cliente_id_de_usuario(db, usuario.id)
    verificar_proyecto_cliente(db, proyecto_id, cliente_id)

    reporte = db.query(Reporte).filter(
        Reporte.proyecto_id == proyecto_id,
        Reporte.compartido_cliente == True,
        Reporte.activo == True
    ).order_by(Reporte.created_at.desc()).first()

    if not reporte:
        raise HTTPException(
            status_code=404,
            detail="No hay reportes disponibles"
        )

    return {
        "id": str(reporte.id),
        "fecha_desde": reporte.fecha_desde.isoformat(),
        "fecha_hasta": reporte.fecha_hasta.isoformat(),
        "tipo": reporte.tipo,
        "pdf_url": reporte.pdf_url,
        "created_at": reporte.created_at.isoformat()
    }
