from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class Socio(Base, BaseModel):
    """Socio de la empresa. Recibe una porcion de las ganancias."""
    __tablename__ = "socios"

    nombre = Column(String(150), nullable=False)
    apellido = Column(String(150), nullable=True)
    porcentaje_participacion = Column(Numeric(5, 2), nullable=False, default=50)
    email = Column(String(150), nullable=True)
    telefono = Column(String(50), nullable=True)
    notas = Column(Text, nullable=True)

    # Relacion opcional con un usuario del sistema
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True, unique=True)

    usuario = relationship("Usuario", backref="socio")
    aportes = relationship("AporteSocio", back_populates="socio", cascade="all, delete-orphan")
    retiros = relationship("RetiroSocio", back_populates="socio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Socio {self.nombre} {self.apellido or ''} ({self.porcentaje_participacion}%)>"


class AporteSocio(Base, BaseModel):
    """Aporte de capital que un socio hace a la empresa. Cuenta como ingreso."""
    __tablename__ = "aportes_socio"

    socio_id = Column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha = Column(Date, nullable=False)
    concepto = Column(String(300), nullable=True)
    observaciones = Column(Text, nullable=True)

    cuenta_id = Column(UUID(as_uuid=True), ForeignKey("cuentas.id"), nullable=True)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    socio = relationship("Socio", back_populates="aportes")
    cuenta = relationship("Cuenta")
    creador = relationship("Usuario", foreign_keys=[creado_por_id])

    def __repr__(self):
        return f"<AporteSocio socio={self.socio_id} ${self.monto}>"


class RetiroSocio(Base, BaseModel):
    """Retiro que un socio hace de su ganancia acumulada."""
    __tablename__ = "retiros_socio"

    socio_id = Column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha = Column(Date, nullable=False)
    concepto = Column(String(300), nullable=True)
    observaciones = Column(Text, nullable=True)

    cuenta_id = Column(UUID(as_uuid=True), ForeignKey("cuentas.id"), nullable=True)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    socio = relationship("Socio", back_populates="retiros")
    cuenta = relationship("Cuenta")
    creador = relationship("Usuario", foreign_keys=[creado_por_id])

    def __repr__(self):
        return f"<RetiroSocio socio={self.socio_id} ${self.monto}>"
