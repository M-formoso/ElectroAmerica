from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from collections import defaultdict

from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.material import Material
from app.models.proyecto import Proyecto
from app.models.etapa import Etapa
from app.models.actividad_tipo import ActividadTipo
from app.models.requerimiento_material import (
    RequerimientoMaterial, HistorialRequerimiento, EmpresaProveedora,
    EstadoRequerimiento, OrigenMaterial, PrioridadRequerimiento
)
from app.schemas.requerimiento_material import (
    RequerimientoMaterialCreate, RequerimientoMaterialUpdate,
    RequerimientoMaterialFromActividad, RequerimientoMaterialResponse,
    RequerimientoAprobacion, RequerimientoCambioEstado,
    RequerimientoEntrega, RequerimientoConsumo,
    CalculoMaterialesRequest, CalculoMaterialesResponse, MaterialCalculado,
    ResumenMaterialesProyecto, HistorialRequerimientoResponse,
    EmpresaProveedoraCreate, EmpresaProveedoraUpdate, EmpresaProveedoraResponse
)

router = APIRouter()


# ============ Helper Functions ============

def _enrich_requerimiento(req: RequerimientoMaterial) -> RequerimientoMaterialResponse:
    """Enriquece un requerimiento con datos relacionados."""
    return RequerimientoMaterialResponse(
        id=req.id,
        proyecto_id=req.proyecto_id,
        etapa_id=req.etapa_id,
        material_id=req.material_id,
        cantidad_estimada=float(req.cantidad_estimada),
        cantidad_aprobada=float(req.cantidad_aprobada) if req.cantidad_aprobada else None,
        cantidad_entregada=float(req.cantidad_entregada or 0),
        cantidad_consumida=float(req.cantidad_consumida or 0),
        cantidad_pendiente=req.cantidad_pendiente,
        cantidad_disponible=req.cantidad_disponible,
        estado=req.estado,
        prioridad=req.prioridad,
        origen=req.origen,
        empresa_origen_id=req.empresa_origen_id,
        actividad_tipo_id=req.actividad_tipo_id,
        cantidad_trabajo=float(req.cantidad_trabajo) if req.cantidad_trabajo else None,
        fecha_necesidad=req.fecha_necesidad,
        fecha_solicitud=req.fecha_solicitud,
        fecha_entrega=req.fecha_entrega,
        notas=req.notas,
        notas_aprobacion=req.notas_aprobacion,
        creado_por_id=req.creado_por_id,
        aprobado_por_id=req.aprobado_por_id,
        fecha_aprobacion=req.fecha_aprobacion,
        activo=req.activo,
        created_at=req.created_at,
        updated_at=req.updated_at,
        material_nombre=req.material.nombre if req.material else None,
        material_unidad=req.material.unidad if req.material else None,
        material_stock=float(req.material.stock_actual) if req.material else None,
        proyecto_nombre=req.proyecto.nombre if req.proyecto else None,
        etapa_nombre=req.etapa.nombre if req.etapa else None,
        actividad_tipo_nombre=req.actividad_tipo.nombre if req.actividad_tipo else None,
        empresa_origen_nombre=req.empresa_origen.nombre if req.empresa_origen else None,
    )


def _registrar_historial(
    db: Session,
    requerimiento_id: UUID,
    usuario_id: UUID,
    campo: str,
    valor_anterior: str,
    valor_nuevo: str,
    motivo: Optional[str] = None
):
    """Registra un cambio en el historial."""
    historial = HistorialRequerimiento(
        requerimiento_id=requerimiento_id,
        usuario_id=usuario_id,
        campo_modificado=campo,
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
        motivo=motivo
    )
    db.add(historial)


# ============ Empresas Proveedoras ============

