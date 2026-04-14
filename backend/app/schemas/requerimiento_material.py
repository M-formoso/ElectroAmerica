from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from app.models.requerimiento_material import (
    EstadoRequerimiento, OrigenMaterial, PrioridadRequerimiento
)


# ============ Empresa Proveedora Schemas ============

class EmpresaProveedoraBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    tipo: str = Field(..., max_length=50)  # cliente, proveedor
    cuit: Optional[str] = Field(None, max_length=20)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    direccion: Optional[str] = None
    contacto_nombre: Optional[str] = Field(None, max_length=200)
    notas: Optional[str] = None


class EmpresaProveedoraCreate(EmpresaProveedoraBase):
    pass


class EmpresaProveedoraUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    tipo: Optional[str] = Field(None, max_length=50)
    cuit: Optional[str] = Field(None, max_length=20)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    direccion: Optional[str] = None
    contacto_nombre: Optional[str] = Field(None, max_length=200)
    notas: Optional[str] = None


class EmpresaProveedoraResponse(EmpresaProveedoraBase):
    id: UUID
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Requerimiento Material Schemas ============

class RequerimientoMaterialBase(BaseModel):
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    material_id: UUID
    cantidad_estimada: float = Field(..., gt=0)
    prioridad: PrioridadRequerimiento = PrioridadRequerimiento.media
    fecha_necesidad: Optional[date] = None
    notas: Optional[str] = None


class RequerimientoMaterialCreate(RequerimientoMaterialBase):
    """Para crear requerimiento manual."""
    origen: Optional[OrigenMaterial] = None
    empresa_origen_id: Optional[UUID] = None


class RequerimientoMaterialFromActividad(BaseModel):
    """Para crear requerimientos desde una actividad tipo."""
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    actividad_tipo_id: UUID
    cantidad_trabajo: float = Field(..., gt=0)
    fecha_necesidad: Optional[date] = None
    prioridad: PrioridadRequerimiento = PrioridadRequerimiento.media


class RequerimientoMaterialUpdate(BaseModel):
    """Actualización de requerimiento."""
    cantidad_estimada: Optional[float] = Field(None, gt=0)
    cantidad_aprobada: Optional[float] = Field(None, ge=0)
    prioridad: Optional[PrioridadRequerimiento] = None
    origen: Optional[OrigenMaterial] = None
    empresa_origen_id: Optional[UUID] = None
    fecha_necesidad: Optional[date] = None
    notas: Optional[str] = None


class RequerimientoAprobacion(BaseModel):
    """Para aprobar un requerimiento."""
    cantidad_aprobada: float = Field(..., ge=0)
    notas_aprobacion: Optional[str] = None


class RequerimientoCambioEstado(BaseModel):
    """Para cambiar el estado de un requerimiento."""
    estado: EstadoRequerimiento
    motivo: Optional[str] = None
    origen: Optional[OrigenMaterial] = None
    empresa_origen_id: Optional[UUID] = None


class RequerimientoEntrega(BaseModel):
    """Para registrar entrega de material."""
    cantidad_entregada: float = Field(..., gt=0)
    notas: Optional[str] = None


class RequerimientoConsumo(BaseModel):
    """Para registrar consumo de material."""
    cantidad_consumida: float = Field(..., gt=0)
    notas: Optional[str] = None


class RequerimientoMaterialResponse(BaseModel):
    """Respuesta completa de requerimiento."""
    id: UUID
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    material_id: UUID

    cantidad_estimada: float
    cantidad_aprobada: Optional[float] = None
    cantidad_entregada: float
    cantidad_consumida: float
    cantidad_pendiente: float
    cantidad_disponible: float

    estado: EstadoRequerimiento
    prioridad: PrioridadRequerimiento
    origen: Optional[OrigenMaterial] = None
    empresa_origen_id: Optional[UUID] = None

    actividad_tipo_id: Optional[UUID] = None
    cantidad_trabajo: Optional[float] = None

    fecha_necesidad: Optional[date] = None
    fecha_solicitud: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None

    notas: Optional[str] = None
    notas_aprobacion: Optional[str] = None

    creado_por_id: Optional[UUID] = None
    aprobado_por_id: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None

    activo: bool
    created_at: datetime
    updated_at: datetime

    # Datos relacionados (se agregan en el endpoint)
    material_nombre: Optional[str] = None
    material_unidad: Optional[str] = None
    material_stock: Optional[float] = None
    proyecto_nombre: Optional[str] = None
    etapa_nombre: Optional[str] = None
    actividad_tipo_nombre: Optional[str] = None
    empresa_origen_nombre: Optional[str] = None

    class Config:
        from_attributes = True


class RequerimientoMaterialResumen(BaseModel):
    """Resumen simplificado para listas."""
    id: UUID
    material_nombre: str
    material_unidad: str
    cantidad_estimada: float
    cantidad_aprobada: Optional[float] = None
    cantidad_pendiente: float
    estado: EstadoRequerimiento
    prioridad: PrioridadRequerimiento
    fecha_necesidad: Optional[date] = None
    origen: Optional[OrigenMaterial] = None


class HistorialRequerimientoResponse(BaseModel):
    """Respuesta de historial."""
    id: UUID
    campo_modificado: str
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    motivo: Optional[str] = None
    usuario_nombre: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Cálculo y Consolidación ============

class CalculoMaterialesRequest(BaseModel):
    """Request para calcular materiales de múltiples actividades."""
    proyecto_id: UUID
    etapa_id: Optional[UUID] = None
    actividades: List[dict]  # [{actividad_tipo_id, cantidad_trabajo}]
    fecha_necesidad: Optional[date] = None
    prioridad: PrioridadRequerimiento = PrioridadRequerimiento.media
    crear_requerimientos: bool = False  # Si true, crea los requerimientos


class MaterialCalculado(BaseModel):
    """Material calculado con cantidad consolidada."""
    material_id: UUID
    material_nombre: str
    material_unidad: str
    cantidad_total: float
    stock_disponible: float
    falta_stock: bool
    actividades_origen: List[dict]  # [{actividad_tipo_id, cantidad}]


class CalculoMaterialesResponse(BaseModel):
    """Respuesta del cálculo de materiales."""
    materiales: List[MaterialCalculado]
    total_items: int
    items_sin_stock: int
    requerimientos_creados: Optional[List[UUID]] = None


class ResumenMaterialesProyecto(BaseModel):
    """Resumen de materiales por estado para un proyecto."""
    proyecto_id: UUID
    proyecto_nombre: str
    total_requerimientos: int
    por_estado: dict  # {estado: count}
    por_prioridad: dict  # {prioridad: count}
    materiales_pendientes: int
    materiales_en_obra: int
    valor_estimado_total: Optional[float] = None
