# Agente: Costos, Precios y Recaudación

## Rol
Implementar el módulo financiero con control de costos, precios de ítems, recaudación y rentabilidad. **Solo visible para administrador y supervisor.**

## Modelos

### models/precio_item.py
```python
from sqlalchemy import Column, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel

class PrecioItem(Base, BaseModel):
    __tablename__ = "precios_items"

    item_trabajo_id = Column(UUID(as_uuid=True), ForeignKey("items_trabajo.id"), nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    fecha_desde = Column(DateTime(timezone=True), nullable=False)
    fecha_hasta = Column(DateTime(timezone=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    # Relaciones
    item_trabajo = relationship("ItemTrabajo")
    actualizador = relationship("Usuario")
```

## Schemas

### schemas/finanzas.py
```python
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from datetime import datetime

class PrecioItemCreate(BaseModel):
    item_trabajo_id: UUID
    precio_unitario: Decimal

class PrecioItemResponse(BaseModel):
    id: UUID
    item_trabajo_id: UUID
    precio_unitario: Decimal
    fecha_desde: datetime
    fecha_hasta: Optional[datetime]

    class Config:
        from_attributes = True

class ResumenCostosEtapa(BaseModel):
    etapa_id: UUID
    nombre_etapa: str
    costo_items: Decimal
    costo_materiales: Decimal
    costo_total: Decimal

class ResumenFinancieroProyecto(BaseModel):
    proyecto_id: UUID
    nombre_proyecto: str
    monto_contratado: Optional[Decimal]
    costo_items: Decimal
    costo_materiales: Decimal
    costo_gastos: Decimal
    costo_total: Decimal
    rentabilidad: Optional[Decimal]
    porcentaje_rentabilidad: Optional[Decimal]
    etapas: List[ResumenCostosEtapa]

class ResumenFinancieroGeneral(BaseModel):
    total_contratado: Decimal
    total_costos: Decimal
    total_rentabilidad: Decimal
    proyectos_activos: int
    proyectos: List[ResumenFinancieroProyecto]
```

## Services

### services/finanzas_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa
from app.models.item_trabajo import ItemTrabajo
from app.models.asignacion_material import AsignacionMaterial
from app.models.gasto import Gasto
from app.models.precio_item import PrecioItem
from app.schemas.finanzas import (
    ResumenFinancieroProyecto,
    ResumenCostosEtapa,
    ResumenFinancieroGeneral
)

def cargar_precio_item(
    db: Session,
    item_trabajo_id: UUID,
    precio_unitario: Decimal,
    usuario_id: UUID
) -> PrecioItem:
    """
    Carga o actualiza el precio de un ítem de trabajo.
    Mantiene historial de precios.
    """
    # Cerrar precio anterior si existe
    precio_actual = db.query(PrecioItem).filter(
        PrecioItem.item_trabajo_id == item_trabajo_id,
        PrecioItem.fecha_hasta.is_(None)
    ).first()

    if precio_actual:
        precio_actual.fecha_hasta = datetime.utcnow()

    # Crear nuevo precio
    nuevo_precio = PrecioItem(
        item_trabajo_id=item_trabajo_id,
        precio_unitario=precio_unitario,
        fecha_desde=datetime.utcnow(),
        updated_by=usuario_id
    )
    db.add(nuevo_precio)

    # Actualizar precio en el ítem
    item = db.query(ItemTrabajo).filter(ItemTrabajo.id == item_trabajo_id).first()
    if item:
        item.precio_unitario = precio_unitario

    db.commit()
    db.refresh(nuevo_precio)
    return nuevo_precio

def calcular_costo_etapa(db: Session, etapa_id: UUID) -> dict:
    """
    Calcula el costo total de una etapa (ítems + materiales).
    """
    # Costo de ítems (cantidad × precio_unitario)
    costo_items = db.query(
        func.coalesce(func.sum(ItemTrabajo.cantidad * ItemTrabajo.precio_unitario), 0)
    ).filter(
        ItemTrabajo.etapa_id == etapa_id,
        ItemTrabajo.activo == True
    ).scalar()

    # Costo de materiales asignados a la etapa
    costo_materiales = db.query(
        func.coalesce(func.sum(AsignacionMaterial.cantidad * AsignacionMaterial.precio_unitario), 0)
    ).filter(
        AsignacionMaterial.etapa_id == etapa_id
    ).scalar()

    return {
        "costo_items": Decimal(costo_items or 0),
        "costo_materiales": Decimal(costo_materiales or 0),
        "costo_total": Decimal(costo_items or 0) + Decimal(costo_materiales or 0)
    }

