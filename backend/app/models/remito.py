from sqlalchemy import (
    Column, String, Text, Numeric, ForeignKey, Integer, Sequence, Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


# Secuencia PostgreSQL para numero correlativo de remitos.
# Atomica: cada nextval() devuelve un valor unico aunque haya inserts concurrentes.
remito_numero_seq = Sequence("remito_numero_seq", start=1, increment=1)


class Remito(Base, BaseModel):
    """Remito de salida de materiales desde un deposito o subdeposito.

    El numero es correlativo y se formatea como REM-XXXX al exponer.
    El destinatario es opcional (proyecto por defecto, o texto libre).
    """
    __tablename__ = "remitos"

    numero = Column(
        Integer,
        remito_numero_seq,
        server_default=remito_numero_seq.next_value(),
        nullable=False,
        unique=True,
        index=True,
    )
    fecha = Column(Date, nullable=False, index=True)

    deposito_id = Column(
        UUID(as_uuid=True),
        ForeignKey("depositos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    proyecto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Destinatario libre cuando no hay proyecto. Opcional.
    destinatario_texto = Column(String(255), nullable=True)
    responsable_retira = Column(String(255), nullable=True)
    direccion_entrega = Column(String(255), nullable=True)
    transportista = Column(String(255), nullable=True)
    observaciones = Column(Text, nullable=True)

    # Quien creo el remito en el sistema.
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    deposito = relationship("Deposito", lazy="joined")
    proyecto = relationship("Proyecto", lazy="joined")
    usuario = relationship("Usuario", lazy="joined")
    items = relationship(
        "RemitoItem",
        back_populates="remito",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    @property
    def numero_formateado(self) -> str:
        return f"REM-{self.numero:04d}"

    def __repr__(self):
        return f"<Remito {self.numero_formateado} deposito={self.deposito_id}>"


class RemitoItem(Base, BaseModel):
    """Linea de detalle de un remito. Snapshot del material para que el
    remito sea historicamente correcto aunque renombren/borren materiales.
    """
    __tablename__ = "remito_items"

    remito_id = Column(
        UUID(as_uuid=True),
        ForeignKey("remitos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    material_id = Column(
        UUID(as_uuid=True),
        ForeignKey("materiales.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    material_codigo = Column(String(50), nullable=True)
    material_nombre = Column(String(200), nullable=False)
    material_unidad = Column(String(50), nullable=False)
    cantidad = Column(Numeric(12, 4), nullable=False)

    remito = relationship("Remito", back_populates="items")
    material = relationship("Material", lazy="joined")

    def __repr__(self):
        return f"<RemitoItem {self.material_nombre} x{self.cantidad}>"
