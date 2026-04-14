from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Date, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base, BaseModel
import enum


class EstadoRequerimiento(str, enum.Enum):
    """Estados del requerimiento de material para un proyecto."""
    estimado = "estimado"                    # Calculado automáticamente por el sistema
    aprobado = "aprobado"                    # Supervisor validó que se necesita
    pendiente_compra = "pendiente_compra"    # No hay stock, hay que comprar
    en_proceso_compra = "en_proceso_compra"  # Se solicitó al proveedor
    pendiente_entrega = "pendiente_entrega"  # Esperando entrega de empresa (EDEMSA, etc)
    pendiente_retiro = "pendiente_retiro"    # Está en depósito, hay que retirarlo
    entregado_obra = "entregado_obra"        # Ya está en la obra
    consumido = "consumido"                  # Ya se usó
    cancelado = "cancelado"                  # Ya no se necesita


class OrigenMaterial(str, enum.Enum):
    """Origen del material."""
    stock_propio = "stock_propio"            # Del depósito de Electro América
    compra = "compra"                        # Se compra a proveedor
    entrega_cliente = "entrega_cliente"      # Lo entrega la empresa cliente (EDEMSA, etc)


class PrioridadRequerimiento(str, enum.Enum):
    """Prioridad del requerimiento."""
    critica = "critica"    # Afecta habilitación, entrega o seguridad
    alta = "alta"          # Solicitado expresamente por el cliente
    media = "media"        # Según cronograma planificado
    baja = "baja"          # Puede postergarse sin impacto


class RequerimientoMaterial(Base, BaseModel):
    """
    Modelo de requerimiento de material para un proyecto.
    Representa la necesidad de un material específico, con estados y tracking completo.
    """
    __tablename__ = "requerimientos_material"

    # Relaciones principales
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id", ondelete="SET NULL"), nullable=True)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materiales.id", ondelete="CASCADE"), nullable=False)

    # Cantidades
    cantidad_estimada = Column(Numeric(12, 4), nullable=False)  # Lo que se calculó/estimó
    cantidad_aprobada = Column(Numeric(12, 4), nullable=True)   # Lo que se aprobó (puede diferir)
    cantidad_entregada = Column(Numeric(12, 4), default=0)      # Lo que ya se entregó a obra
    cantidad_consumida = Column(Numeric(12, 4), default=0)      # Lo que ya se usó

    # Estado y prioridad
    estado = Column(Enum(EstadoRequerimiento), default=EstadoRequerimiento.estimado, nullable=False)
    prioridad = Column(Enum(PrioridadRequerimiento), default=PrioridadRequerimiento.media, nullable=False)

    # Origen del material
    origen = Column(Enum(OrigenMaterial), nullable=True)
    empresa_origen_id = Column(UUID(as_uuid=True), ForeignKey("empresas_proveedoras.id"), nullable=True)

    # Si viene de una actividad tipo
    actividad_tipo_id = Column(UUID(as_uuid=True), ForeignKey("actividades_tipo.id"), nullable=True)
    cantidad_trabajo = Column(Numeric(12, 4), nullable=True)  # Cantidad de trabajo que generó este requerimiento

    # Fechas importantes
    fecha_necesidad = Column(Date, nullable=True)         # Cuándo se necesita en obra
    fecha_solicitud = Column(DateTime(timezone=True), nullable=True)  # Cuándo se solicitó compra/entrega
    fecha_entrega = Column(DateTime(timezone=True), nullable=True)    # Cuándo llegó

    # Notas y observaciones
    notas = Column(Text, nullable=True)
    notas_aprobacion = Column(Text, nullable=True)

    # Auditoría
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    aprobado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    fecha_aprobacion = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    proyecto = relationship("Proyecto", backref="requerimientos_material")
    etapa = relationship("Etapa", backref="requerimientos_material")
    material = relationship("Material", backref="requerimientos")
    actividad_tipo = relationship("ActividadTipo", backref="requerimientos_generados")
    empresa_origen = relationship("EmpresaProveedora", backref="entregas_material")
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
    aprobado_por = relationship("Usuario", foreign_keys=[aprobado_por_id])

    # Historial de cambios
    historial = relationship(
        "HistorialRequerimiento",
        back_populates="requerimiento",
        cascade="all, delete-orphan",
        order_by="desc(HistorialRequerimiento.created_at)"
    )

    @property
    def cantidad_pendiente(self) -> float:
        """Cantidad que falta entregar."""
        aprobada = float(self.cantidad_aprobada or self.cantidad_estimada or 0)
        entregada = float(self.cantidad_entregada or 0)
        return max(0, aprobada - entregada)

    @property
    def cantidad_disponible(self) -> float:
        """Cantidad disponible en obra (entregada - consumida)."""
        entregada = float(self.cantidad_entregada or 0)
        consumida = float(self.cantidad_consumida or 0)
        return max(0, entregada - consumida)

    def __repr__(self):
        return f"<RequerimientoMaterial {self.material_id} -> {self.proyecto_id}>"


class HistorialRequerimiento(Base, BaseModel):
    """Historial de cambios en requerimientos de material."""
    __tablename__ = "historial_requerimiento"

    requerimiento_id = Column(UUID(as_uuid=True), ForeignKey("requerimientos_material.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # Qué cambió
    campo_modificado = Column(String(100), nullable=False)  # estado, cantidad_aprobada, etc.
    valor_anterior = Column(Text, nullable=True)
    valor_nuevo = Column(Text, nullable=True)
    motivo = Column(Text, nullable=True)

    # Relaciones
    requerimiento = relationship("RequerimientoMaterial", back_populates="historial")
    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<HistorialRequerimiento {self.requerimiento_id} - {self.campo_modificado}>"


class EmpresaProveedora(Base, BaseModel):
    """
    Empresas que proveen o entregan materiales (EDEMSA, proveedores, etc).
    """
    __tablename__ = "empresas_proveedoras"

    nombre = Column(String(200), nullable=False)
    tipo = Column(String(50), nullable=False)  # cliente, proveedor
    cuit = Column(String(20), nullable=True)
    telefono = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    direccion = Column(Text, nullable=True)
    contacto_nombre = Column(String(200), nullable=True)
    notas = Column(Text, nullable=True)

    def __repr__(self):
        return f"<EmpresaProveedora {self.nombre}>"
