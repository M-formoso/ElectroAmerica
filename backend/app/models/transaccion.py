from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class TipoTransaccion(str, enum.Enum):
    """Tipo de transaccion financiera."""
    INGRESO = "ingreso"
    EGRESO = "egreso"


class MetodoPago(str, enum.Enum):
    """Metodo de pago utilizado."""
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    TARJETA_DEBITO = "tarjeta_debito"
    TARJETA_CREDITO = "tarjeta_credito"
    CHEQUE = "cheque"
    MERCADO_PAGO = "mercado_pago"
    OTRO = "otro"


class EstadoTransaccion(str, enum.Enum):
    """Estado de la transaccion."""
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    ANULADA = "anulada"


class Transaccion(Base, BaseModel):
    """Modelo de transaccion financiera (ingreso o egreso)."""
    __tablename__ = "transacciones"

    tipo = Column(Enum(TipoTransaccion), nullable=False)
    concepto = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha = Column(Date, nullable=False)

    # Metodo de pago
    metodo_pago = Column(Enum(MetodoPago), default=MetodoPago.EFECTIVO)
    referencia_pago = Column(String(100), nullable=True)  # Nro cheque, transferencia, etc.

    # Estado
    estado = Column(Enum(EstadoTransaccion), default=EstadoTransaccion.CONFIRMADA)

    # Comprobante
    numero_comprobante = Column(String(100), nullable=True)
    tipo_comprobante = Column(String(50), nullable=True)  # Factura A, B, C, Recibo, etc.
    comprobante_url = Column(String(500), nullable=True)

    # Relaciones opcionales
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True)
    categoria_id = Column(UUID(as_uuid=True), ForeignKey("categorias_gasto.id"), nullable=True)
    cuenta_id = Column(UUID(as_uuid=True), ForeignKey("cuentas.id"), nullable=True)
    cliente_proveedor_id = Column(UUID(as_uuid=True), ForeignKey("clientes_proveedores.id"), nullable=True)

    # Auditoria
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    proyecto = relationship("Proyecto", backref="transacciones")
    categoria = relationship("CategoriaGasto")
    cuenta = relationship("Cuenta", back_populates="transacciones")
    cliente_proveedor = relationship("ClienteProveedor", back_populates="transacciones")
    creador = relationship("Usuario", foreign_keys=[creado_por_id])

    def __repr__(self):
        return f"<Transaccion {self.tipo.value} {self.concepto[:30]} ${self.monto}>"


class TipoCuenta(str, enum.Enum):
    """Tipo de cuenta financiera."""
    CAJA = "caja"
    BANCO = "banco"
    MERCADO_PAGO = "mercado_pago"
    OTRO = "otro"


class Cuenta(Base, BaseModel):
    """Cuenta financiera (caja, banco, etc.)."""
    __tablename__ = "cuentas"

    nombre = Column(String(100), nullable=False)
    tipo = Column(Enum(TipoCuenta), default=TipoCuenta.CAJA)
    descripcion = Column(String(300), nullable=True)
    numero_cuenta = Column(String(50), nullable=True)
    banco = Column(String(100), nullable=True)
    cbu = Column(String(30), nullable=True)
    alias = Column(String(50), nullable=True)
    saldo_inicial = Column(Numeric(12, 2), default=0)

    # Relaciones
    transacciones = relationship("Transaccion", back_populates="cuenta")

    @property
    def saldo_actual(self):
        """Calcula el saldo actual basado en transacciones."""
        from sqlalchemy import func
        from app.db.session import SessionLocal

        # Esto se calculara en el servicio para evitar queries N+1
        return None

    def __repr__(self):
        return f"<Cuenta {self.nombre} ({self.tipo.value})>"


class TipoClienteProveedor(str, enum.Enum):
    """Tipo de entidad."""
    CLIENTE = "cliente"
    PROVEEDOR = "proveedor"
    AMBOS = "ambos"


class ClienteProveedor(Base, BaseModel):
    """Cliente o proveedor para finanzas."""
    __tablename__ = "clientes_proveedores"

    tipo = Column(Enum(TipoClienteProveedor), default=TipoClienteProveedor.CLIENTE)
    razon_social = Column(String(200), nullable=False)
    nombre_fantasia = Column(String(200), nullable=True)
    cuit = Column(String(15), nullable=True)
    direccion = Column(String(300), nullable=True)
    telefono = Column(String(50), nullable=True)
    email = Column(String(150), nullable=True)
    notas = Column(Text, nullable=True)

    # Condicion fiscal
    condicion_iva = Column(String(50), nullable=True)  # RI, Monotributo, Exento, etc.

    # Relacion con usuario (si es cliente del sistema)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True, unique=True)

    # Relaciones
    usuario = relationship("Usuario", backref="cliente_proveedor")
    transacciones = relationship("Transaccion", back_populates="cliente_proveedor")

    def __repr__(self):
        return f"<ClienteProveedor {self.razon_social}>"


class Presupuesto(Base, BaseModel):
    """Presupuesto para un proyecto o periodo."""
    __tablename__ = "presupuestos"

    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    monto_total = Column(Numeric(12, 2), nullable=False)
    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)

    # Relacion con proyecto
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True)
    categoria_id = Column(UUID(as_uuid=True), ForeignKey("categorias_gasto.id"), nullable=True)

    # Relaciones
    proyecto = relationship("Proyecto", backref="presupuestos")
    categoria = relationship("CategoriaGasto")

    def __repr__(self):
        return f"<Presupuesto {self.nombre} ${self.monto_total}>"
