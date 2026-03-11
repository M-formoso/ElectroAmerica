from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import date

from app.core.deps import get_db, get_usuario_actual
from app.models.usuario import Usuario
from app.models.cliente import TipoCliente
from app.schemas.cliente import (
    ClienteCreate, ClienteUpdate, ClienteResponse, ClienteListItem,
    EstadoCuentaCliente, MovimientoCuentaCorriente, RegistroPagoCreate,
    PagoResponse, UsuarioClienteCreate, UsuarioClienteResponse,
    ProyectoClienteResumen, ClienteConProyectos
)
from app.services import cliente_service

router = APIRouter()


# ============ CRUD CLIENTES ============

@router.get("", response_model=List[ClienteListItem])
def listar_clientes(
    tipo: Optional[TipoCliente] = None,
    activo: Optional[bool] = True,
    con_deuda: Optional[bool] = None,
    buscar: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Lista todos los clientes con filtros."""
    clientes = cliente_service.get_clientes(
        db, tipo=tipo, activo=activo, con_deuda=con_deuda,
        buscar=buscar, skip=skip, limit=limit
    )

    return [
        ClienteListItem(
            id=c.id,
            codigo=c.codigo,
            razon_social=c.razon_social,
            nombre_fantasia=c.nombre_fantasia,
            tipo=c.tipo,
            cuit=c.cuit,
            telefono=c.telefono,
            email=c.email,
            ciudad=c.ciudad,
            saldo_cuenta_corriente=float(c.saldo_cuenta_corriente or 0),
            activo=c.activo
        )
        for c in clientes
    ]


@router.get("/lista", response_model=List[ClienteListItem])
def lista_clientes_simple(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Lista simplificada de clientes para selectores."""
    return cliente_service.get_clientes_lista(db)


@router.get("/tipos")
def obtener_tipos_cliente():
    """Obtiene los tipos de cliente disponibles."""
    return [{"value": t.value, "label": t.value.replace("_", " ").title()} for t in TipoCliente]


@router.get("/condiciones-iva")
def obtener_condiciones_iva():
    """Obtiene las condiciones de IVA disponibles."""
    from app.models.cliente import CondicionIVA
    labels = {
        "responsable_inscripto": "Responsable Inscripto",
        "monotributo": "Monotributo",
        "exento": "Exento",
        "consumidor_final": "Consumidor Final",
        "no_responsable": "No Responsable"
    }
    return [{"value": c.value, "label": labels.get(c.value, c.value)} for c in CondicionIVA]


@router.get("/estadisticas")
def obtener_estadisticas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene estadísticas generales de clientes."""
    return cliente_service.get_estadisticas_clientes(db)


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene el detalle de un cliente."""
    cliente = cliente_service.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return cliente_service.get_cliente_response(db, cliente)


@router.get("/{cliente_id}/completo", response_model=ClienteConProyectos)
def obtener_cliente_completo(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene el detalle completo de un cliente con proyectos."""
    cliente = cliente_service.get_cliente_con_proyectos(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return cliente


@router.post("", response_model=ClienteResponse)
def crear_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Crea un nuevo cliente."""
    try:
        db_cliente = cliente_service.create_cliente(db, cliente)
        return cliente_service.get_cliente_response(db, db_cliente)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: UUID,
    cliente: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Actualiza un cliente existente."""
    try:
        db_cliente = cliente_service.update_cliente(db, cliente_id, cliente)
        if not db_cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        return cliente_service.get_cliente_response(db, db_cliente)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{cliente_id}")
def eliminar_cliente(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Desactiva un cliente (soft delete)."""
    try:
        success = cliente_service.delete_cliente(db, cliente_id)
        if not success:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        return {"message": "Cliente eliminado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ CUENTA CORRIENTE ============

@router.get("/{cliente_id}/cuenta-corriente", response_model=EstadoCuentaCliente)
def obtener_estado_cuenta(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene el estado de cuenta de un cliente."""
    estado = cliente_service.get_estado_cuenta(db, cliente_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return estado


@router.get("/{cliente_id}/movimientos", response_model=List[MovimientoCuentaCorriente])
def obtener_movimientos(
    cliente_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene los movimientos de cuenta corriente de un cliente."""
    return cliente_service.get_movimientos_cuenta(
        db, cliente_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip, limit=limit
    )


@router.post("/{cliente_id}/pagos", response_model=PagoResponse)
def registrar_pago(
    cliente_id: UUID,
    pago: RegistroPagoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Registra un pago de un cliente."""
    try:
        return cliente_service.registrar_pago(db, cliente_id, pago, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ USUARIO CLIENTE ============

@router.get("/{cliente_id}/usuario", response_model=Optional[UsuarioClienteResponse])
def obtener_usuario_cliente(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene el usuario asociado a un cliente."""
    return cliente_service.get_usuario_cliente(db, cliente_id)


@router.post("/{cliente_id}/usuario", response_model=UsuarioClienteResponse)
def crear_usuario_cliente(
    cliente_id: UUID,
    datos: UsuarioClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Crea un usuario de acceso al portal para el cliente."""
    try:
        return cliente_service.crear_usuario_cliente(db, cliente_id, datos)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{cliente_id}/usuario/reset-password")
def reset_password_usuario(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Resetea la contraseña del usuario cliente."""
    try:
        nuevo_password = cliente_service.reset_password_usuario_cliente(db, cliente_id)
        return {"password": nuevo_password}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ PROYECTOS ============

@router.get("/{cliente_id}/proyectos", response_model=List[ProyectoClienteResumen])
def obtener_proyectos_cliente(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_usuario_actual)
):
    """Obtiene los proyectos de un cliente."""
    return cliente_service.get_proyectos_cliente(db, cliente_id)
