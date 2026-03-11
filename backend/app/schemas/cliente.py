from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date
from uuid import UUID
from enum import Enum


class TipoCliente(str, Enum):
    PARTICULAR = "particular"
    EMPRESA = "empresa"
    GOBIERNO = "gobierno"
    CONSTRUCTORA = "constructora"
    CONSORCIO = "consorcio"
    OTRO = "otro"


class CondicionIVA(str, Enum):
    RESPONSABLE_INSCRIPTO = "responsable_inscripto"
    MONOTRIBUTO = "monotributo"
    EXENTO = "exento"
    CONSUMIDOR_FINAL = "consumidor_final"
    NO_RESPONSABLE = "no_responsable"


# ============ CLIENTE ============

class ClienteBase(BaseModel):
    tipo: TipoCliente = TipoCliente.PARTICULAR
    razon_social: str = Field(..., min_length=2, max_length=200)
    nombre_fantasia: Optional[str] = None
    cuit: Optional[str] = None
    condicion_iva: CondicionIVA = CondicionIVA.CONSUMIDOR_FINAL
    email: Optional[str] = None
    telefono: Optional[str] = None
    celular: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_cargo: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = "Buenos Aires"
    codigo_postal: Optional[str] = None
    descuento_general: float = 0
    limite_credito: Optional[float] = None
    dias_credito: int = 0
    enviar_notificaciones: bool = True
    notas: Optional[str] = None
    notas_internas: Optional[str] = None


class ClienteCreate(ClienteBase):
    class Config:
        use_enum_values = True


class ClienteUpdate(BaseModel):
    tipo: Optional[TipoCliente] = None
    razon_social: Optional[str] = None
    nombre_fantasia: Optional[str] = None
    cuit: Optional[str] = None
    condicion_iva: Optional[CondicionIVA] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    celular: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_cargo: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None
    descuento_general: Optional[float] = None
    limite_credito: Optional[float] = None
    dias_credito: Optional[int] = None
    enviar_notificaciones: Optional[bool] = None
    notas: Optional[str] = None
    notas_internas: Optional[str] = None

    class Config:
        use_enum_values = True


class ClienteInDB(ClienteBase):
    id: UUID
    codigo: str
    saldo_cuenta_corriente: float = 0
    fecha_alta: Optional[date] = None
    fecha_ultimo_proyecto: Optional[date] = None
    usuario_id: Optional[UUID] = None
    activo: bool

    class Config:
        from_attributes = True


class ClienteResponse(ClienteInDB):
    nombre_display: str = ""
    tiene_deuda: bool = False
    cantidad_proyectos: int = 0
    usuario_email: Optional[str] = None


class ClienteListItem(BaseModel):
    """Schema simplificado para listas y selectores."""
    id: UUID
    codigo: str
    razon_social: str
    nombre_fantasia: Optional[str] = None
    tipo: TipoCliente
    cuit: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    ciudad: Optional[str] = None
    saldo_cuenta_corriente: float = 0
    activo: bool

    class Config:
        from_attributes = True


# ============ CUENTA CORRIENTE ============

class TipoMovimientoCC(str, Enum):
    CARGO = "cargo"
    PAGO = "pago"
    AJUSTE = "ajuste"


class MovimientoCuentaCorriente(BaseModel):
    id: UUID
    tipo: TipoMovimientoCC
    concepto: str
    monto: float
    fecha: date
    saldo_anterior: float
    saldo_posterior: float
    referencia: Optional[str] = None
    proyecto_nombre: Optional[str] = None


class EstadoCuentaCliente(BaseModel):
    cliente_id: UUID
    cliente_nombre: str
    saldo_actual: float
    limite_credito: Optional[float]
    credito_disponible: Optional[float]
    total_facturado_mes: float
    total_pagado_mes: float
    proyectos_activos: int
    dias_factura_mas_antigua: Optional[int]


class RegistroPagoCreate(BaseModel):
    monto: float = Field(..., gt=0)
    fecha: date
    metodo_pago: str = "efectivo"
    referencia: Optional[str] = None
    notas: Optional[str] = None
    proyecto_id: Optional[UUID] = None


class PagoResponse(BaseModel):
    id: UUID
    cliente_id: UUID
    monto: float
    fecha: date
    metodo_pago: str
    referencia: Optional[str]
    numero_recibo: str
    saldo_anterior: float
    saldo_posterior: float


# ============ USUARIO CLIENTE ============

class UsuarioClienteCreate(BaseModel):
    """Schema para crear usuario de acceso al portal para el cliente."""
    email: str
    nombre: str
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    password: Optional[str] = None  # Si no se provee, se genera automaticamente


class UsuarioClienteResponse(BaseModel):
    id: UUID
    email: str
    nombre: str
    apellido: Optional[str]
    activo: bool
    password_visible: Optional[str] = None  # Solo se muestra al crear


# ============ PROYECTOS DEL CLIENTE ============

class ProyectoClienteResumen(BaseModel):
    id: UUID
    nombre: str
    estado: str
    porcentaje_avance: float
    fecha_inicio: Optional[date]
    fecha_fin_estimada: Optional[date]
    monto_contratado: Optional[float]


class ClienteConProyectos(ClienteResponse):
    proyectos: List[ProyectoClienteResumen] = []
