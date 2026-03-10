# Agente: Stock de Materiales

## Rol
Implementar el módulo completo de inventario, movimientos de stock y asignación de materiales a proyectos.

## Modelos

### models/material.py
```python
from sqlalchemy import Column, String, Numeric, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel

class Material(Base, BaseModel):
    __tablename__ = "materiales"

    nombre = Column(String(255), nullable=False)
    categoria = Column(String(100))
    unidad = Column(String(30))
    stock_actual = Column(Numeric(10, 3), nullable=False, default=0)
    stock_minimo = Column(Numeric(10, 3), default=0)
    precio_costo = Column(Numeric(10, 2))
    proveedor = Column(String(255))

    # Relaciones
    movimientos = relationship("MovimientoStock", back_populates="material")
    asignaciones = relationship("AsignacionMaterial", back_populates="material")
```

### models/movimiento_stock.py
```python
from sqlalchemy import Column, String, Text, Numeric, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum

class TipoMovimiento(str, enum.Enum):
    ingreso = "ingreso"
    egreso = "egreso"
    ajuste = "ajuste"

class MovimientoStock(Base, BaseModel):
    __tablename__ = "movimientos_stock"

    material_id = Column(UUID(as_uuid=True), ForeignKey("materiales.id"), nullable=False)
    tipo = Column(Enum(TipoMovimiento), nullable=False)
    cantidad = Column(Numeric(10, 3), nullable=False)
    referencia_tipo = Column(String(50))  # 'asignacion', 'compra', 'ajuste_manual'
    referencia_id = Column(UUID(as_uuid=True), nullable=True)
    observaciones = Column(Text)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    # Relaciones
    material = relationship("Material", back_populates="movimientos")
    usuario = relationship("Usuario")
```

### models/asignacion_material.py
```python
from sqlalchemy import Column, Date, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel

class AsignacionMaterial(Base, BaseModel):
    __tablename__ = "asignaciones_material"

    material_id = Column(UUID(as_uuid=True), ForeignKey("materiales.id"), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=True)
    cantidad = Column(Numeric(10, 3), nullable=False)
    precio_unitario = Column(Numeric(10, 2))
    fecha = Column(Date, nullable=False)
    observaciones = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    # Relaciones
    material = relationship("Material", back_populates="asignaciones")
    proyecto = relationship("Proyecto")
    etapa = relationship("Etapa")
    creador = relationship("Usuario")
```

## Services

### services/material_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from fastapi import HTTPException
from app.models.material import Material
from app.models.movimiento_stock import MovimientoStock, TipoMovimiento
from app.models.asignacion_material import AsignacionMaterial
from app.schemas.material import MaterialCreate, MaterialUpdate, AsignacionCreate, IngresoCreate

def obtener_materiales(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    categoria: Optional[str] = None,
    solo_stock_bajo: bool = False
) -> List[Material]:
    query = db.query(Material).filter(Material.activo == True)

    if categoria:
        query = query.filter(Material.categoria == categoria)
    if solo_stock_bajo:
        query = query.filter(Material.stock_actual <= Material.stock_minimo)

    return query.offset(skip).limit(limit).all()

def obtener_material(db: Session, material_id: UUID) -> Optional[Material]:
    return db.query(Material).filter(
        Material.id == material_id,
        Material.activo == True
    ).first()

def crear_material(db: Session, material: MaterialCreate) -> Material:
    db_material = Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

def asignar_material_a_proyecto(
    db: Session,
    asignacion: AsignacionCreate,
    usuario_id: UUID
) -> AsignacionMaterial:
    """
    Asigna material a un proyecto, descuenta del stock y registra el movimiento.
    """
    material = obtener_material(db, asignacion.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    if material.stock_actual < asignacion.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponible: {material.stock_actual}"
        )

    # Crear asignación
    db_asignacion = AsignacionMaterial(
        material_id=asignacion.material_id,
        proyecto_id=asignacion.proyecto_id,
        etapa_id=asignacion.etapa_id,
        cantidad=asignacion.cantidad,
        precio_unitario=material.precio_costo,
        fecha=date.today(),
        observaciones=asignacion.observaciones,
        created_by=usuario_id
    )
    db.add(db_asignacion)

    # Descontar stock
    material.stock_actual -= asignacion.cantidad

    # Registrar movimiento
    movimiento = MovimientoStock(
        material_id=asignacion.material_id,
        tipo=TipoMovimiento.egreso,
        cantidad=asignacion.cantidad,
        referencia_tipo="asignacion",
        referencia_id=db_asignacion.id,
        observaciones=f"Asignado a proyecto",
        usuario_id=usuario_id
    )
    db.add(movimiento)

    db.commit()
    db.refresh(db_asignacion)

    # Verificar alerta de stock bajo
    if material.stock_actual <= material.stock_minimo:
        from app.tasks.alertas import alerta_stock_bajo
        alerta_stock_bajo.delay(str(material.id))

    return db_asignacion

