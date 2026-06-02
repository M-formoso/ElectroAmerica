from sqlalchemy import Column, String, Text, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class ListaPrecio(Base, BaseModel):
    """Lista de precios maestra que se asigna a un proyecto al crearlo.

    Cada empresa/cliente principal tiene su lista (EMA, MANTELECTRIC,
    ELECTROAMERICA). Los precios de cada actividad viven en
    `PrecioListaActividad`. Al cargar una tarea a un proyecto, el precio
    se "congela" en `ProyectoActividad.precio_unitario_snapshot`, asi los
    proyectos viejos no se ven afectados si despues se modifica la lista.
    """
    __tablename__ = "listas_precio"

    nombre = Column(String(120), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)

    precios = relationship(
        "PrecioListaActividad",
        back_populates="lista",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ListaPrecio {self.nombre}>"


class PrecioListaActividad(Base, BaseModel):
    """Precio de una actividad tipo dentro de una lista de precios."""
    __tablename__ = "precios_lista_actividad"
    __table_args__ = (
        UniqueConstraint(
            "lista_precio_id",
            "actividad_tipo_id",
            name="uq_precio_lista_actividad",
        ),
    )

    lista_precio_id = Column(
        UUID(as_uuid=True),
        ForeignKey("listas_precio.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actividad_tipo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("actividades_tipo.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    precio_unitario = Column(Numeric(12, 2), nullable=False, default=0)

    lista = relationship("ListaPrecio", back_populates="precios")
    actividad_tipo = relationship("ActividadTipo")

    def __repr__(self):
        return f"<PrecioListaActividad lista={self.lista_precio_id} act={self.actividad_tipo_id} ${self.precio_unitario}>"
