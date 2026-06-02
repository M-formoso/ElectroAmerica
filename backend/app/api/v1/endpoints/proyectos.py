from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario, RolUsuario
from app.models.proyecto import EstadoProyecto
from app.schemas.proyecto import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse, ProyectoDetailResponse,
    VerificarStockRequest, VerificarStockResponse, MaterialFaltante,
)
from decimal import Decimal
from collections import defaultdict
from app.models.actividad_tipo import MaterialActividadTipo
from app.models.material import Material
from app.models.deposito import Deposito, DepositoMaterial
from app.schemas.etapa import EtapaResponse
from app.schemas.gasto import GastoResponse
from app.schemas.material import AsignacionMaterialResponse
from app.models.asignacion_material import AsignacionMaterial
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
    # Cliente solo ve sus proyectos. cliente_id en proyectos es FK a clientes,
    # asi que tenemos que buscar el Cliente asociado al usuario.
    if usuario.rol == RolUsuario.cliente:
        from app.models.cliente import Cliente
        cliente_empresa = db.query(Cliente).filter(Cliente.usuario_id == usuario.id).first()
        if not cliente_empresa:
            return []
        cliente_id = cliente_empresa.id

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
        deposito_id=proyecto.deposito_id,
        deposito_nombre=proyecto.deposito.nombre if proyecto.deposito else None,
        lista_precio_id=proyecto.lista_precio_id,
        lista_precio_nombre=proyecto.lista_precio.nombre if proyecto.lista_precio else None,
        total_etapas=stats.get("total_etapas", 0),
        etapas_completadas=stats.get("etapas_completadas", 0),
        cliente_nombre=proyecto.cliente.nombre_display if proyecto.cliente else None
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


@router.get("/{proyecto_id}/materiales", response_model=List[AsignacionMaterialResponse])
def listar_materiales_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista los materiales asignados a un proyecto."""
    if not proyecto_service.verificar_acceso_proyecto(db, proyecto_id, usuario.id, usuario.rol):
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    asignaciones = (
        db.query(AsignacionMaterial)
        .filter(
            AsignacionMaterial.proyecto_id == proyecto_id,
            AsignacionMaterial.activo == True
        )
        .order_by(AsignacionMaterial.fecha_asignacion.desc())
        .all()
    )

    return [
        AsignacionMaterialResponse(
            id=a.id,
            material_id=a.material_id,
            proyecto_id=a.proyecto_id,
            etapa_id=a.etapa_id,
            cantidad=a.cantidad,
            precio_unitario=a.material.precio_unitario if a.material else None,
            fecha=a.fecha_asignacion,
            observaciones=a.notas,
            material_nombre=a.material.nombre if a.material else None,
            created_at=a.created_at
        )
        for a in asignaciones
    ]


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


@router.post("/verificar-stock-deposito", response_model=VerificarStockResponse)
def verificar_stock_deposito(
    body: VerificarStockRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor),
):
    """Verifica si un deposito tiene stock suficiente para realizar
    el conjunto de actividades indicado (cada una con su cantidad
    planificada). Retorna lista de materiales faltantes si los hay.
    """
    deposito = db.query(Deposito).filter(
        Deposito.id == body.deposito_id, Deposito.activo == True
    ).first()
    if not deposito:
        raise HTTPException(status_code=404, detail="Deposito no encontrado")

    if not body.actividades:
        return VerificarStockResponse(ok=True, faltantes=[])

    # Calcular total necesario por material (sumando todas las actividades)
    necesario_por_material: dict = defaultdict(Decimal)
    actividad_ids = [a.actividad_tipo_id for a in body.actividades]
    materiales_act = db.query(MaterialActividadTipo).filter(
        MaterialActividadTipo.actividad_tipo_id.in_(actividad_ids),
        MaterialActividadTipo.activo == True,
    ).all()
    # Mapa actividad_tipo_id -> [(material_id, cantidad_por_unidad)]
    by_actividad = defaultdict(list)
    for m in materiales_act:
        by_actividad[m.actividad_tipo_id].append((m.material_id, Decimal(str(m.cantidad_por_unidad))))

    for item in body.actividades:
        for material_id, cantidad_por_unidad in by_actividad.get(item.actividad_tipo_id, []):
            necesario_por_material[material_id] += cantidad_por_unidad * item.cantidad_planificada

    if not necesario_por_material:
        return VerificarStockResponse(ok=True, faltantes=[])

    # Traer stock del deposito para esos materiales
    material_ids = list(necesario_por_material.keys())
    rows_dm = db.query(DepositoMaterial).filter(
        DepositoMaterial.deposito_id == body.deposito_id,
        DepositoMaterial.material_id.in_(material_ids),
        DepositoMaterial.activo == True,
    ).all()
    stock_por_material = {dm.material_id: Decimal(str(dm.stock_actual)) for dm in rows_dm}

    # Info de cada material para devolver
    materiales = {
        m.id: m for m in db.query(Material).filter(Material.id.in_(material_ids)).all()
    }

    faltantes = []
    for material_id, necesario in necesario_por_material.items():
        disponible = stock_por_material.get(material_id, Decimal("0"))
        if disponible < necesario:
            mat = materiales.get(material_id)
            faltantes.append(MaterialFaltante(
                material_id=material_id,
                material_nombre=mat.nombre if mat else "(desconocido)",
                material_codigo=mat.codigo if mat else None,
                unidad=mat.unidad if mat else None,
                necesario=necesario,
                disponible=disponible,
                faltante=necesario - disponible,
            ))

    return VerificarStockResponse(ok=len(faltantes) == 0, faltantes=faltantes)
