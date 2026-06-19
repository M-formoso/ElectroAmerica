from sqlalchemy import Column, String, Text, Date, Enum, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum


class EstadoProyecto(str, enum.Enum):
    """Estados posibles de un proyecto."""
    planificacion = "planificacion"
    en_ejecucion = "en_ejecucion"
    pausado = "pausado"
    finalizado = "finalizado"


class EstadoFacturacion(str, enum.Enum):
    """Estados de facturación/cobro de un proyecto finalizado."""
    pendiente = "pendiente"
    facturado = "facturado"
    cobrado = "cobrado"


class Proyecto(Base, BaseModel):
    """Modelo de proyecto/obra."""
    __tablename__ = "proyectos"

    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)
    ubicacion = Column(String(255), nullable=True)
    fecha_inicio = Column(Date, nullable=True)
    fecha_fin_estimada = Column(Date, nullable=True)
    fecha_fin_real = Column(Date, nullable=True)
    estado = Column(Enum(EstadoProyecto), default=EstadoProyecto.planificacion, nullable=False)
    porcentaje_avance = Column(Numeric(5, 2), default=0, nullable=False)
    monto_contratado = Column(Numeric(15, 2), nullable=True)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    # Fuente de materiales: null = stock global, valor = deposito especifico
    deposito_id = Column(UUID(as_uuid=True), ForeignKey("depositos.id"), nullable=True)
    # Lista de precios usada por el proyecto. Al cargar una actividad, el
    # precio se congela en ProyectoActividad.precio_unitario_snapshot.
    lista_precio_id = Column(
        UUID(as_uuid=True),
        ForeignKey("listas_precio.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Facturación y cobro del proyecto finalizado.
    estado_facturacion = Column(
        Enum(EstadoFacturacion),
        default=EstadoFacturacion.pendiente,
        nullable=False,
    )
    numero_factura = Column(String(60), nullable=True)
    fecha_facturacion = Column(Date, nullable=True)
    fecha_cobro = Column(Date, nullable=True)
    monto_facturado = Column(Numeric(15, 2), nullable=True)

    # Relaciones
    cliente = relationship(
        "Cliente",
        foreign_keys=[cliente_id],
        backref="proyectos"
    )
    supervisor = relationship(
        "Usuario",
        foreign_keys=[supervisor_id]
    )
    deposito = relationship(
        "Deposito",
        foreign_keys=[deposito_id]
    )
    lista_precio = relationship(
        "ListaPrecio",
        foreign_keys=[lista_precio_id]
    )
    etapas = relationship(
        "Etapa",
        back_populates="proyecto",
        cascade="all, delete-orphan",
        order_by="Etapa.orden"
    )
    fotos = relationship(
        "Foto",
        back_populates="proyecto",
        cascade="all, delete-orphan"
    )
    gastos = relationship(
        "Gasto",
        back_populates="proyecto"
    )
    asignaciones_material = relationship(
        "AsignacionMaterial",
        back_populates="proyecto"
    )
    asignaciones_equipo = relationship(
        "AsignacionEquipo",
        back_populates="proyecto"
    )
    reportes = relationship(
        "Reporte",
        back_populates="proyecto",
        cascade="all, delete-orphan"
    )

    @property
    def cliente_nombre(self):
        """Nombre del cliente para mostrar (razon_social/nombre_fantasia)."""
        return self.cliente.nombre_display if self.cliente else None

    @property
    def deposito_nombre(self):
        """Nombre del deposito asociado al proyecto, si tiene."""
        return self.deposito.nombre if self.deposito else None

    def __repr__(self):
        return f"<Proyecto {self.nombre}>"