def obtener_resumen_financiero_proyecto(
    db: Session,
    proyecto_id: UUID
) -> ResumenFinancieroProyecto:
    """
    Genera el resumen financiero completo de un proyecto.
    """
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        return None

    # Calcular costos por etapa
    etapas_resumen = []
    total_costo_items = Decimal(0)
    total_costo_materiales = Decimal(0)

    for etapa in proyecto.etapas:
        costos_etapa = calcular_costo_etapa(db, etapa.id)
        etapas_resumen.append(ResumenCostosEtapa(
            etapa_id=etapa.id,
            nombre_etapa=etapa.nombre,
            costo_items=costos_etapa["costo_items"],
            costo_materiales=costos_etapa["costo_materiales"],
            costo_total=costos_etapa["costo_total"]
        ))
        total_costo_items += costos_etapa["costo_items"]
        total_costo_materiales += costos_etapa["costo_materiales"]

    # Gastos del proyecto
    total_gastos = db.query(
        func.coalesce(func.sum(Gasto.monto), 0)
    ).filter(
        Gasto.proyecto_id == proyecto_id,
        Gasto.activo == True
    ).scalar()
    total_gastos = Decimal(total_gastos or 0)

    # Calcular totales y rentabilidad
    costo_total = total_costo_items + total_costo_materiales + total_gastos

    rentabilidad = None
    porcentaje_rentabilidad = None
    if proyecto.monto_contratado:
        rentabilidad = proyecto.monto_contratado - costo_total
        if proyecto.monto_contratado > 0:
            porcentaje_rentabilidad = (rentabilidad / proyecto.monto_contratado) * 100

    return ResumenFinancieroProyecto(
        proyecto_id=proyecto.id,
        nombre_proyecto=proyecto.nombre,
        monto_contratado=proyecto.monto_contratado,
        costo_items=total_costo_items,
        costo_materiales=total_costo_materiales,
        costo_gastos=total_gastos,
        costo_total=costo_total,
        rentabilidad=rentabilidad,
        porcentaje_rentabilidad=porcentaje_rentabilidad,
        etapas=etapas_resumen
    )

def obtener_resumen_financiero_general(db: Session) -> ResumenFinancieroGeneral:
    """
    Genera el resumen financiero de todos los proyectos activos.
    """
    proyectos = db.query(Proyecto).filter(
        Proyecto.activo == True,
        Proyecto.estado.in_([EstadoProyecto.en_ejecucion, EstadoProyecto.planificacion])
    ).all()

    resumenes = []
    total_contratado = Decimal(0)
    total_costos = Decimal(0)

    for proyecto in proyectos:
        resumen = obtener_resumen_financiero_proyecto(db, proyecto.id)
        if resumen:
            resumenes.append(resumen)
            if resumen.monto_contratado:
                total_contratado += resumen.monto_contratado
            total_costos += resumen.costo_total

    return ResumenFinancieroGeneral(
        total_contratado=total_contratado,
        total_costos=total_costos,
        total_rentabilidad=total_contratado - total_costos,
        proyectos_activos=len(proyectos),
        proyectos=resumenes
    )

def actualizar_monto_contratado(
    db: Session,
    proyecto_id: UUID,
    monto: Decimal
) -> Proyecto:
    """
    Actualiza el monto contratado de un proyecto.
    """
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if proyecto:
        proyecto.monto_contratado = monto
        db.commit()
        db.refresh(proyecto)
    return proyecto
