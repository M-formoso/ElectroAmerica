from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import date
from app.core.deps import get_db, require_admin_or_supervisor, get_usuario_actual
from app.models.usuario import Usuario
from app.schemas.finanzas import (
    PrecioItemCreate, PrecioItemResponse,
    ResumenFinancieroProyecto, ResumenFinancieroGeneral,
    ActualizarMontoRequest
)
from app.schemas.transaccion import (
    TransaccionCreate, TransaccionUpdate,
    CuentaCreate, CuentaUpdate,
    ClienteProveedorCreate, ClienteProveedorUpdate,
    PresupuestoCreate, PresupuestoUpdate,
    TipoTransaccion, EstadoTransaccion
)
from app.services import finanzas_service

router = APIRouter()


@router.get("/proyecto/{proyecto_id}", response_model=ResumenFinancieroProyecto)
def obtener_finanzas_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """
    Obtiene el resumen financiero de un proyecto.
    Solo admin y supervisor tienen acceso.
    """
    resumen = finanzas_service.obtener_resumen_financiero_proyecto(db, proyecto_id)
    if not resumen:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return resumen


@router.get("/resumen-general", response_model=ResumenFinancieroGeneral)
def obtener_resumen_general(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """
    Obtiene el resumen financiero general de todos los proyectos activos.
    Solo admin y supervisor tienen acceso.
    """
    return finanzas_service.obtener_resumen_financiero_general(db)


@router.post("/precio-item", response_model=PrecioItemResponse)
def cargar_precio_item(
    precio: PrecioItemCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """
    Carga o actualiza el precio de un ítem de trabajo.
    Mantiene historial de precios.
    """
    return finanzas_service.cargar_precio_item(
        db, precio.item_trabajo_id, precio.precio_unitario, usuario.id
    )


@router.put("/proyecto/{proyecto_id}/monto")
def actualizar_monto_proyecto(
    proyecto_id: UUID,
    request: ActualizarMontoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza el monto contratado de un proyecto."""
    proyecto = finanzas_service.actualizar_monto_contratado(db, proyecto_id, request.monto)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return {
        "message": "Monto actualizado",
        "proyecto_id": str(proyecto_id),
        "monto_contratado": float(request.monto)
    }


@router.get("/rentabilidad")
def obtener_rentabilidad(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene listado de rentabilidad por proyecto."""
    resumen = finanzas_service.obtener_resumen_financiero_general(db)

    return [
        {
            "proyecto_id": str(p.proyecto_id),
            "nombre": p.nombre_proyecto,
            "monto_contratado": float(p.monto_contratado) if p.monto_contratado else None,
            "costo_total": float(p.costo_total),
            "rentabilidad": float(p.rentabilidad) if p.rentabilidad else None,
            "porcentaje_rentabilidad": float(p.porcentaje_rentabilidad) if p.porcentaje_rentabilidad else None
        }
        for p in resumen.proyectos
    ]


# ============ DASHBOARD ============

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene datos del dashboard de finanzas."""
    return finanzas_service.get_dashboard_finanzas(db)


# ============ TRANSACCIONES ============

@router.get("/transacciones")
def get_transacciones(
    tipo: Optional[str] = Query(None, description="ingreso o egreso"),
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    proyecto_id: Optional[UUID] = None,
    categoria_id: Optional[UUID] = None,
    cuenta_id: Optional[UUID] = None,
    cliente_proveedor_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Lista transacciones con filtros."""
    tipo_enum = TipoTransaccion(tipo) if tipo else None
    estado_enum = EstadoTransaccion(estado) if estado else None

    transacciones = finanzas_service.get_transacciones(
        db, tipo_enum, fecha_desde, fecha_hasta,
        proyecto_id, categoria_id, cuenta_id,
        cliente_proveedor_id, estado_enum, skip, limit
    )

    return [
        {
            "id": str(t.id),
            "tipo": t.tipo.value,
            "concepto": t.concepto,
            "descripcion": t.descripcion,
            "monto": float(t.monto),
            "fecha": t.fecha.isoformat(),
            "metodo_pago": t.metodo_pago.value if t.metodo_pago else None,
            "referencia_pago": t.referencia_pago,
            "estado": t.estado.value,
            "numero_comprobante": t.numero_comprobante,
            "tipo_comprobante": t.tipo_comprobante,
            "proyecto_id": str(t.proyecto_id) if t.proyecto_id else None,
            "proyecto_nombre": t.proyecto.nombre if t.proyecto else None,
            "categoria_id": str(t.categoria_id) if t.categoria_id else None,
            "categoria_nombre": t.categoria.nombre if t.categoria else None,
            "cuenta_id": str(t.cuenta_id) if t.cuenta_id else None,
            "cuenta_nombre": t.cuenta.nombre if t.cuenta else None,
            "cliente_proveedor_id": str(t.cliente_proveedor_id) if t.cliente_proveedor_id else None,
            "cliente_proveedor_nombre": t.cliente_proveedor.razon_social if t.cliente_proveedor else None,
            "creado_por": f"{t.creador.nombre} {t.creador.apellido}" if t.creador else None,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in transacciones
    ]


@router.get("/transacciones/{transaccion_id}")
def get_transaccion(
    transaccion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene una transaccion por ID."""
    t = finanzas_service.get_transaccion(db, transaccion_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")

    return {
        "id": str(t.id),
        "tipo": t.tipo.value,
        "concepto": t.concepto,
        "descripcion": t.descripcion,
        "monto": float(t.monto),
        "fecha": t.fecha.isoformat(),
        "metodo_pago": t.metodo_pago.value if t.metodo_pago else None,
        "referencia_pago": t.referencia_pago,
        "estado": t.estado.value,
        "numero_comprobante": t.numero_comprobante,
        "tipo_comprobante": t.tipo_comprobante,
        "comprobante_url": t.comprobante_url,
        "proyecto_id": str(t.proyecto_id) if t.proyecto_id else None,
        "proyecto_nombre": t.proyecto.nombre if t.proyecto else None,
        "categoria_id": str(t.categoria_id) if t.categoria_id else None,
        "categoria_nombre": t.categoria.nombre if t.categoria else None,
        "cuenta_id": str(t.cuenta_id) if t.cuenta_id else None,
        "cuenta_nombre": t.cuenta.nombre if t.cuenta else None,
        "cliente_proveedor_id": str(t.cliente_proveedor_id) if t.cliente_proveedor_id else None,
        "cliente_proveedor_nombre": t.cliente_proveedor.razon_social if t.cliente_proveedor else None,
        "creado_por_id": str(t.creado_por_id),
        "creado_por": f"{t.creador.nombre} {t.creador.apellido}" if t.creador else None,
        "created_at": t.created_at.isoformat() if t.created_at else None
    }


@router.post("/transacciones")
def create_transaccion(
    transaccion: TransaccionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Crea una nueva transaccion (ingreso o egreso)."""
    t = finanzas_service.create_transaccion(db, transaccion, current_user.id)
    return {
        "id": str(t.id),
        "tipo": t.tipo.value,
        "concepto": t.concepto,
        "monto": float(t.monto),
        "fecha": t.fecha.isoformat(),
        "estado": t.estado.value,
        "message": "Transaccion creada exitosamente"
    }


@router.put("/transacciones/{transaccion_id}")
def update_transaccion(
    transaccion_id: UUID,
    transaccion: TransaccionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza una transaccion."""
    t = finanzas_service.update_transaccion(db, transaccion_id, transaccion)
    if not t:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")
    return {"message": "Transaccion actualizada", "id": str(t.id)}


@router.delete("/transacciones/{transaccion_id}")
def delete_transaccion(
    transaccion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina una transaccion."""
    success = finanzas_service.delete_transaccion(db, transaccion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")
    return {"message": "Transaccion eliminada"}


@router.post("/transacciones/{transaccion_id}/anular")
def anular_transaccion(
    transaccion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Anula una transaccion (no la elimina, cambia su estado)."""
    t = finanzas_service.anular_transaccion(db, transaccion_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")
    return {"message": "Transaccion anulada", "id": str(t.id)}


# ============ CUENTAS ============

@router.get("/cuentas")
def get_cuentas(
    tipo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Lista todas las cuentas con sus saldos."""
    cuentas = finanzas_service.get_cuentas(db, tipo)
    return [finanzas_service.get_saldo_cuenta(db, c.id) for c in cuentas]


@router.get("/cuentas/{cuenta_id}")
def get_cuenta(
    cuenta_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene una cuenta con su saldo."""
    cuenta = finanzas_service.get_cuenta(db, cuenta_id)
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return finanzas_service.get_saldo_cuenta(db, cuenta_id)


@router.post("/cuentas")
def create_cuenta(
    cuenta: CuentaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Crea una nueva cuenta (caja, banco, etc.)."""
    c = finanzas_service.create_cuenta(db, cuenta)
    return {
        "id": str(c.id),
        "nombre": c.nombre,
        "tipo": c.tipo.value,
        "message": "Cuenta creada exitosamente"
    }


@router.put("/cuentas/{cuenta_id}")
def update_cuenta(
    cuenta_id: UUID,
    cuenta: CuentaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza una cuenta."""
    c = finanzas_service.update_cuenta(db, cuenta_id, cuenta)
    if not c:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return {"message": "Cuenta actualizada", "id": str(c.id)}


@router.delete("/cuentas/{cuenta_id}")
def delete_cuenta(
    cuenta_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina una cuenta."""
    success = finanzas_service.delete_cuenta(db, cuenta_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return {"message": "Cuenta eliminada"}


@router.get("/cuentas/{cuenta_id}/movimientos")
def get_movimientos_cuenta(
    cuenta_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene movimientos de una cuenta especifica."""
    cuenta = finanzas_service.get_cuenta(db, cuenta_id)
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    transacciones = finanzas_service.get_transacciones(
        db, cuenta_id=cuenta_id,
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        skip=skip, limit=limit
    )

    return {
        "cuenta": finanzas_service.get_saldo_cuenta(db, cuenta_id),
        "movimientos": [
            {
                "id": str(t.id),
                "tipo": t.tipo.value,
                "concepto": t.concepto,
                "monto": float(t.monto),
                "fecha": t.fecha.isoformat(),
                "estado": t.estado.value
            }
            for t in transacciones
        ]
    }


# ============ CLIENTES/PROVEEDORES ============

@router.get("/clientes-proveedores")
def get_clientes_proveedores(
    tipo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Lista clientes y proveedores."""
    items = finanzas_service.get_clientes_proveedores(db, tipo)
    return [
        {
            "id": str(cp.id),
            "tipo": cp.tipo.value,
            "razon_social": cp.razon_social,
            "nombre_fantasia": cp.nombre_fantasia,
            "cuit": cp.cuit,
            "telefono": cp.telefono,
            "email": cp.email,
            "condicion_iva": cp.condicion_iva
        }
        for cp in items
    ]


@router.get("/clientes-proveedores/{cp_id}")
def get_cliente_proveedor(
    cp_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene un cliente/proveedor."""
    cp = finanzas_service.get_cliente_proveedor(db, cp_id)
    if not cp:
        raise HTTPException(status_code=404, detail="Cliente/Proveedor no encontrado")
    return {
        "id": str(cp.id),
        "tipo": cp.tipo.value,
        "razon_social": cp.razon_social,
        "nombre_fantasia": cp.nombre_fantasia,
        "cuit": cp.cuit,
        "direccion": cp.direccion,
        "telefono": cp.telefono,
        "email": cp.email,
        "notas": cp.notas,
        "condicion_iva": cp.condicion_iva
    }


@router.post("/clientes-proveedores")
def create_cliente_proveedor(
    cp: ClienteProveedorCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Crea un cliente o proveedor."""
    item = finanzas_service.create_cliente_proveedor(db, cp)
    return {
        "id": str(item.id),
        "razon_social": item.razon_social,
        "message": "Creado exitosamente"
    }


@router.put("/clientes-proveedores/{cp_id}")
def update_cliente_proveedor(
    cp_id: UUID,
    cp: ClienteProveedorUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Actualiza un cliente/proveedor."""
    item = finanzas_service.update_cliente_proveedor(db, cp_id, cp)
    if not item:
        raise HTTPException(status_code=404, detail="Cliente/Proveedor no encontrado")
    return {"message": "Actualizado", "id": str(item.id)}


@router.delete("/clientes-proveedores/{cp_id}")
def delete_cliente_proveedor(
    cp_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina un cliente/proveedor."""
    success = finanzas_service.delete_cliente_proveedor(db, cp_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cliente/Proveedor no encontrado")
    return {"message": "Eliminado"}


@router.get("/clientes-proveedores/{cp_id}/cuenta-corriente")
def get_cuenta_corriente(
    cp_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene cuenta corriente de un cliente/proveedor."""
    result = finanzas_service.get_cuenta_corriente(db, cp_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ============ BALANCES Y REPORTES ============

@router.get("/balance")
def get_balance(
    fecha_desde: date,
    fecha_hasta: date,
    proyecto_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene balance general del periodo (ingresos, egresos, balance)."""
    return finanzas_service.get_balance_general(db, fecha_desde, fecha_hasta, proyecto_id)


@router.get("/flujo-caja")
def get_flujo_caja(
    fecha_desde: date,
    fecha_hasta: date,
    cuenta_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene flujo de caja del periodo."""
    return finanzas_service.get_flujo_caja(db, fecha_desde, fecha_hasta, cuenta_id)


@router.get("/resumen-mensual")
def get_resumen_mensual(
    mes: int = Query(..., ge=1, le=12),
    anio: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Obtiene resumen financiero mensual con comparativa vs mes anterior."""
    return finanzas_service.get_resumen_mensual(db, mes, anio)


# ============ PRESUPUESTOS ============

@router.get("/presupuestos")
def get_presupuestos(
    proyecto_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Lista presupuestos."""
    items = finanzas_service.get_presupuestos(db, proyecto_id)
    return [
        {
            "id": str(p.id),
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "monto_total": float(p.monto_total),
            "fecha_inicio": p.fecha_inicio.isoformat() if p.fecha_inicio else None,
            "fecha_fin": p.fecha_fin.isoformat() if p.fecha_fin else None,
            "proyecto_id": str(p.proyecto_id) if p.proyecto_id else None
        }
        for p in items
    ]


@router.post("/presupuestos")
def create_presupuesto(
    presupuesto: PresupuestoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Crea un presupuesto."""
    p = finanzas_service.create_presupuesto(db, presupuesto)
    return {"id": str(p.id), "nombre": p.nombre, "message": "Presupuesto creado"}


@router.put("/presupuestos/{presupuesto_id}")
def update_presupuesto(
    presupuesto_id: UUID,
    presupuesto: PresupuestoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza un presupuesto."""
    p = finanzas_service.update_presupuesto(db, presupuesto_id, presupuesto)
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return {"message": "Presupuesto actualizado", "id": str(p.id)}


@router.delete("/presupuestos/{presupuesto_id}")
def delete_presupuesto(
    presupuesto_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina un presupuesto."""
    success = finanzas_service.delete_presupuesto(db, presupuesto_id)
    if not success:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return {"message": "Presupuesto eliminado"}
