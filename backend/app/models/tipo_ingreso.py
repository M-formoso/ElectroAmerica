from sqlalchemy import Column, String, Integer, Boolean
from app.db.base_class import Base, BaseModel


class TipoIngresoConfig(Base, BaseModel):
    """
    Planilla de ingreso configurable. Reemplaza al enum fijo y permite
    que el usuario cree/renombre/desactive planillas desde la UI.
    """
    __tablename__ = "tipos_ingreso"

    nombre = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), nullable=False, default="#10B981")
    orden = Column(Integer, nullable=False, default=0)
    # Los aportes de socios se muestran en su propia planilla especial:
    # esta bandera identifica cual de los tipos representa esa planilla,
    # para poder fusionarla con la tabla aportes_socio en el resumen.
    es_aporte_socio = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<TipoIngresoConfig {self.nombre}>"