def registrar_ingreso_stock(
    db: Session,
    ingreso: IngresoCreate,
    usuario_id: UUID
) -> MovimientoStock:
    """
    Registra una compra/ingreso de material al stock.
    """
    material = obtener_material(db, ingreso.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    # Actualizar stock
    material.stock_actual += ingreso.cantidad

    # Si viene precio, actualizar precio costo
    if ingreso.precio_unitario:
        material.precio_costo = ingreso.precio_unitario

    if ingreso.proveedor:
        material.proveedor = ingreso.proveedor

    # Registrar movimiento
    movimiento = MovimientoStock(
        material_id=ingreso.material_id,
        tipo=TipoMovimiento.ingreso,
        cantidad=ingreso.cantidad,
        referencia_tipo="compra",
        observaciones=ingreso.observaciones,
        usuario_id=usuario_id
    )
    db.add(movimiento)

    db.commit()
    db.refresh(movimiento)
    return movimiento

def obtener_valor_total_inventario(db: Session) -> Decimal:
    """Calcula el valor total del inventario (stock × precio costo)."""
    resultado = db.query(
        func.sum(Material.stock_actual * Material.precio_costo)
    ).filter(Material.activo == True).scalar()

    return Decimal(resultado or 0)

def obtener_movimientos_material(
    db: Session,
    material_id: UUID,
    limit: int = 50
) -> List[MovimientoStock]:
    return db.query(MovimientoStock).filter(
        MovimientoStock.material_id == material_id
    ).order_by(MovimientoStock.created_at.desc()).limit(limit).all()
```

## Endpoints

### api/v1/endpoints/materiales.py
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.schemas.material import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    AsignacionCreate, AsignacionResponse,
    IngresoCreate, MovimientoResponse,
    ValorInventarioResponse
)
from app.services import material_service

router = APIRouter()

@router.get("/", response_model=List[MaterialResponse])
def listar_materiales(
    categoria: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return material_service.obtener_materiales(db, skip, limit, categoria)

@router.get("/stock-bajo", response_model=List[MaterialResponse])
def listar_materiales_stock_bajo(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return material_service.obtener_materiales(db, solo_stock_bajo=True)

@router.get("/valor-total", response_model=ValorInventarioResponse)
def obtener_valor_inventario(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    valor = material_service.obtener_valor_total_inventario(db)
    return {"valor_total": valor}

@router.post("/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def crear_material(
    material: MaterialCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    return material_service.crear_material(db, material)

@router.get("/{material_id}", response_model=MaterialResponse)
def obtener_material(
    material_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    material = material_service.obtener_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return material

@router.get("/{material_id}/movimientos", response_model=List[MovimientoResponse])
def listar_movimientos_material(
    material_id: UUID,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return material_service.obtener_movimientos_material(db, material_id, limit)

@router.post("/asignar", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
def asignar_material(
    asignacion: AsignacionCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return material_service.asignar_material_a_proyecto(db, asignacion, usuario.id)

@router.post("/ingreso", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
def registrar_ingreso(
    ingreso: IngresoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    return material_service.registrar_ingreso_stock(db, ingreso, usuario.id)
```

## Celery Task

### tasks/alertas.py
```python
from celery import shared_task
from app.db.session import SessionLocal
from app.models.material import Material

@shared_task
def alerta_stock_bajo(material_id: str):
    """
    Notifica a admin y supervisor cuando un material llega al stock mínimo.
    TODO: Implementar notificación por email o en dashboard.
    """
    db = SessionLocal()
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if material and material.stock_actual <= material.stock_minimo:
            # Aquí implementar notificación
            print(f"ALERTA: Material {material.nombre} con stock bajo: {material.stock_actual}")
    finally:
        db.close()
```

## Frontend Components

### components/materiales/MaterialList.tsx
```typescript
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Material } from '@/types/material';
import { formatearMonto } from '@/utils/formatters';
import { Package, AlertTriangle, Plus } from 'lucide-react';
import api from '@/services/api';

export function MaterialList() {
  const { data: materiales, isLoading } = useQuery<Material[]>({
    queryKey: ['materiales'],
    queryFn: () => api.get('/materiales').then(res => res.data),
  });

  if (isLoading) return <div>Cargando...</div>;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          <h2 className="text-xl font-semibold">Stock de Materiales</h2>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Material
        </Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Material</TableHead>
              <TableHead>Categoría</TableHead>
              <TableHead className="text-right">Stock</TableHead>
              <TableHead className="text-right">Mínimo</TableHead>
              <TableHead className="text-right">Precio</TableHead>
              <TableHead>Estado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {materiales?.map((material) => (
              <TableRow key={material.id}>
                <TableCell className="font-medium">{material.nombre}</TableCell>
                <TableCell>{material.categoria}</TableCell>
                <TableCell className="text-right">
                  {material.stockActual} {material.unidad}
                </TableCell>
                <TableCell className="text-right">
                  {material.stockMinimo} {material.unidad}
                </TableCell>
                <TableCell className="text-right">
                  {material.precioCosto && formatearMonto(material.precioCosto)}
                </TableCell>
                <TableCell>
                  {material.stockActual <= material.stockMinimo ? (
                    <Badge variant="destructive" className="flex items-center gap-1 w-fit">
                      <AlertTriangle className="h-3 w-3" />
                      Stock Bajo
                    </Badge>
                  ) : (
                    <Badge variant="secondary">Normal</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
```

## Checklist de Completado
- [ ] Modelo Material
- [ ] Modelo MovimientoStock
- [ ] Modelo AsignacionMaterial
- [ ] Schemas Pydantic
- [ ] Service con CRUD y lógica de stock
- [ ] Endpoints con permisos
- [ ] Celery task para alertas
- [ ] MaterialList component
- [ ] MaterialForm component
- [ ] AsignacionForm modal
- [ ] IngresoForm modal
- [ ] MovimientosHistorial component
- [ ] Widget stock bajo en dashboard
