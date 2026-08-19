from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import date
from uuid import UUID


# ============ FACTURA ============

class FacturaBase(BaseModel):
    cliente_id: UUID
    # La factura puede vincularse a un proyecto formal o traer solo el
    # nombre libre (obra_texto). Al menos uno debe estar presente.
    proyecto_id: Optional[UUID] = None
    obra_texto: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    fecha_inscripcion: date
    # Fecha de pago prevista/registrada al momento de cargar la factura.
    # Si se completa, no cambia el estado (sigue pendiente) hasta que se
    # marque como pagada; sirve como referencia para el listado.
    fecha_pago: Optional[date] = None
    monto: float = Field(..., gt=0)
    observaciones: Optional[str] = None

    @model_validator(mode="after")
    def _validar_obra(self):
        if not self.proyecto_id and not (self.obra_texto and self.obra_texto.strip()):
            raise ValueError(
                "Debe indicar un proyecto (proyecto_id) o el nombre de la obra (obra_texto)."
            )
        if self.obra_texto:
            self.obra_texto = self.obra_texto.strip() or None
        return self


class FacturaCreate(FacturaBase):
    pass


class FacturaUpdate(BaseModel):
    cliente_id: Optional[UUID] = None
    proyecto_id: Optional[UUID] = None
    obra_texto: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    fecha_inscripcion: Optional[date] = None
    fecha_pago: Optional[date] = None
    monto: Optional[float] = Field(None, gt=0)
    observaciones: Optional[str] = None


class MarcarPagadaRequest(BaseModel):
    fecha_pago: date
    observaciones: Optional[str] = None


class FacturaResponse(BaseModel):
    """Response que no reejecuta el validador de FacturaBase (permite responder
    facturas ya persistidas sin obligar a reafirmar obra_texto/proyecto_id)."""
    id: UUID
    cliente_id: UUID
    proyecto_id: Optional[UUID] = None
    obra_texto: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inscripcion: date
    monto: float
    observaciones: Optional[str] = None
    estado: str
    fecha_pago: Optional[date] = None
    transaccion_id: Optional[UUID] = None
    creado_por_id: UUID

    # Campos denormalizados para la UI
    cliente_nombre: Optional[str] = None
    proyecto_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# ============ EMPRESAS (vista simplificada de clientes) ============

class EmpresaFacturasResumen(BaseModel):
    """Cliente con totales de facturas asociadas."""
    id: UUID
    nombre: str
    cuit: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    cantidad_facturas: int = 0
    cantidad_pendientes: int = 0
    total_pendiente: float = 0.0
    total_pagado: float = 0.0


class EmpresaQuickCreate(BaseModel):
    """Alta rapida de empresa desde el modulo de facturas."""
    razon_social: str = Field(..., max_length=200)
    nombre_fantasia: Optional[str] = Field(None, max_length=200)
    cuit: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = None
    telefono: Optional[str] = None


# ============ AGRUPADO POR MES ============

class FacturaMesItem(BaseModel):
    """Bucket de facturas de un mes, agrupadas por fecha_pago (o fecha_inscripcion si pendiente)."""
    anio: int
    mes: int
    label: str  # ej: "Agosto 2026"
    total: float
    cantidad: int
    facturas: List[FacturaResponse]
