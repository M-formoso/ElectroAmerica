# Agente: Gastos Operativos

## Rol
Implementar el módulo de registro de egresos del día a día, asociados a proyectos o a la empresa en general.

## Modelos

### models/gasto.py
```python
from sqlalchemy import Column, String, Text, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel

class Gasto(Base, BaseModel):
    __tablename__ = "gastos"

    fecha = Column(Date, nullable=False)
    categoria = Column(String(100), nullable=False)  # combustible, viaticos, herramientas, servicios, otro
    descripcion = Column(Text, nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True)  # NULL = gasto general
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    comprobante_url = Column(String(500), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="gastos")
    responsable = relationship("Usuario", foreign_keys=[responsable_id])
    creador = relationship("Usuario", foreign_keys=[created_by])


class CategoriaGasto(Base, BaseModel):
    __tablename__ = "categorias_gasto"

    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    color = Column(String(7), default="#E53935")  # Hex color
```

## Schemas

### schemas/gasto.py
```python
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from datetime import date, datetime

class GastoBase(BaseModel):
    fecha: date
    categoria: str
    descripcion: str
    monto: Decimal
    proyecto_id: Optional[UUID] = None
    responsable_id: UUID

class GastoCreate(GastoBase):
    comprobante_url: Optional[str] = None

class GastoUpdate(BaseModel):
    fecha: Optional[date] = None
    categoria: Optional[str] = None
    descripcion: Optional[str] = None
    monto: Optional[Decimal] = None
    proyecto_id: Optional[UUID] = None
    comprobante_url: Optional[str] = None

class GastoResponse(GastoBase):
    id: UUID
    comprobante_url: Optional[str]
    created_at: datetime
    proyecto: Optional[dict] = None  # {"id": UUID, "nombre": str}
    responsable: Optional[dict] = None  # {"id": UUID, "nombre": str}

    class Config:
        from_attributes = True

class ResumenGastosPeriodo(BaseModel):
    fecha_desde: date
    fecha_hasta: date
    total: Decimal
    por_categoria: dict[str, Decimal]
    por_proyecto: dict[str, Decimal]

class CategoriaGastoResponse(BaseModel):
    id: UUID
    nombre: str
    descripcion: Optional[str]
    color: str

    class Config:
        from_attributes = True
```

## Services

### services/gasto_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from app.models.gasto import Gasto, CategoriaGasto
from app.schemas.gasto import GastoCreate, GastoUpdate, ResumenGastosPeriodo

def obtener_gastos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    proyecto_id: Optional[UUID] = None,
    categoria: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Gasto]:
    query = db.query(Gasto).filter(Gasto.activo == True)

    if proyecto_id:
        query = query.filter(Gasto.proyecto_id == proyecto_id)
    if categoria:
        query = query.filter(Gasto.categoria == categoria)
    if fecha_desde:
        query = query.filter(Gasto.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Gasto.fecha <= fecha_hasta)

    return query.order_by(Gasto.fecha.desc()).offset(skip).limit(limit).all()

def obtener_gasto(db: Session, gasto_id: UUID) -> Optional[Gasto]:
    return db.query(Gasto).filter(
        Gasto.id == gasto_id,
        Gasto.activo == True
    ).first()

def crear_gasto(db: Session, gasto: GastoCreate, usuario_id: UUID) -> Gasto:
    db_gasto = Gasto(
        **gasto.model_dump(),
        created_by=usuario_id
    )
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

def actualizar_gasto(db: Session, gasto_id: UUID, gasto: GastoUpdate) -> Optional[Gasto]:
    db_gasto = obtener_gasto(db, gasto_id)
    if not db_gasto:
        return None

    for field, value in gasto.model_dump(exclude_unset=True).items():
        setattr(db_gasto, field, value)

    db.commit()
    db.refresh(db_gasto)
    return db_gasto

def eliminar_gasto(db: Session, gasto_id: UUID) -> bool:
    gasto = obtener_gasto(db, gasto_id)
    if not gasto:
        return False
    gasto.activo = False
    db.commit()
    return True

