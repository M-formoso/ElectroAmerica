from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class ReporteCreate(BaseModel):
    """Schema para crear reporte."""
    proyecto_id: UUID
    fecha_desde: date
    fecha_hasta: date
    notas: Optional[str] = None


class ReporteResponse(BaseModel):
    """Schema de respuesta de reporte."""
    id: UUID
    proyecto_id: UUID
    fecha_desde: date
    fecha_hasta: date
    tipo: str
    pdf_url: Optional[str] = None
    excel_url: Optional[str] = None
    compartido_cliente: bool
    notas: Optional[str] = None
    created_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class CompartirReporteRequest(BaseModel):
    """Schema para compartir reporte con cliente."""
    reporte_id: UUID
