from sqlalchemy import Column, String, Text, Numeric, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class ActividadTipo(Base, BaseModel):
    """
    Modelo de actividad tipo/estándar.
    Define actividades que se repiten en las obras con sus materiales predefinidos.
    """
    __tablename__ = "actividades_tipo"

    # Identificación
    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)

    # Categoría de la actividad
    categoria = Column(String(100), nullable=True)
    # Ejemplos: instalacion_electrica, tendido_cables, montaje, conexion, etc.

    # Unidad de medida para la actividad (para calcular materiales)
    unidad_trabajo = Column(String(50), nullable=True)
    # Ejemplos: "unidad", "metro", "punto", "tablero", etc.

    # Tiempo estimado por unidad (en horas)
    tiempo_estimado = Column(Numeric(6, 2), nullable=True)

    # Relación con materiales
    materiales = relationship(
        "MaterialActividadTipo",
        back_populates="actividad_tipo",
        cascade="all, delete-orphan"
    )

    def calcular_materiales(self, cantidad_trabajo: float) -> list:
        """
        Calcula los materiales necesarios para una cantidad de trabajo dada.

        Args:
            cantidad_trabajo: Cantidad de unidades de trabajo a realizar

        Returns:
            Lista de diccionarios con material_id y cantidad calculada
        """
        resultado = []
        for mat in self.materiales:
            if mat.activo:
                cantidad = float(mat.cantidad_por_unidad) * cantidad_trabajo
                resultado.append({
                    "material_id": mat.material_id,
                    "material_nombre": mat.material.nombre if mat.material else None,
                    "cantidad": cantidad,
                    "es_opcional": mat.es_opcional,
                    "notas": mat.notas
                })
        return resultado

    def __repr__(self):
        return f"<ActividadTipo {self.codigo} - {self.nombre}>"


class MaterialActividadTipo(Base, BaseModel):
    """
    Relación entre actividad tipo y material.
    Define qué materiales y en qué cantidad se necesitan para cada actividad.
    """
    __tablename__ = "materiales_actividad_tipo"

    # Actividad tipo
    actividad_tipo_id = Column(UUID(as_uuid=True), ForeignKey("actividades_tipo.id"), nullable=False)

    # Material
    material_id = Column(UUID(as_uuid=True), ForeignKey("materiales.id"), nullable=False)

    # Cantidad por unidad de trabajo
    cantidad_por_unidad = Column(Numeric(12, 4), nullable=False)
    # Ej: Si la actividad es "instalar tablero" y el material es "cable 2.5mm",
    # cantidad_por_unidad = 5 significa 5 metros por cada tablero

    # Si es opcional o requerido
    es_opcional = Column(Boolean, default=False, nullable=False)

    # Notas adicionales
    notas = Column(Text, nullable=True)

    # Relaciones
    actividad_tipo = relationship("ActividadTipo", back_populates="materiales")
    material = relationship("Material", backref="actividades_tipo")

    def __repr__(self):
        return f"<MaterialActividadTipo {self.actividad_tipo_id} - {self.material_id}>"
