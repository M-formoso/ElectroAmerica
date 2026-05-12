from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import random
import string

from app.models.cliente import Cliente, TipoCliente, CondicionIVA
from app.models.usuario import Usuario, RolUsuario
from app.models.proyecto import Proyecto
from app.models.transaccion import Transaccion, TipoTransaccion
from app.schemas.cliente import (
    ClienteCreate, ClienteUpdate, ClienteResponse, ClienteListItem,
    EstadoCuentaCliente, MovimientoCuentaCorriente, RegistroPagoCreate,
    PagoResponse, UsuarioClienteCreate, UsuarioClienteResponse,
    ProyectoClienteResumen, ClienteConProyectos
)
from app.core.security import hashear_password


def generar_codigo_cliente(db: Session) -> str:
    """Genera un codigo unico para el cliente."""
    while True:
        # Formato: CLI-XXXX (4 digitos)
        numero = random.randint(1000, 9999)
        codigo = f"CLI-{numero}"

        existe = db.query(Cliente).filter(Cliente.codigo == codigo).first()
        if not existe:
            return codigo


def generar_password_aleatorio(length: int = 8) -> str:
    """Genera una contraseña aleatoria."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(length))


def get_clientes(
    db: Session,
    tipo: Optional[TipoCliente] = None,
    activo: Optional[bool] = True,
    con_deuda: Optional[bool] = None,
    buscar: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Cliente]:
    """Obtiene lista de clientes con filtros."""
    query = db.query(Cliente)

    if activo is not None:
        query = query.filter(Cliente.activo == activo)

    if tipo:
        query = query.filter(Cliente.tipo == tipo)

    if con_deuda is True:
        query = query.filter(Cliente.saldo_cuenta_corriente > 0)
    elif con_deuda is False:
        query = query.filter(Cliente.saldo_cuenta_corriente <= 0)

    if buscar:
        buscar_like = f"%{buscar}%"
        query = query.filter(
            or_(
                Cliente.codigo.ilike(buscar_like),
                Cliente.razon_social.ilike(buscar_like),
                Cliente.nombre_fantasia.ilike(buscar_like),
                Cliente.cuit.ilike(buscar_like),
                Cliente.email.ilike(buscar_like)
            )
        )

    return query.order_by(Cliente.razon_social).offset(skip).limit(limit).all()


def get_cliente(db: Session, cliente_id: UUID) -> Optional[Cliente]:
    """Obtiene un cliente por ID."""
    return db.query(Cliente).filter(
        Cliente.id == cliente_id,
        Cliente.activo == True
    ).first()


def get_cliente_by_codigo(db: Session, codigo: str) -> Optional[Cliente]:
    """Obtiene un cliente por codigo."""
    return db.query(Cliente).filter(
        Cliente.codigo == codigo,
        Cliente.activo == True
    ).first()


def get_cliente_by_cuit(db: Session, cuit: str) -> Optional[Cliente]:
    """Obtiene un cliente por CUIT."""
    return db.query(Cliente).filter(
        Cliente.cuit == cuit,
        Cliente.activo == True
    ).first()


def create_cliente(db: Session, cliente: ClienteCreate) -> Cliente:
    """Crea un nuevo cliente."""
    # Verificar CUIT unico si se proporciona
    if cliente.cuit:
        existente = get_cliente_by_cuit(db, cliente.cuit)
        if existente:
            raise ValueError(f"Ya existe un cliente con CUIT {cliente.cuit}")

    db_cliente = Cliente(
        codigo=generar_codigo_cliente(db),
        fecha_alta=date.today(),
        **cliente.model_dump()
    )

    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


def update_cliente(db: Session, cliente_id: UUID, cliente: ClienteUpdate) -> Optional[Cliente]:
    """Actualiza un cliente."""
    db_cliente = get_cliente(db, cliente_id)
    if not db_cliente:
        return None

    update_data = cliente.model_dump(exclude_unset=True)

    # Verificar CUIT unico si se actualiza
    if "cuit" in update_data and update_data["cuit"]:
        existente = db.query(Cliente).filter(
            Cliente.cuit == update_data["cuit"],
            Cliente.id != cliente_id,
            Cliente.activo == True
        ).first()
        if existente:
            raise ValueError(f"Ya existe un cliente con CUIT {update_data['cuit']}")

    for field, value in update_data.items():
        setattr(db_cliente, field, value)

    db.commit()
    db.refresh(db_cliente)
    return db_cliente


def delete_cliente(db: Session, cliente_id: UUID) -> bool:
    """Desactiva un cliente (soft delete)."""
    db_cliente = get_cliente(db, cliente_id)
    if not db_cliente:
        return False

    # No permitir eliminar si tiene deuda
    if db_cliente.tiene_deuda:
        raise ValueError("No se puede eliminar un cliente con deuda pendiente")

    db_cliente.activo = False
    db.commit()
    return True


def get_cliente_response(db: Session, cliente: Cliente) -> ClienteResponse:
    """Convierte un cliente a response con datos adicionales."""
    # Contar proyectos
    cantidad_proyectos = db.query(func.count(Proyecto.id)).filter(
        Proyecto.cliente_id == cliente.id,
        Proyecto.activo == True
    ).scalar() or 0

    # Obtener email del usuario vinculado
    usuario_email = None
    if cliente.usuario_id:
        usuario = db.query(Usuario).filter(Usuario.id == cliente.usuario_id).first()
        if usuario:
            usuario_email = usuario.email

    return ClienteResponse(
        id=cliente.id,
        codigo=cliente.codigo,
        tipo=cliente.tipo,
        razon_social=cliente.razon_social,
        nombre_fantasia=cliente.nombre_fantasia,
        cuit=cliente.cuit,
        condicion_iva=cliente.condicion_iva,
        email=cliente.email,
        telefono=cliente.telefono,
        celular=cliente.celular,
        contacto_nombre=cliente.contacto_nombre,
        contacto_cargo=cliente.contacto_cargo,
        direccion=cliente.direccion,
        ciudad=cliente.ciudad,
        provincia=cliente.provincia,
        codigo_postal=cliente.codigo_postal,
        descuento_general=float(cliente.descuento_general or 0),
        limite_credito=float(cliente.limite_credito) if cliente.limite_credito else None,
        dias_credito=int(cliente.dias_credito or 0),
        enviar_notificaciones=cliente.enviar_notificaciones,
        notas=cliente.notas,
        notas_internas=cliente.notas_internas,
        saldo_cuenta_corriente=float(cliente.saldo_cuenta_corriente or 0),
        fecha_alta=cliente.fecha_alta,
        fecha_ultimo_proyecto=cliente.fecha_ultimo_proyecto,
        usuario_id=cliente.usuario_id,
        activo=cliente.activo,
        nombre_display=cliente.nombre_display,
        tiene_deuda=cliente.tiene_deuda,
        cantidad_proyectos=cantidad_proyectos,
        usuario_email=usuario_email
    )


# ============ CUENTA CORRIENTE ============

def get_estado_cuenta(db: Session, cliente_id: UUID) -> Optional[EstadoCuentaCliente]:
    """Obtiene el estado de cuenta de un cliente."""
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        return None

    hoy = date.today()
    primer_dia_mes = date(hoy.year, hoy.month, 1)

    # Total facturado este mes (egresos del cliente = ingresos nuestros)
    total_facturado = db.query(func.sum(Transaccion.monto)).filter(
        Transaccion.cliente_proveedor_id == cliente_id,
        Transaccion.tipo == TipoTransaccion.INGRESO.value,
        Transaccion.fecha >= primer_dia_mes,
        Transaccion.activo == True
    ).scalar() or 0

    # Total pagado este mes
    total_pagado = db.query(func.sum(Transaccion.monto)).filter(
        Transaccion.cliente_proveedor_id == cliente_id,
        Transaccion.tipo == TipoTransaccion.EGRESO.value,
        Transaccion.concepto.ilike("%pago%"),
        Transaccion.fecha >= primer_dia_mes,
        Transaccion.activo == True
    ).scalar() or 0

    # Proyectos activos del cliente
    proyectos_activos = db.query(func.count(Proyecto.id)).filter(
        Proyecto.cliente_id == cliente.id,
        Proyecto.activo == True,
        Proyecto.estado.in_(["planificacion", "en_ejecucion"])
    ).scalar() or 0

    # Credito disponible
    credito_disponible = None
    if cliente.limite_credito:
        credito_disponible = float(cliente.limite_credito) - float(cliente.saldo_cuenta_corriente or 0)

    return EstadoCuentaCliente(
        cliente_id=cliente.id,
        cliente_nombre=cliente.nombre_display,
        saldo_actual=float(cliente.saldo_cuenta_corriente or 0),
        limite_credito=float(cliente.limite_credito) if cliente.limite_credito else None,
        credito_disponible=credito_disponible,
        total_facturado_mes=float(total_facturado),
        total_pagado_mes=float(total_pagado),
        proyectos_activos=proyectos_activos,
        dias_factura_mas_antigua=None  # TODO: calcular
    )


def get_movimientos_cuenta(
    db: Session,
    cliente_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 50
) -> List[MovimientoCuentaCorriente]:
    """Obtiene los movimientos de cuenta corriente de un cliente."""
    query = db.query(Transaccion).filter(
        Transaccion.cliente_proveedor_id == cliente_id,
        Transaccion.activo == True
    )

    if fecha_desde:
        query = query.filter(Transaccion.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Transaccion.fecha <= fecha_hasta)

    transacciones = query.order_by(Transaccion.fecha.desc()).offset(skip).limit(limit).all()

    movimientos = []
    for t in transacciones:
        tipo_mov = "cargo" if t.tipo == TipoTransaccion.INGRESO.value else "pago"

        # Obtener nombre del proyecto si existe
        proyecto_nombre = None
        if t.proyecto_id:
            proyecto = db.query(Proyecto).filter(Proyecto.id == t.proyecto_id).first()
            if proyecto:
                proyecto_nombre = proyecto.nombre

        movimientos.append(MovimientoCuentaCorriente(
            id=t.id,
            tipo=tipo_mov,
            concepto=t.concepto,
            monto=float(t.monto),
            fecha=t.fecha,
            saldo_anterior=0,  # TODO: calcular
            saldo_posterior=0,  # TODO: calcular
            referencia=t.numero_comprobante,
            proyecto_nombre=proyecto_nombre
        ))

    return movimientos


def registrar_pago(
    db: Session,
    cliente_id: UUID,
    pago: RegistroPagoCreate,
    usuario_id: UUID
) -> PagoResponse:
    """Registra un pago del cliente."""
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        raise ValueError("Cliente no encontrado")

    saldo_anterior = float(cliente.saldo_cuenta_corriente or 0)
    saldo_posterior = saldo_anterior - pago.monto

    # Generar numero de recibo
    numero_recibo = f"REC-{date.today().strftime('%y%m%d')}-{random.randint(1000, 9999)}"

    # Crear transaccion de pago (egreso desde perspectiva del cliente)
    transaccion = Transaccion(
        tipo=TipoTransaccion.EGRESO.value,
        concepto=f"Pago recibido - {numero_recibo}",
        descripcion=pago.notas,
        monto=pago.monto,
        fecha=pago.fecha,
        metodo_pago=pago.metodo_pago,
        referencia_pago=pago.referencia,
        numero_comprobante=numero_recibo,
        cliente_proveedor_id=cliente_id,
        proyecto_id=pago.proyecto_id,
        creado_por_id=usuario_id
    )

    db.add(transaccion)

    # Actualizar saldo del cliente
    cliente.saldo_cuenta_corriente = Decimal(str(saldo_posterior))

    db.commit()
    db.refresh(transaccion)

    return PagoResponse(
        id=transaccion.id,
        cliente_id=cliente_id,
        monto=pago.monto,
        fecha=pago.fecha,
        metodo_pago=pago.metodo_pago,
        referencia=pago.referencia,
        numero_recibo=numero_recibo,
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior
    )


# ============ USUARIO CLIENTE ============

def crear_usuario_cliente(
    db: Session,
    cliente_id: UUID,
    datos: UsuarioClienteCreate
) -> UsuarioClienteResponse:
    """Crea un usuario de acceso al portal para el cliente."""
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        raise ValueError("Cliente no encontrado")

    if cliente.usuario_id:
        raise ValueError("El cliente ya tiene un usuario asociado")

    # Verificar que el email no exista
    email_existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if email_existe:
        raise ValueError(f"Ya existe un usuario con el email {datos.email}")

    # Generar password si no se proporciona
    password = datos.password or generar_password_aleatorio()

    # Crear usuario
    usuario = Usuario(
        email=datos.email,
        hashed_password=hashear_password(password),
        nombre=datos.nombre,
        apellido=datos.apellido,
        telefono=datos.telefono,
        rol=RolUsuario.cliente
    )

    db.add(usuario)
    db.flush()

    # Vincular con cliente
    cliente.usuario_id = usuario.id

    db.commit()
    db.refresh(usuario)

    return UsuarioClienteResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        activo=usuario.activo,
        password_visible=password  # Solo se muestra al crear
    )


def get_usuario_cliente(db: Session, cliente_id: UUID) -> Optional[UsuarioClienteResponse]:
    """Obtiene el usuario asociado a un cliente."""
    cliente = get_cliente(db, cliente_id)
    if not cliente or not cliente.usuario_id:
        return None

    usuario = db.query(Usuario).filter(Usuario.id == cliente.usuario_id).first()
    if not usuario:
        return None

    return UsuarioClienteResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        activo=usuario.activo
    )


def reset_password_usuario_cliente(db: Session, cliente_id: UUID) -> str:
    """Resetea la contraseña del usuario cliente."""
    cliente = get_cliente(db, cliente_id)
    if not cliente or not cliente.usuario_id:
        raise ValueError("El cliente no tiene usuario asociado")

    usuario = db.query(Usuario).filter(Usuario.id == cliente.usuario_id).first()
    if not usuario:
        raise ValueError("Usuario no encontrado")

    nuevo_password = generar_password_aleatorio()
    usuario.hashed_password = hashear_password(nuevo_password)

    db.commit()

    return nuevo_password


# ============ PROYECTOS DEL CLIENTE ============

def get_proyectos_cliente(db: Session, cliente_id: UUID) -> List[ProyectoClienteResumen]:
    """Obtiene los proyectos de un cliente."""
    cliente = get_cliente(db, cliente_id)
    if not cliente or not cliente.usuario_id:
        return []

    proyectos = db.query(Proyecto).filter(
        Proyecto.cliente_id == cliente.id,
        Proyecto.activo == True
    ).order_by(Proyecto.created_at.desc()).all()

    return [
        ProyectoClienteResumen(
            id=p.id,
            nombre=p.nombre,
            estado=p.estado.value if hasattr(p.estado, 'value') else str(p.estado),
            porcentaje_avance=float(p.porcentaje_avance or 0),
            fecha_inicio=p.fecha_inicio,
            fecha_fin_estimada=p.fecha_fin_estimada,
            monto_contratado=float(p.monto_contratado) if p.monto_contratado else None
        )
        for p in proyectos
    ]


def get_cliente_con_proyectos(db: Session, cliente_id: UUID) -> Optional[ClienteConProyectos]:
    """Obtiene un cliente con sus proyectos."""
    cliente = get_cliente(db, cliente_id)
    if not cliente:
        return None

    cliente_response = get_cliente_response(db, cliente)
    proyectos = get_proyectos_cliente(db, cliente_id)

    return ClienteConProyectos(
        **cliente_response.model_dump(),
        proyectos=proyectos
    )


# ============ LISTA SIMPLE ============

def get_clientes_lista(db: Session) -> List[ClienteListItem]:
    """Obtiene lista simplificada de clientes para selectores."""
    clientes = db.query(Cliente).filter(Cliente.activo == True).order_by(Cliente.razon_social).all()

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


# ============ ESTADISTICAS ============

def get_estadisticas_clientes(db: Session) -> dict:
    """Obtiene estadísticas generales de clientes."""
    total = db.query(func.count(Cliente.id)).filter(Cliente.activo == True).scalar() or 0
    con_deuda = db.query(func.count(Cliente.id)).filter(
        Cliente.activo == True,
        Cliente.saldo_cuenta_corriente > 0
    ).scalar() or 0

    total_deuda = db.query(func.sum(Cliente.saldo_cuenta_corriente)).filter(
        Cliente.activo == True,
        Cliente.saldo_cuenta_corriente > 0
    ).scalar() or 0

    # Por tipo
    por_tipo = db.query(
        Cliente.tipo,
        func.count(Cliente.id)
    ).filter(Cliente.activo == True).group_by(Cliente.tipo).all()

    return {
        "total_clientes": total,
        "clientes_con_deuda": con_deuda,
        "total_deuda": float(total_deuda),
        "por_tipo": [{"tipo": getattr(t, "value", t), "cantidad": c} for t, c in por_tipo]
    }