def obtener_resumen_gastos(
    db: Session,
    fecha_desde: date,
    fecha_hasta: date,
    proyecto_id: Optional[UUID] = None
) -> ResumenGastosPeriodo:
    """
    Genera un resumen de gastos por período.
    """
    base_query = db.query(Gasto).filter(
        Gasto.activo == True,
        Gasto.fecha >= fecha_desde,
        Gasto.fecha <= fecha_hasta
    )

    if proyecto_id:
        base_query = base_query.filter(Gasto.proyecto_id == proyecto_id)

    # Total
    total = db.query(func.coalesce(func.sum(Gasto.monto), 0)).filter(
        Gasto.activo == True,
        Gasto.fecha >= fecha_desde,
        Gasto.fecha <= fecha_hasta
    )
    if proyecto_id:
        total = total.filter(Gasto.proyecto_id == proyecto_id)
    total = Decimal(total.scalar() or 0)

    # Por categoría
    por_categoria_query = db.query(
        Gasto.categoria,
        func.sum(Gasto.monto)
    ).filter(
        Gasto.activo == True,
        Gasto.fecha >= fecha_desde,
        Gasto.fecha <= fecha_hasta
    )
    if proyecto_id:
        por_categoria_query = por_categoria_query.filter(Gasto.proyecto_id == proyecto_id)
    por_categoria = {
        cat: Decimal(monto or 0)
        for cat, monto in por_categoria_query.group_by(Gasto.categoria).all()
    }

    # Por proyecto
    from app.models.proyecto import Proyecto
    por_proyecto_query = db.query(
        Proyecto.nombre,
        func.sum(Gasto.monto)
    ).join(Proyecto, Gasto.proyecto_id == Proyecto.id).filter(
        Gasto.activo == True,
        Gasto.fecha >= fecha_desde,
        Gasto.fecha <= fecha_hasta
    )
    if proyecto_id:
        por_proyecto_query = por_proyecto_query.filter(Gasto.proyecto_id == proyecto_id)
    por_proyecto = {
        nombre: Decimal(monto or 0)
        for nombre, monto in por_proyecto_query.group_by(Proyecto.nombre).all()
    }

    # Gastos generales (sin proyecto)
    gastos_generales = db.query(func.sum(Gasto.monto)).filter(
        Gasto.activo == True,
        Gasto.proyecto_id.is_(None),
        Gasto.fecha >= fecha_desde,
        Gasto.fecha <= fecha_hasta
    ).scalar()
    if gastos_generales:
        por_proyecto["General (sin proyecto)"] = Decimal(gastos_generales)

    return ResumenGastosPeriodo(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        total=total,
        por_categoria=por_categoria,
        por_proyecto=por_proyecto
    )

def obtener_categorias(db: Session) -> List[CategoriaGasto]:
    return db.query(CategoriaGasto).filter(CategoriaGasto.activo == True).all()

def crear_categoria(db: Session, nombre: str, descripcion: str = None, color: str = "#E53935") -> CategoriaGasto:
    categoria = CategoriaGasto(nombre=nombre, descripcion=descripcion, color=color)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria

# Categorías por defecto
CATEGORIAS_DEFAULT = [
    ("Combustible", "Gastos de nafta, gasoil, etc.", "#F97316"),
    ("Viáticos", "Gastos de alimentación y transporte del personal", "#3B82F6"),
    ("Herramientas", "Compra y reparación de herramientas", "#8B5CF6"),
    ("Servicios", "Servicios contratados (fletes, etc.)", "#10B981"),
    ("Materiales menores", "Materiales de bajo costo no inventariados", "#EC4899"),
    ("Otros", "Gastos varios", "#6B7280"),
]

def inicializar_categorias(db: Session):
    """Crea las categorías por defecto si no existen."""
    for nombre, descripcion, color in CATEGORIAS_DEFAULT:
        existe = db.query(CategoriaGasto).filter(CategoriaGasto.nombre == nombre).first()
        if not existe:
            crear_categoria(db, nombre, descripcion, color)
```

## Endpoints

### api/v1/endpoints/gastos.py
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.deps import get_db, get_usuario_actual, require_staff
from app.models.usuario import Usuario
from app.schemas.gasto import (
    GastoCreate, GastoUpdate, GastoResponse,
    ResumenGastosPeriodo, CategoriaGastoResponse
)
from app.services import gasto_service
from app.services.cloudinary_service import subir_imagen

router = APIRouter()

@router.get("/", response_model=List[GastoResponse])
def listar_gastos(
    proyecto_id: Optional[UUID] = None,
    categoria: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return gasto_service.obtener_gastos(
        db, skip, limit, proyecto_id, categoria, fecha_desde, fecha_hasta
    )

@router.get("/resumen", response_model=ResumenGastosPeriodo)
def obtener_resumen_gastos(
    fecha_desde: date,
    fecha_hasta: date,
    proyecto_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return gasto_service.obtener_resumen_gastos(db, fecha_desde, fecha_hasta, proyecto_id)

@router.get("/por-proyecto/{proyecto_id}", response_model=List[GastoResponse])
def listar_gastos_proyecto(
    proyecto_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return gasto_service.obtener_gastos(db, skip, limit, proyecto_id=proyecto_id)

@router.get("/categorias", response_model=List[CategoriaGastoResponse])
def listar_categorias(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return gasto_service.obtener_categorias(db)

@router.post("/categorias", response_model=CategoriaGastoResponse)
def crear_categoria(
    nombre: str,
    descripcion: Optional[str] = None,
    color: str = "#E53935",
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return gasto_service.crear_categoria(db, nombre, descripcion, color)

@router.post("/", response_model=GastoResponse, status_code=status.HTTP_201_CREATED)
def crear_gasto(
    gasto: GastoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return gasto_service.crear_gasto(db, gasto, usuario.id)

@router.post("/{gasto_id}/comprobante")
async def subir_comprobante(
    gasto_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Sube una foto del comprobante/factura."""
    gasto = gasto_service.obtener_gasto(db, gasto_id)
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    # Subir a Cloudinary
    url = await subir_imagen(file, folder="comprobantes")

    gasto.comprobante_url = url
    db.commit()

    return {"url": url}

@router.get("/{gasto_id}", response_model=GastoResponse)
def obtener_gasto(
    gasto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    gasto = gasto_service.obtener_gasto(db, gasto_id)
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    return gasto

@router.put("/{gasto_id}", response_model=GastoResponse)
def actualizar_gasto(
    gasto_id: UUID,
    gasto: GastoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    db_gasto = gasto_service.actualizar_gasto(db, gasto_id, gasto)
    if not db_gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    return db_gasto

@router.delete("/{gasto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_gasto(
    gasto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    if not gasto_service.eliminar_gasto(db, gasto_id):
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
```

