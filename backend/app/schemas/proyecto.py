from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from app.models.proyecto import EstadoProyecto


class ProyectoBase(BaseModel):
    """Schema base de proyecto."""
    nombre: str = Field(..., min_length=2, max_length=255)
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = Field(None, max_length=255)
    fecha_inicio: Optional[date] = None
    fecha_fin_estimada: Optional[date] = None
    estado: EstadoProyecto = EstadoProyecto.planificacion


class ProyectoCreate(ProyectoBase):
    """Schema para crear proyecto."""
    cliente_id: Optional[UUID] = None
    monto_contratado: Optional[Decimal] = Field(None, ge=0)
    # Actividades tipo a asignar al proyecto
    actividades_tipo_ids: Optional[List[UUID]] = None
    # Herramientas a asignar al proyecto
    herramientas_ids: Optional[List[UUID]] = None


class ProyectoUpdate(BaseModel):
    """Schema para actualizar proyecto."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=255)
    descripcion: Optional[str] = None
    cliente_id: Optional[UUID] = None
    ubicacion: Optional[str] = Field(None, max_length=255)
    fecha_inicio: Optional[date] = None
    fecha_fin_estimada: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    estado: Optional[EstadoProyecto] = None
    monto_contratado: Optional[Decimal] = Field(None, ge=0)


class ProyectoResponse(ProyectoBase):
    """Schema de respuesta de proyecto."""
    id: UUID
    cliente_id: Optional[UUID] = None
    cliente_nombre: Optional[str] = None
    fecha_fin_real: Optional[date] = None
    porcentaje_avance: Decimal
    activo: bool
    created_at: datetime
    supervisor_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class ProyectoDetailResponse(ProyectoResponse):
    """Schema de respuesta detallada de proyecto."""
    monto_contratado: Optional[Decimal] = None  # Solo para admin/supervisor
    cliente_nombre: Optional[str] = None
    total_etapas: int = 0
    etapas_completadas: int = 0

    class Config:
        from_attributes = True


class ProyectoClienteResponse(BaseModel):
    """Schema de respuesta de proyecto para cliente (sin datos financieros)."""
    id: UUID
    nombre: str
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin_estimada: Optional[date] = None
    estado: EstadoProyecto
    porcentaje_avance: Decimal

    class Config:
        from_attributes = True
