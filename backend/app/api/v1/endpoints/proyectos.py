from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario, RolUsuario
from app.models.proyecto import EstadoProyecto
from app.schemas.proyecto import ProyectoCreate, ProyectoUpdate, ProyectoResponse, ProyectoDetailResponse
from app.schemas.etapa import EtapaResponse
from app.schemas.gasto import GastoResponse
from app.services import proyecto_service, etapa_service, gasto_service

router = APIRouter()


@router.get("/", response_model=List[ProyectoResponse])
def listar_proyectos(
    estado: Optional[EstadoProyecto] = None,
    cliente_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """
    Lista proyectos.
    - Admin/Supervisor/Operario: ven todos los proyectos
    - Cliente: solo ve sus proyectos asignados
    """
    # Cliente solo ve sus proyectos
    if usuario.rol == RolUsuario.cliente:
        cliente_id = usuario.id

    return proyecto_service.obtener_proyectos(db, skip, limit, estado, cliente_id)


@router.post("/", response_model=ProyectoResponse, status_code=status.HTTP_201_CREATED)
def crear_proyecto(
    proyecto: ProyectoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Crea un nuevo proyecto (solo admin/supervisor)."""
    return proyecto_service.crear_proyecto(db, proyecto, usuario.id)


@router.get("/{proyecto_id}", response_model=ProyectoDetailResponse)
def obtener_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Obtiene detalle de un proyecto."""
    proyecto = proyecto_service.obtener_proyecto(db, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Verificar acceso
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    # Obtener estadísticas
    stats = proyecto_service.obtener_estadisticas_proyecto(db, proyecto_id)

    # Construir respuesta
    response = ProyectoDetailResponse(
        id=proyecto.id,
        nombre=proyecto.nombre,
        descripcion=proyecto.descripcion,
        cliente_id=proyecto.cliente_id,
        ubicacion=proyecto.ubicacion,
        fecha_inicio=proyecto.fecha_inicio,
        fecha_fin_estimada=proyecto.fecha_fin_estimada,
        fecha_fin_real=proyecto.fecha_fin_real,
        estado=proyecto.estado,
        porcentaje_avance=proyecto.porcentaje_avance,
        activo=proyecto.activo,
        created_at=proyecto.created_at,
        supervisor_id=proyecto.supervisor_id,
        total_etapas=stats.get("total_etapas", 0),
        etapas_completadas=stats.get("etapas_completadas", 0),
        cliente_nombre=proyecto.cliente.nombre if proyecto.cliente else None
    )

    # Solo admin/supervisor ven monto contratado
    if usuario.rol in [RolUsuario.administrador, RolUsuario.supervisor]:
        response.monto_contratado = proyecto.monto_contratado

    return response


@router.put("/{proyecto_id}", response_model=ProyectoResponse)
def actualizar_proyecto(
    proyecto_id: UUID,
    proyecto: ProyectoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza un proyecto (solo admin/supervisor)."""
    db_proyecto = proyecto_service.actualizar_proyecto(db, proyecto_id, proyecto)
    if not db_proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return db_proyecto


@router.delete("/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina un proyecto (soft delete, solo admin/supervisor)."""
    if not proyecto_service.eliminar_proyecto(db, proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")


@router.get("/{proyecto_id}/etapas", response_model=List[EtapaResponse])
def listar_etapas_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista las etapas de un proyecto."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    return etapa_service.obtener_etapas(db, proyecto_id)


@router.get("/{proyecto_id}/gastos", response_model=List[GastoResponse])
def listar_gastos_proyecto(
    proyecto_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista los gastos de un proyecto (solo staff)."""
    return gasto_service.obtener_gastos(db, skip, limit, proyecto_id=proyecto_id)


@router.post("/{proyecto_id}/recalcular-avance")
def recalcular_avance(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Recalcula el porcentaje de avance del proyecto."""
    proyecto = proyecto_service.obtener_proyecto(db, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    nuevo_avance = proyecto_service.recalcular_avance_proyecto(db, proyecto_id)
    return {"porcentaje_avance": float(nuevo_avance)}
