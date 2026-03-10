from sqlalchemy import Column, String, Text, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel


class Foto(Base, BaseModel):
    """Modelo de foto de proyecto/etapa."""
    __tablename__ = "fotos"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=True)
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    descripcion = Column(Text, nullable=True)
    fecha = Column(Date, nullable=False)
    visible_cliente = Column(Boolean, default=False, nullable=False)
    subido_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="fotos")
    etapa = relationship("Etapa", back_populates="fotos")
    subido_por = relationship("Usuario", foreign_keys=[subido_por_id])

    def __repr__(self):
        return f"<Foto {self.id}>"
