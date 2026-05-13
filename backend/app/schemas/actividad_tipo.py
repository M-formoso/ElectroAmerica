from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============== MATERIAL DE ACTIVIDAD TIPO ==============

class MaterialActividadTipoBase(BaseModel):
    material_id: UUID
    cantidad_por_unidad: float = Field(..., gt=0)
    es_opcional: bool = False
    notas: Optional[str] = None


class MaterialActividadTipoCreate(MaterialActividadTipoBase):
    pass


class MaterialActividadTipoUpdate(BaseModel):
    cantidad_por_unidad: Optional[float] = None
    es_opcional: Optional[bool] = None
    notas: Optional[str] = None


class MaterialActividadTipoResponse(MaterialActividadTipoBase):
    id: UUID
    actividad_tipo_id: UUID
    activo: bool

    # Datos del material
    material_codigo: Optional[str] = None
    material_nombre: Optional[str] = None
    material_unidad: Optional[str] = None
    material_stock_actual: Optional[float] = None

    class Config:
        from_attributes = True


# ============== ACTIVIDAD TIPO ==============

class ActividadTipoBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=50)
    nombre: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    unidad_trabajo: Optional[str] = None
    tiempo_estimado: Optional[float] = None


class ActividadTipoCreate(ActividadTipoBase):
    codigo: Optional[str] = Field(None, max_length=50)
    materiales: List[MaterialActividadTipoCreate] = []


class ActividadTipoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    unidad_trabajo: Optional[str] = None
    tiempo_estimado: Optional[float] = None


class ActividadTipoResponse(ActividadTipoBase):
    id: UUID
    activo: bool
    created_at: datetime

    # Materiales asociados
    materiales: List[MaterialActividadTipoResponse] = []

    class Config:
        from_attributes = True


class ActividadTipoListResponse(BaseModel):
    """Schema simplificado para listados."""
    id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    unidad_trabajo: Optional[str] = None
    cantidad_materiales: int = 0
    materiales: List[MaterialActividadTipoResponse] = []
    activo: bool

    class Config:
        from_attributes = True


# ============== CÁLCULO DE MATERIALES ==============

class CalcularMaterialesRequest(BaseModel):
    """Request para calcular materiales de una actividad."""
    actividad_tipo_id: UUID
    cantidad_trabajo: float = Field(..., gt=0)


class MaterialCalculado(BaseModel):
    """Material calculado para una cantidad de trabajo."""
    material_id: UUID
    material_codigo: str
    material_nombre: str
    material_unidad: str
    cantidad_calculada: float
    es_opcional: bool
    stock_actual: Optional[float] = None
    stock_suficiente: bool = True
    notas: Optional[str] = None


class CalcularMaterialesResponse(BaseModel):
    """Response del cálculo de materiales."""
    actividad_tipo_id: UUID
    actividad_nombre: str
    cantidad_trabajo: float
    unidad_trabajo: Optional[str] = None
    tiempo_estimado_total: Optional[float] = None
    materiales: List[MaterialCalculado]
    alertas_stock: List[str] = []  # Materiales sin stock suficiente


# ============== CATEGORÍAS ==============

class CategoriaActividadResponse(BaseModel):
    """Categoría de actividades."""
    nombre: str
    cantidad_actividades: int


class ListarCategoriasResponse(BaseModel):
    """Listado de categorías disponibles."""
    categorias: List[CategoriaActividadResponse]