```

## Endpoints

### api/v1/endpoints/finanzas.py
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from app.core.deps import get_db, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.schemas.finanzas import (
    PrecioItemCreate, PrecioItemResponse,
    ResumenFinancieroProyecto, ResumenFinancieroGeneral
)
from app.services import finanzas_service

router = APIRouter()

@router.get("/proyecto/{proyecto_id}", response_model=ResumenFinancieroProyecto)
def obtener_finanzas_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Solo admin y supervisor pueden ver finanzas."""
    resumen = finanzas_service.obtener_resumen_financiero_proyecto(db, proyecto_id)
    if not resumen:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return resumen

@router.get("/resumen-general", response_model=ResumenFinancieroGeneral)
def obtener_resumen_general(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Resumen financiero de todos los proyectos activos."""
    return finanzas_service.obtener_resumen_financiero_general(db)

@router.post("/precio-item", response_model=PrecioItemResponse)
def cargar_precio_item(
    precio: PrecioItemCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Carga o actualiza el precio de un ítem de trabajo."""
    return finanzas_service.cargar_precio_item(
        db, precio.item_trabajo_id, precio.precio_unitario, usuario.id
    )

@router.put("/proyecto/{proyecto_id}/monto")
def actualizar_monto_proyecto(
    proyecto_id: UUID,
    monto: Decimal,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza el monto contratado del proyecto."""
    proyecto = finanzas_service.actualizar_monto_contratado(db, proyecto_id, monto)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"message": "Monto actualizado", "monto_contratado": monto}

@router.get("/rentabilidad")
def obtener_rentabilidad_proyectos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    """Listado de rentabilidad por proyecto."""
    resumen = finanzas_service.obtener_resumen_financiero_general(db)
    return [
        {
            "proyecto_id": p.proyecto_id,
            "nombre": p.nombre_proyecto,
            "monto_contratado": p.monto_contratado,
            "costo_total": p.costo_total,
            "rentabilidad": p.rentabilidad,
            "porcentaje": p.porcentaje_rentabilidad
        }
        for p in resumen.proyectos
    ]
```

## Frontend Components

### components/finanzas/ResumenFinanciero.tsx
```typescript
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { formatearMonto, formatearPorcentaje } from '@/utils/formatters';
import { TrendingUp, TrendingDown, DollarSign, Briefcase } from 'lucide-react';
import api from '@/services/api';

interface ResumenGeneral {
  totalContratado: number;
  totalCostos: number;
  totalRentabilidad: number;
  proyectosActivos: number;
}

export function ResumenFinanciero() {
  const { data: resumen, isLoading } = useQuery<ResumenGeneral>({
    queryKey: ['finanzas', 'resumen-general'],
    queryFn: () => api.get('/finanzas/resumen-general').then(res => res.data),
  });

  if (isLoading) return <div>Cargando...</div>;
  if (!resumen) return null;

  const rentabilidadPositiva = resumen.totalRentabilidad >= 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted">Total Contratado</p>
              <p className="text-2xl font-bold">{formatearMonto(resumen.totalContratado)}</p>
            </div>
            <DollarSign className="h-8 w-8 text-primary" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted">Total Costos</p>
              <p className="text-2xl font-bold">{formatearMonto(resumen.totalCostos)}</p>
            </div>
            <TrendingDown className="h-8 w-8 text-yellow-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted">Rentabilidad</p>
              <p className={`text-2xl font-bold ${rentabilidadPositiva ? 'text-green-600' : 'text-red-600'}`}>
                {formatearMonto(resumen.totalRentabilidad)}
              </p>
            </div>
            {rentabilidadPositiva ? (
              <TrendingUp className="h-8 w-8 text-green-500" />
            ) : (
              <TrendingDown className="h-8 w-8 text-red-500" />
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted">Proyectos Activos</p>
              <p className="text-2xl font-bold">{resumen.proyectosActivos}</p>
            </div>
            <Briefcase className="h-8 w-8 text-primary" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### components/finanzas/RentabilidadChart.tsx
```typescript
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { formatearMonto } from '@/utils/formatters';

interface ProyectoRentabilidad {
  nombre: string;
  rentabilidad: number;
}

interface Props {
  data: ProyectoRentabilidad[];
}

export function RentabilidadChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" tickFormatter={(v) => formatearMonto(v)} />
        <YAxis type="category" dataKey="nombre" width={150} />
        <Tooltip formatter={(value: number) => formatearMonto(value)} />
        <Bar dataKey="rentabilidad">
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.rentabilidad >= 0 ? '#10B981' : '#EF4444'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
```

## Seguridad

Este módulo es **exclusivo para administrador y supervisor**. Operarios y clientes NO deben tener acceso.

```python
# En TODOS los endpoints usar:
usuario: Usuario = Depends(require_admin_or_supervisor)
```

## Checklist de Completado
- [ ] Modelo PrecioItem con historial
- [ ] Schemas Pydantic financieros
- [ ] Service con cálculos de costos
- [ ] Service con cálculo de rentabilidad
- [ ] Endpoints protegidos por rol
- [ ] ResumenFinanciero component
- [ ] RentabilidadChart component
- [ ] ProyectoFinanzasDetail page
- [ ] Tabla de rentabilidad por proyecto
- [ ] Form para cargar precios de ítems
- [ ] Form para actualizar monto contratado
