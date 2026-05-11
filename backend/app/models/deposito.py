from sqlalchemy import Column, String, Text, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class Deposito(Base, BaseModel):
    """Deposito/stock fisico asociado a un cliente.

    Un cliente puede tener uno o varios depositos (deposito central,
    obra X, sucursal Y, etc.). Cada deposito tiene su propio stock
    de materiales.
    """
    __tablename__ = "depositos"

    cliente_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre = Column(String(200), nullable=False)
    direccion = Column(String(255), nullable=True)
    descripcion = Column(Text, nullable=True)

    cliente = relationship("Cliente", lazy="joined")
    materiales = relationship(
        "DepositoMaterial",
        back_populates="deposito",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Deposito {self.nombre} (cliente={self.cliente_id})>"


class DepositoMaterial(Base, BaseModel):
    """Stock de un material en un deposito especifico."""
    __tablename__ = "deposito_materiales"
    __table_args__ = (
        UniqueConstraint("deposito_id", "material_id", name="uq_deposito_material"),
    )

    deposito_id = Column(
        UUID(as_uuid=True),
        ForeignKey("depositos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    material_id = Column(
        UUID(as_uuid=True),
        ForeignKey("materiales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stock_actual = Column(Numeric(12, 4), nullable=False, default=0)
    stock_minimo = Column(Numeric(12, 4), nullable=False, default=0)

    deposito = relationship("Deposito", back_populates="materiales")
    material = relationship("Material", lazy="joined")

    def __repr__(self):
        return f"<DepositoMaterial deposito={self.deposito_id} material={self.material_id}>"