## Frontend Components

### components/gastos/GastoForm.tsx
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import api from '@/services/api';

const gastoSchema = z.object({
  fecha: z.string().min(1, 'Fecha requerida'),
  categoria: z.string().min(1, 'Categoría requerida'),
  descripcion: z.string().min(1, 'Descripción requerida'),
  monto: z.number().positive('Monto debe ser positivo'),
  proyectoId: z.string().optional(),
  responsableId: z.string().min(1, 'Responsable requerido'),
});

type GastoFormData = z.infer<typeof gastoSchema>;

interface Props {
  onSuccess?: () => void;
}

export function GastoForm({ onSuccess }: Props) {
  const queryClient = useQueryClient();

  const { data: categorias } = useQuery({
    queryKey: ['categorias-gasto'],
    queryFn: () => api.get('/gastos/categorias').then(res => res.data),
  });

  const { data: proyectos } = useQuery({
    queryKey: ['proyectos'],
    queryFn: () => api.get('/proyectos').then(res => res.data),
  });

  const { register, handleSubmit, formState: { errors }, setValue } = useForm<GastoFormData>({
    resolver: zodResolver(gastoSchema),
    defaultValues: {
      fecha: new Date().toISOString().split('T')[0],
    },
  });

  const mutation = useMutation({
    mutationFn: (data: GastoFormData) => api.post('/gastos', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gastos'] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: GastoFormData) => {
    mutation.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Fecha</label>
          <Input type="date" {...register('fecha')} />
          {errors.fecha && <span className="text-primary text-sm">{errors.fecha.message}</span>}
        </div>

        <div>
          <label className="text-sm font-medium">Monto</label>
          <Input
            type="number"
            step="0.01"
            {...register('monto', { valueAsNumber: true })}
            placeholder="0.00"
          />
          {errors.monto && <span className="text-primary text-sm">{errors.monto.message}</span>}
        </div>
      </div>

      <div>
        <label className="text-sm font-medium">Categoría</label>
        <Select onValueChange={(v) => setValue('categoria', v)}>
          <SelectTrigger>
            <SelectValue placeholder="Seleccionar categoría" />
          </SelectTrigger>
          <SelectContent>
            {categorias?.map((cat: { nombre: string }) => (
              <SelectItem key={cat.nombre} value={cat.nombre}>
                {cat.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.categoria && <span className="text-primary text-sm">{errors.categoria.message}</span>}
      </div>

      <div>
        <label className="text-sm font-medium">Proyecto (opcional)</label>
        <Select onValueChange={(v) => setValue('proyectoId', v)}>
          <SelectTrigger>
            <SelectValue placeholder="Gasto general (sin proyecto)" />
          </SelectTrigger>
          <SelectContent>
            {proyectos?.map((p: { id: string; nombre: string }) => (
              <SelectItem key={p.id} value={p.id}>
                {p.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="text-sm font-medium">Descripción</label>
        <Textarea {...register('descripcion')} placeholder="Detalle del gasto..." />
        {errors.descripcion && <span className="text-primary text-sm">{errors.descripcion.message}</span>}
      </div>

      <Button type="submit" className="w-full" disabled={mutation.isPending}>
        {mutation.isPending ? 'Guardando...' : 'Registrar Gasto'}
      </Button>
    </form>
  );
}
```

### components/gastos/GastosChart.tsx
```typescript
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { formatearMonto } from '@/utils/formatters';

interface Props {
  data: Record<string, number>;
}

const COLORS = ['#E53935', '#F97316', '#3B82F6', '#8B5CF6', '#10B981', '#EC4899', '#6B7280'];

export function GastosChart({ data }: Props) {
  const chartData = Object.entries(data).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
        >
          {chartData.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number) => formatearMonto(value)} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
```

## Checklist de Completado
- [ ] Modelo Gasto
- [ ] Modelo CategoriaGasto
- [ ] Schemas Pydantic
- [ ] Service con CRUD y resúmenes
- [ ] Endpoints con permisos
- [ ] Subida de comprobantes a Cloudinary
- [ ] GastoForm component
- [ ] GastosList component
- [ ] GastosChart component (por categoría)
- [ ] ResumenGastos component
- [ ] Filtros por fecha/proyecto/categoría
