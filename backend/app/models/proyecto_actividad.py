"""
Modelos para vincular proyectos con actividades tipo y registrar avances.
"""
from sqlalchemy import Column, String, Text, Date, Numeric, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
from decimal import Decimal


class ProyectoActividad(Base, BaseModel):
    """
    Vincula un proyecto con una actividad tipo y su cantidad planificada.

    Ejemplo:
    - Proyecto: "Obra Centro"
    - Actividad: "Contrabases"
    - Cantidad planificada: 10 unidades
    - Cantidad ejecutada: 5 unidades (50% avance)
    """
    __tablename__ = "proyecto_actividades"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    actividad_tipo_id = Column(UUID(as_uuid=True), ForeignKey("actividades_tipo.id"), nullable=False)

    # Cantidades
    cantidad_planificada = Column(Numeric(10, 2), nullable=False, default=1)
    cantidad_ejecutada = Column(Numeric(10, 2), nullable=False, default=0)

    # Orden de la actividad en el proyecto
    orden = Column(Integer, nullable=False, default=0)

    # Observaciones
    observaciones = Column(Text, nullable=True)

    # Materiales calculados (cache del cálculo automático)
    # Estructura: [{"material_id": "uuid", "material_nombre": "Cemento", "cantidad_total": 71.4, "unidad": "kg"}]
    materiales_calculados = Column(JSONB, nullable=True)

    # Relaciones
    proyecto = relationship("Proyecto", backref="actividades")
    actividad_tipo = relationship("ActividadTipo")
    avances = relationship(
        "AvanceActividad",
        back_populates="proyecto_actividad",
        cascade="all, delete-orphan",
        order_by="desc(AvanceActividad.fecha)"
    )

    @property
    def porcentaje_avance(self) -> Decimal:
        """Calcula el porcentaje de avance de esta actividad."""
        if self.cantidad_planificada and self.cantidad_planificada > 0:
            return (self.cantidad_ejecutada / self.cantidad_planificada) * 100
        return Decimal("0")

    @property
    def cantidad_pendiente(self) -> Decimal:
        """Calcula la cantidad pendiente de ejecutar."""
        return self.cantidad_planificada - self.cantidad_ejecutada

    def __repr__(self):
        return f"<ProyectoActividad {self.actividad_tipo_id} - {self.cantidad_ejecutada}/{self.cantidad_planificada}>"


class AvanceActividad(Base, BaseModel):
    """
    Registro diario de avance de una actividad en un proyecto.

    Ejemplo:
    - Fecha: 2024-04-24
    - Cantidad ejecutada: 3 contrabases
    - Materiales consumidos: [{cemento: 21.42kg}, {arena: 82.5kg}]
    """
    __tablename__ = "avances_actividad"

    proyecto_actividad_id = Column(UUID(as_uuid=True), ForeignKey("proyecto_actividades.id"), nullable=False)

    # Fecha del avance
    fecha = Column(Date, nullable=False)

    # Cantidad ejecutada en este registro
    cantidad = Column(Numeric(10, 2), nullable=False)

    # Materiales consumidos en este avance
    # Estructura: [{"material_id": "uuid", "material_nombre": "Cemento", "cantidad": 21.42, "unidad": "kg"}]
    materiales_consumidos = Column(JSONB, nullable=True)

    # Observaciones del avance
    observaciones = Column(Text, nullable=True)

    # Usuario que registró el avance
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    proyecto_actividad = relationship("ProyectoActividad", back_populates="avances")
    registrado_por = relationship("Usuario")

    def __repr__(self):
        return f"<AvanceActividad {self.fecha} - {self.cantidad}>"


class ProyectoHerramienta(Base, BaseModel):
    """
    Vincula un proyecto con las herramientas asignadas.
    """
    __tablename__ = "proyecto_herramientas"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    herramienta_id = Column(UUID(as_uuid=True), ForeignKey("herramientas.id"), nullable=False)

    # Fecha de asignación
    fecha_asignacion = Column(Date, nullable=True)

    # Observaciones
    observaciones = Column(Text, nullable=True)

    # Relaciones
    proyecto = relationship("Proyecto", backref="herramientas_asignadas")
    herramienta = relationship("Herramienta")

    def __repr__(self):
        return f"<ProyectoHerramienta {self.proyecto_id} - {self.herramienta_id}>"
