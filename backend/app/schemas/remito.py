from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


TipoRemitoLiteral = Literal["egreso", "ingreso"]


class RemitoItemCreate(BaseModel):
    material_id: UUID
    cantidad: Decimal = Field(..., gt=0)


class RemitoItemResponse(BaseModel):
    id: UUID
    material_id: Optional[UUID] = None
    material_codigo: Optional[str] = None
    material_nombre: str
    material_unidad: str
    cantidad: Decimal

    class Config:
        from_attributes = True


class RemitoCreate(BaseModel):
    fecha: date
    deposito_id: UUID
    proyecto_id: Optional[UUID] = None
    destinatario_texto: Optional[str] = Field(None, max_length=255)
    responsable_retira: Optional[str] = Field(None, max_length=255)
    direccion_entrega: Optional[str] = Field(None, max_length=255)
    transportista: Optional[str] = Field(None, max_length=255)
    observaciones: Optional[str] = None
    items: List[RemitoItemCreate] = Field(..., min_length=1)
    # Si True, el descuento de stock puede continuar en cualquier
    # deposito activo con stock real (no solo el grupo del origen).
    # Util cuando se eligio el modo 'Catalogo completo' en el modal.
    descontar_de_cualquier_deposito: bool = False


class RemitoIngresoCreate(BaseModel):
    """Schema para crear un remito de INGRESO de materiales.

    Si `deposito_id` esta seteado, la cantidad suma al stock de ese
    deposito. Si es None, suma al stock global del material (Material.
    stock_actual). Esto ultimo es lo que ocurre cuando el ingreso se
    registra desde el modulo Materiales sin elegir deposito.
    """
    fecha: date
    deposito_id: Optional[UUID] = None
    proyecto_id: Optional[UUID] = None
    destinatario_texto: Optional[str] = Field(None, max_length=255, description="Proveedor / origen del material")
    responsable_retira: Optional[str] = Field(None, max_length=255, description="Responsable que recibe")
    direccion_entrega: Optional[str] = Field(None, max_length=255)
    transportista: Optional[str] = Field(None, max_length=255)
    observaciones: Optional[str] = None
    items: List[RemitoItemCreate] = Field(..., min_length=1)


class RemitoUpdate(BaseModel):
    """Edicion de datos generales del remito (no toca items ni stock)."""
    fecha: Optional[date] = None
    proyecto_id: Optional[UUID] = None
    destinatario_texto: Optional[str] = Field(None, max_length=255)
    responsable_retira: Optional[str] = Field(None, max_length=255)
    direccion_entrega: Optional[str] = Field(None, max_length=255)
    transportista: Optional[str] = Field(None, max_length=255)
    observaciones: Optional[str] = None


class RemitoItemsUpdate(BaseModel):
    """Reemplazo completo de los items del remito (revierte y reaplica stock)."""
    items: List[RemitoItemCreate] = Field(..., min_length=1)
    descontar_de_cualquier_deposito: bool = False


class RemitoAnular(BaseModel):
    motivo: str = Field(..., min_length=3, max_length=1000)


class RemitoResponse(BaseModel):
    id: UUID
    tipo: TipoRemitoLiteral = "egreso"
    numero: int
    numero_formateado: str
    fecha: date
    deposito_id: Optional[UUID] = None
    deposito_nombre: Optional[str] = None
    deposito_padre_nombre: Optional[str] = None
    es_subdeposito: bool = False
    deposito_eliminado: bool = False
    proyecto_id: Optional[UUID] = None
    proyecto_nombre: Optional[str] = None
    destinatario_texto: Optional[str] = None
    responsable_retira: Optional[str] = None
    direccion_entrega: Optional[str] = None
    transportista: Optional[str] = None
    observaciones: Optional[str] = None
    usuario_id: Optional[UUID] = None
    usuario_nombre: Optional[str] = None
    items: List[RemitoItemResponse] = []
    created_at: datetime
    anulado: bool = False
    anulado_at: Optional[datetime] = None
    anulado_por_nombre: Optional[str] = None
    motivo_anulacion: Optional[str] = None
    editado: bool = False
    editado_at: Optional[datetime] = None
    editado_por_nombre: Optional[str] = None

    class Config:
        from_attributes = True


class RemitoListResponse(BaseModel):
    """Schema reducido para el listado."""
    id: UUID
    tipo: TipoRemitoLiteral = "egreso"
    numero: int
    numero_formateado: str
    fecha: date
    deposito_id: Optional[UUID] = None
    deposito_nombre: Optional[str] = None
    deposito_padre_nombre: Optional[str] = None
    es_subdeposito: bool = False
    deposito_eliminado: bool = False
    proyecto_id: Optional[UUID] = None
    proyecto_nombre: Optional[str] = None
    destinatario_texto: Optional[str] = None
    usuario_nombre: Optional[str] = None
    cantidad_items: int = 0
    created_at: datetime
    anulado: bool = False
    editado: bool = False

    class Config:
        from_attributes = True
