from sqlalchemy import Column, String, Enum, Text, Date, Numeric, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class TipoCliente(str, enum.Enum):
    """Tipo de cliente."""
    PARTICULAR = "particular"
    EMPRESA = "empresa"
    GOBIERNO = "gobierno"
    CONSTRUCTORA = "constructora"
    CONSORCIO = "consorcio"
    OTRO = "otro"


class CondicionIVA(str, enum.Enum):
    """Condicion frente al IVA."""
    RESPONSABLE_INSCRIPTO = "responsable_inscripto"
    MONOTRIBUTO = "monotributo"
    EXENTO = "exento"
    CONSUMIDOR_FINAL = "consumidor_final"
    NO_RESPONSABLE = "no_responsable"


class Cliente(Base, BaseModel):
    """Modelo de cliente de la empresa."""
    __tablename__ = "clientes"

    # Codigo unico autogenerado
    codigo = Column(String(20), unique=True, nullable=False, index=True)

    # Tipo de cliente
    tipo = Column(Enum(TipoCliente), default=TipoCliente.PARTICULAR)

    # Datos basicos
    razon_social = Column(String(200), nullable=False)
    nombre_fantasia = Column(String(200), nullable=True)

    # Datos fiscales
    cuit = Column(String(15), unique=True, nullable=True, index=True)
    condicion_iva = Column(Enum(CondicionIVA), default=CondicionIVA.CONSUMIDOR_FINAL)

    # Contacto
    email = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    celular = Column(String(50), nullable=True)
    contacto_nombre = Column(String(100), nullable=True)
    contacto_cargo = Column(String(100), nullable=True)

    # Direccion
    direccion = Column(String(300), nullable=True)
    ciudad = Column(String(100), nullable=True)
    provincia = Column(String(100), default="Buenos Aires")
    codigo_postal = Column(String(10), nullable=True)

    # Comercial
    descuento_general = Column(Numeric(5, 2), default=0)
    limite_credito = Column(Numeric(12, 2), nullable=True)
    dias_credito = Column(Numeric(3, 0), default=0)

    # Estado de cuenta
    saldo_cuenta_corriente = Column(Numeric(12, 2), default=0)

    # Preferencias
    enviar_notificaciones = Column(Boolean, default=True)

    # Notas
    notas = Column(Text, nullable=True)
    notas_internas = Column(Text, nullable=True)

    # Fechas
    fecha_alta = Column(Date, nullable=True)
    fecha_ultimo_proyecto = Column(Date, nullable=True)

    # Relaciones - Usuario vinculado (acceso al portal)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True, unique=True)
    usuario = relationship("Usuario", backref="cliente_asociado", foreign_keys=[usuario_id])

    @property
    def nombre_display(self):
        """Retorna nombre fantasia o razon social."""
        return self.nombre_fantasia or self.razon_social

    @property
    def tiene_deuda(self):
        """Verifica si el cliente tiene deuda."""
        return self.saldo_cuenta_corriente and float(self.saldo_cuenta_corriente) > 0

    @property
    def supera_limite_credito(self):
        """Verifica si el cliente supera su limite de credito."""
        if not self.limite_credito:
            return False
        return self.saldo_cuenta_corriente and float(self.saldo_cuenta_corriente) > float(self.limite_credito)

    def __repr__(self):
        return f"<Cliente {self.codigo} - {self.razon_social}>"
