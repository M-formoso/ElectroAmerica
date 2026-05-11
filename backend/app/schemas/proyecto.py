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
    # Si esta seteado, los materiales del proyecto operan sobre el stock
    # del deposito indicado. Si es None, sobre el stock global.
    deposito_id: Optional[UUID] = None
    # Actividades tipo a asignar al proyecto
    actividades_tipo_ids: Optional[List[UUID]] = None
    # Herramientas a asignar al proyecto
    herramientas_ids: Optional[List[UUID]] = None


class ProyectoUpdate(BaseModel):
    """Schema para actualizar proyecto."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=255)
    descripcion: Optional[str] = None
    cliente_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    deposito_id: Optional[UUID] = None
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
    deposito_id: Optional[UUID] = None
    deposito_nombre: Optional[str] = None

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


class VerificarStockActividadItem(BaseModel):
    """Una actividad a verificar contra el stock del deposito."""
    actividad_tipo_id: UUID
    cantidad_planificada: Decimal = Field(..., gt=0)


class VerificarStockRequest(BaseModel):
    """Request para verificar si un deposito tiene stock para una lista de actividades."""
    deposito_id: UUID
    actividades: List[VerificarStockActividadItem]


class MaterialFaltante(BaseModel):
    """Detalle de un material que no tiene stock suficiente."""
    material_id: UUID
    material_nombre: str
    material_codigo: Optional[str] = None
    unidad: Optional[str] = None
    necesario: Decimal
    disponible: Decimal
    faltante: Decimal


class VerificarStockResponse(BaseModel):
    """Resultado de verificar stock de un deposito para un set de actividades."""
    ok: bool
    faltantes: List[MaterialFaltante] = []


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
