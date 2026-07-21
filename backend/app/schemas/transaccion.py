from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from uuid import UUID
from enum import Enum


class TipoTransaccion(str, Enum):
    INGRESO = "ingreso"
    EGRESO = "egreso"


class MetodoPago(str, Enum):
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    TARJETA_DEBITO = "tarjeta_debito"
    TARJETA_CREDITO = "tarjeta_credito"
    CHEQUE = "cheque"
    MERCADO_PAGO = "mercado_pago"
    OTRO = "otro"


class EstadoTransaccion(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    ANULADA = "anulada"


class TipoIngreso(str, Enum):
    COBRO_FACTURA_OBRA = "cobro_factura_obra"
    COBRO_FACTURA_VENTA = "cobro_factura_venta"
    APORTE_SOCIO = "aporte_socio"
    OTRO = "otro"


class TipoCuenta(str, Enum):
    CAJA = "caja"
    BANCO = "banco"
    MERCADO_PAGO = "mercado_pago"
    OTRO = "otro"


class TipoClienteProveedor(str, Enum):
    CLIENTE = "cliente"
    PROVEEDOR = "proveedor"
    AMBOS = "ambos"


# ============ TRANSACCION ============

class TransaccionBase(BaseModel):
    tipo: TipoTransaccion
    tipo_ingreso: Optional[TipoIngreso] = None
    concepto: str = Field(..., max_length=300)
    descripcion: Optional[str] = None
    monto: float = Field(..., gt=0)
    fecha: date
    metodo_pago: MetodoPago = MetodoPago.EFECTIVO
    referencia_pago: Optional[str] = None
    estado: EstadoTransaccion = EstadoTransaccion.CONFIRMADA
    numero_comprobante: Optional[str] = None
    tipo_comprobante: Optional[str] = None
    comprobante_url: Optional[str] = None
    proyecto_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None
    cuenta_id: Optional[UUID] = None
    cliente_proveedor_id: Optional[UUID] = None


class TransaccionCreate(TransaccionBase):
    class Config:
        use_enum_values = True


class TransaccionUpdate(BaseModel):
    tipo: Optional[TipoTransaccion] = None
    tipo_ingreso: Optional[TipoIngreso] = None
    concepto: Optional[str] = None
    descripcion: Optional[str] = None
    monto: Optional[float] = None
    fecha: Optional[date] = None
    metodo_pago: Optional[MetodoPago] = None
    referencia_pago: Optional[str] = None
    estado: Optional[EstadoTransaccion] = None
    numero_comprobante: Optional[str] = None
    tipo_comprobante: Optional[str] = None
    comprobante_url: Optional[str] = None
    proyecto_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None
    cuenta_id: Optional[UUID] = None
    cliente_proveedor_id: Optional[UUID] = None


class TransaccionInDB(TransaccionBase):
    id: UUID
    creado_por_id: UUID
    activo: bool
    created_at: date

    class Config:
        from_attributes = True


class TransaccionResponse(TransaccionInDB):
    proyecto_nombre: Optional[str] = None
    categoria_nombre: Optional[str] = None
    cuenta_nombre: Optional[str] = None
    cliente_proveedor_nombre: Optional[str] = None
    creador_nombre: Optional[str] = None


# ============ CUENTA ============

class CuentaBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    tipo: TipoCuenta = TipoCuenta.CAJA
    descripcion: Optional[str] = None
    numero_cuenta: Optional[str] = None
    banco: Optional[str] = None
    cbu: Optional[str] = None
    alias: Optional[str] = None
    saldo_inicial: float = 0


class CuentaCreate(CuentaBase):
    class Config:
        use_enum_values = True


class CuentaUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[TipoCuenta] = None
    descripcion: Optional[str] = None
    numero_cuenta: Optional[str] = None
    banco: Optional[str] = None
    cbu: Optional[str] = None
    alias: Optional[str] = None
    saldo_inicial: Optional[float] = None


class CuentaInDB(CuentaBase):
    id: UUID
    activo: bool

    class Config:
        from_attributes = True


class CuentaResponse(CuentaInDB):
    saldo_actual: float = 0
    total_ingresos: float = 0
    total_egresos: float = 0


# ============ CLIENTE/PROVEEDOR ============

class ClienteProveedorBase(BaseModel):
    tipo: TipoClienteProveedor = TipoClienteProveedor.CLIENTE
    razon_social: str = Field(..., max_length=200)
    nombre_fantasia: Optional[str] = None
    cuit: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    notas: Optional[str] = None
    condicion_iva: Optional[str] = None
    usuario_id: Optional[UUID] = None


class ClienteProveedorCreate(ClienteProveedorBase):
    class Config:
        use_enum_values = True


class ClienteProveedorUpdate(BaseModel):
    tipo: Optional[TipoClienteProveedor] = None
    razon_social: Optional[str] = None
    nombre_fantasia: Optional[str] = None
    cuit: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    notas: Optional[str] = None
    condicion_iva: Optional[str] = None
    usuario_id: Optional[UUID] = None


class ClienteProveedorInDB(ClienteProveedorBase):
    id: UUID
    activo: bool

    class Config:
        from_attributes = True


class ClienteProveedorResponse(ClienteProveedorInDB):
    saldo_cuenta_corriente: float = 0
    total_facturado: float = 0


# ============ PRESUPUESTO ============

class PresupuestoBase(BaseModel):
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    monto_total: float = Field(..., gt=0)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    proyecto_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None


class PresupuestoCreate(PresupuestoBase):
    pass


class PresupuestoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    monto_total: Optional[float] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    proyecto_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None


class PresupuestoInDB(PresupuestoBase):
    id: UUID
    activo: bool

    class Config:
        from_attributes = True


class PresupuestoResponse(PresupuestoInDB):
    monto_ejecutado: float = 0
    porcentaje_ejecutado: float = 0
    saldo_disponible: float = 0


# ============ BALANCES Y REPORTES ============

class BalanceGeneral(BaseModel):
    fecha_desde: date
    fecha_hasta: date
    total_ingresos: float
    total_egresos: float
    balance: float
    ingresos_por_categoria: list[dict]
    egresos_por_categoria: list[dict]
    ingresos_por_metodo_pago: list[dict]
    egresos_por_metodo_pago: list[dict]


class FlujoCaja(BaseModel):
    fecha: date
    saldo_inicial: float
    ingresos: float
    egresos: float
    saldo_final: float


class ResumenFinanciero(BaseModel):
    periodo: str
    ingresos_totales: float
    egresos_totales: float
    balance: float
    variacion_vs_anterior: float
    top_categorias_ingreso: list[dict]
    top_categorias_egreso: list[dict]
    flujo_caja_diario: list[FlujoCaja]
    cuentas: list[CuentaResponse]