@router.get("/empresas", response_model=List[EmpresaProveedoraResponse])
def listar_empresas(
    tipo: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista empresas proveedoras/clientes."""
    query = db.query(EmpresaProveedora).filter(EmpresaProveedora.activo == True)
    if tipo:
        query = query.filter(EmpresaProveedora.tipo == tipo)
    return query.order_by(EmpresaProveedora.nombre).all()


@router.post("/empresas", response_model=EmpresaProveedoraResponse, status_code=status.HTTP_201_CREATED)
def crear_empresa(
    empresa: EmpresaProveedoraCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Crea una nueva empresa proveedora/cliente."""
    db_empresa = EmpresaProveedora(**empresa.model_dump())
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa


@router.put("/empresas/{empresa_id}", response_model=EmpresaProveedoraResponse)
def actualizar_empresa(
    empresa_id: UUID,
    empresa: EmpresaProveedoraUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza una empresa."""
    db_empresa = db.query(EmpresaProveedora).filter(
        EmpresaProveedora.id == empresa_id,
        EmpresaProveedora.activo == True
    ).first()
    if not db_empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    for field, value in empresa.model_dump(exclude_unset=True).items():
        setattr(db_empresa, field, value)

    db.commit()
    db.refresh(db_empresa)
    return db_empresa


# ============ Requerimientos CRUD ============

@router.get("/", response_model=List[RequerimientoMaterialResponse])
def listar_requerimientos(
    proyecto_id: Optional[UUID] = None,
    etapa_id: Optional[UUID] = None,
    estado: Optional[EstadoRequerimiento] = None,
    prioridad: Optional[PrioridadRequerimiento] = None,
    origen: Optional[OrigenMaterial] = None,
    pendientes: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=200),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista requerimientos de material con filtros."""
    query = db.query(RequerimientoMaterial).filter(RequerimientoMaterial.activo == True)

    if proyecto_id:
        query = query.filter(RequerimientoMaterial.proyecto_id == proyecto_id)
    if etapa_id:
        query = query.filter(RequerimientoMaterial.etapa_id == etapa_id)
    if estado:
        query = query.filter(RequerimientoMaterial.estado == estado)
    if prioridad:
        query = query.filter(RequerimientoMaterial.prioridad == prioridad)
    if origen:
        query = query.filter(RequerimientoMaterial.origen == origen)
    if pendientes:
        # Filtrar solo los que tienen cantidad pendiente
        query = query.filter(
            RequerimientoMaterial.estado.notin_([
                EstadoRequerimiento.entregado_obra,
                EstadoRequerimiento.consumido,
                EstadoRequerimiento.cancelado
            ])
        )

    # Ordenar por prioridad y fecha de necesidad
    query = query.order_by(
        RequerimientoMaterial.prioridad,
        RequerimientoMaterial.fecha_necesidad,
        RequerimientoMaterial.created_at.desc()
    )

    reqs = query.offset(skip).limit(limit).all()
    return [_enrich_requerimiento(r) for r in reqs]


@router.post("/", response_model=RequerimientoMaterialResponse, status_code=status.HTTP_201_CREATED)
def crear_requerimiento(
    req: RequerimientoMaterialCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Crea un requerimiento de material manual."""
    # Validar que existan proyecto y material
    proyecto = db.query(Proyecto).filter(Proyecto.id == req.proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    material = db.query(Material).filter(Material.id == req.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    db_req = RequerimientoMaterial(
        proyecto_id=req.proyecto_id,
        etapa_id=req.etapa_id,
        material_id=req.material_id,
        cantidad_estimada=req.cantidad_estimada,
        prioridad=req.prioridad,
        origen=req.origen,
        empresa_origen_id=req.empresa_origen_id,
        fecha_necesidad=req.fecha_necesidad,
        notas=req.notas,
        estado=EstadoRequerimiento.estimado,
        creado_por_id=usuario.id
    )

    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return _enrich_requerimiento(db_req)


@router.post("/desde-actividad", response_model=List[RequerimientoMaterialResponse])
def crear_desde_actividad(
    data: RequerimientoMaterialFromActividad,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Crea requerimientos desde una actividad tipo."""
    actividad = db.query(ActividadTipo).filter(
        ActividadTipo.id == data.actividad_tipo_id,
        ActividadTipo.activo == True
    ).first()

    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad tipo no encontrada")

    # Calcular materiales
    materiales_calculados = actividad.calcular_materiales(float(data.cantidad_trabajo))

    requerimientos = []
    for mat in materiales_calculados:
        db_req = RequerimientoMaterial(
            proyecto_id=data.proyecto_id,
            etapa_id=data.etapa_id,
            material_id=mat["material_id"],
            cantidad_estimada=mat["cantidad"],
            prioridad=data.prioridad,
            fecha_necesidad=data.fecha_necesidad,
            actividad_tipo_id=data.actividad_tipo_id,
            cantidad_trabajo=data.cantidad_trabajo,
            notas=mat.get("notas"),
            estado=EstadoRequerimiento.estimado,
            creado_por_id=usuario.id
        )
        db.add(db_req)
        requerimientos.append(db_req)

    db.commit()
    for r in requerimientos:
        db.refresh(r)

    return [_enrich_requerimiento(r) for r in requerimientos]


@router.get("/{requerimiento_id}", response_model=RequerimientoMaterialResponse)
def obtener_requerimiento(
    requerimiento_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene un requerimiento por ID."""
    req = db.query(RequerimientoMaterial).filter(
        RequerimientoMaterial.id == requerimiento_id,
        RequerimientoMaterial.activo == True
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Requerimiento no encontrado")

    return _enrich_requerimiento(req)


@router.put("/{requerimiento_id}", response_model=RequerimientoMaterialResponse)
def actualizar_requerimiento(
    requerimiento_id: UUID,
    data: RequerimientoMaterialUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Actualiza un requerimiento."""
    req = db.query(RequerimientoMaterial).filter(
        RequerimientoMaterial.id == requerimiento_id,
        RequerimientoMaterial.activo == True
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Requerimiento no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_value = str(getattr(req, field))
        setattr(req, field, value)
        _registrar_historial(db, req.id, usuario.id, field, old_value, str(value))

    db.commit()
    db.refresh(req)
    return _enrich_requerimiento(req)


@router.delete("/{requerimiento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_requerimiento(
    requerimiento_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina un requerimiento (soft delete)."""
    req = db.query(RequerimientoMaterial).filter(
        RequerimientoMaterial.id == requerimiento_id,
        RequerimientoMaterial.activo == True
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Requerimiento no encontrado")

    req.activo = False
    _registrar_historial(db, req.id, usuario.id, "activo", "True", "False", "Eliminado")
    db.commit()


# ============ Acciones sobre Requerimientos ============

@router.post("/{requerimiento_id}/aprobar", response_model=RequerimientoMaterialResponse)
def aprobar_requerimiento(
    requerimiento_id: UUID,
    data: RequerimientoAprobacion,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Aprueba un requerimiento."""
    req = db.query(RequerimientoMaterial).filter(
        RequerimientoMaterial.id == requerimiento_id,
        RequerimientoMaterial.activo == True
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Requerimiento no encontrado")

    old_estado = req.estado.value
    req.cantidad_aprobada = data.cantidad_aprobada
    req.notas_aprobacion = data.notas_aprobacion
    req.estado = EstadoRequerimiento.aprobado
    req.aprobado_por_id = usuario.id
    req.fecha_aprobacion = datetime.now()

    _registrar_historial(db, req.id, usuario.id, "estado", old_estado, "aprobado", "Aprobación")
    _registrar_historial(db, req.id, usuario.id, "cantidad_aprobada", str(req.cantidad_estimada), str(data.cantidad_aprobada))

    db.commit()
    db.refresh(req)
    return _enrich_requerimiento(req)


@router.post("/{requerimiento_id}/cambiar-estado", response_model=RequerimientoMaterialResponse)
def cambiar_estado(
    requerimiento_id: UUID,
    data: RequerimientoCambioEstado,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Cambia el estado de un requerimiento."""
    req = db.query(RequerimientoMaterial).filter(
        RequerimientoMaterial.id == requerimiento_id,
        RequerimientoMaterial.activo == True
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Requerimiento no encontrado")

    old_estado = req.estado.value
    req.estado = data.estado

    if data.origen:
        req.origen = data.origen
    if data.empresa_origen_id:
        req.empresa_origen_id = data.empresa_origen_id

    if data.estado in [EstadoRequerimiento.pendiente_compra, EstadoRequerimiento.en_proceso_compra, EstadoRequerimiento.pendiente_entrega]:
        req.fecha_solicitud = datetime.now()

    _registrar_historial(db, req.id, usuario.id, "estado", old_estado, data.estado.value, data.motivo)

    db.commit()
    db.refresh(req)
    return _enrich_requerimiento(req)


@router.post("/{requerimiento_id}/registrar-entrega", response_model=RequerimientoMaterialResponse)
def registrar_entrega(
    requerimiento_id: UUID,
    data: RequerimientoEntrega,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Registra la entrega de material a obra."""
    req = db.query(RequerimientoMaterial).filter(
        RequerimientoMaterial.id == requerimiento_id,
        RequerimientoMaterial.activo == True
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Requerimiento no encontrado")

    old_cantidad = float(req.cantidad_entregada or 0)
    req.cantidad_entregada = old_cantidad + data.cantidad_entregada
    req.fecha_entrega = datetime.now()

    # Actualizar estado si ya se entregó todo
    cantidad_objetivo = float(req.cantidad_aprobada or req.cantidad_estimada)
    if float(req.cantidad_entregada) >= cantidad_objetivo:
        req.estado = EstadoRequerimiento.entregado_obra

    _registrar_historial(
        db, req.id, usuario.id, "cantidad_entregada",
        str(old_cantidad), str(req.cantidad_entregada),
        data.notas
    )

    db.commit()
    db.refresh(req)
    return _enrich_requerimiento(req)


@router.post("/{requerimiento_id}/registrar-consumo", response_model=RequerimientoMaterialResponse)
def registrar_consumo(
    requerimiento_id: UUID,
    data: RequerimientoConsumo,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Registra el consumo de material en obra."""
    req = db.query(RequerimientoMaterial).filter(
        RequerimientoMaterial.id == requerimiento_id,
        RequerimientoMaterial.activo == True
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Requerimiento no encontrado")

    old_cantidad = float(req.cantidad_consumida or 0)
    req.cantidad_consumida = old_cantidad + data.cantidad_consumida

    # Actualizar estado si ya se consumió todo
    if float(req.cantidad_consumida) >= float(req.cantidad_entregada or 0):
        req.estado = EstadoRequerimiento.consumido

    _registrar_historial(
        db, req.id, usuario.id, "cantidad_consumida",
        str(old_cantidad), str(req.cantidad_consumida),
        data.notas
    )

    db.commit()
    db.refresh(req)
    return _enrich_requerimiento(req)


# ============ Historial ============

@router.get("/{requerimiento_id}/historial", response_model=List[HistorialRequerimientoResponse])
def obtener_historial(
    requerimiento_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene el historial de cambios de un requerimiento."""
    historial = db.query(HistorialRequerimiento).filter(
        HistorialRequerimiento.requerimiento_id == requerimiento_id
    ).order_by(HistorialRequerimiento.created_at.desc()).all()

    result = []
    for h in historial:
        result.append(HistorialRequerimientoResponse(
            id=h.id,
            campo_modificado=h.campo_modificado,
            valor_anterior=h.valor_anterior,
            valor_nuevo=h.valor_nuevo,
            motivo=h.motivo,
            usuario_nombre=f"{h.usuario.nombre} {h.usuario.apellido}" if h.usuario else None,
            created_at=h.created_at
        ))
    return result


# ============ Cálculo y Consolidación ============

@router.post("/calcular", response_model=CalculoMaterialesResponse)
def calcular_materiales(
    data: CalculoMaterialesRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """
    Calcula los materiales necesarios para múltiples actividades.
    Consolida materiales repetidos y verifica stock.
    """
    # Consolidar materiales por ID
    materiales_consolidados = defaultdict(lambda: {
        "cantidad_total": 0,
        "actividades_origen": []
    })

    for act_data in data.actividades:
        actividad = db.query(ActividadTipo).filter(
            ActividadTipo.id == act_data["actividad_tipo_id"],
            ActividadTipo.activo == True
        ).first()

        if not actividad:
            continue

        materiales = actividad.calcular_materiales(float(act_data["cantidad_trabajo"]))

        for mat in materiales:
            mat_id = str(mat["material_id"])
            materiales_consolidados[mat_id]["cantidad_total"] += mat["cantidad"]
            materiales_consolidados[mat_id]["actividades_origen"].append({
                "actividad_tipo_id": str(act_data["actividad_tipo_id"]),
                "actividad_nombre": actividad.nombre,
                "cantidad_trabajo": act_data["cantidad_trabajo"],
                "cantidad_material": mat["cantidad"]
            })

    # Obtener datos de materiales y verificar stock
    resultado = []
    items_sin_stock = 0
    requerimientos_creados = []

    for mat_id, datos in materiales_consolidados.items():
        material = db.query(Material).filter(Material.id == mat_id).first()
        if not material:
            continue

        stock = float(material.stock_actual or 0)
        falta = datos["cantidad_total"] > stock

        if falta:
            items_sin_stock += 1

        resultado.append(MaterialCalculado(
            material_id=UUID(mat_id),
            material_nombre=material.nombre,
            material_unidad=material.unidad,
            cantidad_total=datos["cantidad_total"],
            stock_disponible=stock,
            falta_stock=falta,
            actividades_origen=datos["actividades_origen"]
        ))

        # Crear requerimientos si se solicita
        if data.crear_requerimientos:
            db_req = RequerimientoMaterial(
                proyecto_id=data.proyecto_id,
                etapa_id=data.etapa_id,
                material_id=UUID(mat_id),
                cantidad_estimada=datos["cantidad_total"],
                prioridad=data.prioridad,
                fecha_necesidad=data.fecha_necesidad,
                estado=EstadoRequerimiento.estimado,
                creado_por_id=usuario.id
            )
            db.add(db_req)
            requerimientos_creados.append(db_req)

    if data.crear_requerimientos and requerimientos_creados:
        db.commit()
        requerimientos_creados = [r.id for r in requerimientos_creados]

    return CalculoMaterialesResponse(
        materiales=resultado,
        total_items=len(resultado),
        items_sin_stock=items_sin_stock,
        requerimientos_creados=requerimientos_creados if data.crear_requerimientos else None
    )


@router.get("/proyecto/{proyecto_id}/resumen", response_model=ResumenMaterialesProyecto)
def resumen_materiales_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene resumen de materiales de un proyecto."""
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    reqs = db.query(RequerimientoMaterial).filter(
        RequerimientoMaterial.proyecto_id == proyecto_id,
        RequerimientoMaterial.activo == True
    ).all()

    por_estado = defaultdict(int)
    por_prioridad = defaultdict(int)
    pendientes = 0
    en_obra = 0
    valor_total = 0

    for req in reqs:
        por_estado[req.estado.value] += 1
        por_prioridad[req.prioridad.value] += 1

        if req.estado not in [EstadoRequerimiento.entregado_obra, EstadoRequerimiento.consumido, EstadoRequerimiento.cancelado]:
            pendientes += 1
        elif req.estado == EstadoRequerimiento.entregado_obra:
            en_obra += 1

        if req.material and req.material.precio_unitario:
            cantidad = float(req.cantidad_aprobada or req.cantidad_estimada or 0)
            valor_total += cantidad * float(req.material.precio_unitario)

    return ResumenMaterialesProyecto(
        proyecto_id=proyecto_id,
        proyecto_nombre=proyecto.nombre,
        total_requerimientos=len(reqs),
        por_estado=dict(por_estado),
        por_prioridad=dict(por_prioridad),
        materiales_pendientes=pendientes,
        materiales_en_obra=en_obra,
        valor_estimado_total=valor_total if valor_total > 0 else None
    )
