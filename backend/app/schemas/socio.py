from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from uuid import UUID


# ============ SOCIO ============

class SocioBase(BaseModel):
    nombre: str = Field(..., max_length=150)
    apellido: Optional[str] = Field(None, max_length=150)
    porcentaje_participacion: float = Field(50, ge=0, le=100)
    email: Optional[str] = None
    telefono: Optional[str] = None
    notas: Optional[str] = None
    usuario_id: Optional[UUID] = None


class SocioCreate(SocioBase):
    pass


class SocioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    porcentaje_participacion: Optional[float] = Field(None, ge=0, le=100)
    email: Optional[str] = None
    telefono: Optional[str] = None
    notas: Optional[str] = None
    usuario_id: Optional[UUID] = None


class SocioResponse(SocioBase):
    id: UUID
    activo: bool

    class Config:
        from_attributes = True


# ============ APORTE SOCIO ============

class AporteSocioBase(BaseModel):
    socio_id: UUID
    monto: float = Field(..., gt=0)
    fecha: date
    concepto: Optional[str] = Field(None, max_length=300)
    observaciones: Optional[str] = None
    cuenta_id: Optional[UUID] = None


class AporteSocioCreate(AporteSocioBase):
    pass


class AporteSocioUpdate(BaseModel):
    monto: Optional[float] = Field(None, gt=0)
    fecha: Optional[date] = None
    concepto: Optional[str] = None
    observaciones: Optional[str] = None
    cuenta_id: Optional[UUID] = None


class AporteSocioResponse(AporteSocioBase):
    id: UUID
    creado_por_id: UUID
    socio_nombre: Optional[str] = None
    cuenta_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# ============ RETIRO SOCIO ============

class RetiroSocioBase(BaseModel):
    socio_id: UUID
    monto: float = Field(..., gt=0)
    fecha: date
    concepto: Optional[str] = Field(None, max_length=300)
    observaciones: Optional[str] = None
    cuenta_id: Optional[UUID] = None


class RetiroSocioCreate(RetiroSocioBase):
    pass


class RetiroSocioUpdate(BaseModel):
    monto: Optional[float] = Field(None, gt=0)
    fecha: Optional[date] = None
    concepto: Optional[str] = None
    observaciones: Optional[str] = None
    cuenta_id: Optional[UUID] = None


class RetiroSocioResponse(RetiroSocioBase):
    id: UUID
    creado_por_id: UUID
    socio_nombre: Optional[str] = None
    cuenta_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# ============ RESUMEN PANEL SOCIOS ============

class ItemPlanilla(BaseModel):
    """Fila de una planilla de ingreso o gasto."""
    id: UUID
    concepto: str
    monto: float
    fecha: date
    referencia: Optional[str] = None  # ej: nombre del socio, categoria


class PlanillaIngresos(BaseModel):
    """Agrupacion de ingresos por tipo (obra, venta, aportes, otros)."""
    tipo: str
    label: str
    total: float
    cantidad: int
    items: List[ItemPlanilla] = []


class PlanillaGastos(BaseModel):
    """Agrupacion de gastos por categoria."""
    categoria_id: Optional[UUID] = None
    categoria: str
    total: float
    cantidad: int
    items: List[ItemPlanilla] = []


class SaldoSocio(BaseModel):
    """Detalle de la ganancia y retiros de un socio."""
    socio_id: UUID
    nombre: str
    porcentaje_participacion: float
    ganancia_asignada: float
    total_retiros: float
    saldo_disponible: float
    retiros: List[ItemPlanilla] = []


class ResumenPanelSocios(BaseModel):
    """Resumen completo del panel de socios para un periodo."""
    fecha_desde: date
    fecha_hasta: date

    # Ingresos
    total_ingresos: float
    planillas_ingresos: List[PlanillaIngresos]

    # Gastos
    total_gastos: float
    planillas_gastos: List[PlanillaGastos]

    # Ganancia y socios
    ganancia: float
    socios: List[SaldoSocio]
