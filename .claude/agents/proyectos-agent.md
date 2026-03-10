# Agente: Proyectos, Etapas e Ítems de Trabajo

## Rol
Implementar el módulo completo de gestión de proyectos, etapas y seguimiento de avance.

## Modelos

### models/proyecto.py
```python
from sqlalchemy import Column, String, Text, Date, Enum, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum

class EstadoProyecto(str, enum.Enum):
    planificacion = "planificacion"
    en_ejecucion = "en_ejecucion"
    pausado = "pausado"
    finalizado = "finalizado"

class Proyecto(Base, BaseModel):
    __tablename__ = "proyectos"

    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    ubicacion = Column(String(255))
    fecha_inicio = Column(Date)
    fecha_fin_estimada = Column(Date)
    fecha_fin_real = Column(Date, nullable=True)
    estado = Column(Enum(EstadoProyecto), default=EstadoProyecto.planificacion)
    porcentaje_avance = Column(Numeric(5, 2), default=0)
    monto_contratado = Column(Numeric(12, 2), nullable=True)  # Solo admin/supervisor
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    # Relaciones
    cliente = relationship("Usuario", foreign_keys=[cliente_id], back_populates="proyectos_asignados")
    creador = relationship("Usuario", foreign_keys=[created_by], back_populates="proyectos_creados")
    etapas = relationship("Etapa", back_populates="proyecto", cascade="all, delete-orphan")
    fotos = relationship("Foto", back_populates="proyecto")
    gastos = relationship("Gasto", back_populates="proyecto")
```

### models/etapa.py
```python
from sqlalchemy import Column, String, Text, Date, Integer, Enum, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum

class EstadoEtapa(str, enum.Enum):
    pendiente = "pendiente"
    en_curso = "en_curso"
    completada = "completada"
    pausada = "pausada"

class Etapa(Base, BaseModel):
    __tablename__ = "etapas"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    orden = Column(Integer, default=0)
    fecha_inicio_est = Column(Date)
    fecha_fin_est = Column(Date)
    fecha_inicio_real = Column(Date, nullable=True)
    fecha_fin_real = Column(Date, nullable=True)
    estado = Column(Enum(EstadoEtapa), default=EstadoEtapa.pendiente)
    porcentaje_avance = Column(Numeric(5, 2), default=0)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="etapas")
    items_trabajo = relationship("ItemTrabajo", back_populates="etapa", cascade="all, delete-orphan")
    fotos = relationship("Foto", back_populates="etapa")
```

### models/item_trabajo.py
```python
from sqlalchemy import Column, String, Numeric, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum

class EstadoItem(str, enum.Enum):
    pendiente = "pendiente"
    en_curso = "en_curso"
    completado = "completado"

class ItemTrabajo(Base, BaseModel):
    __tablename__ = "items_trabajo"

    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=False)
    descripcion = Column(String(255), nullable=False)
    responsable = Column(String(100))
    cantidad = Column(Numeric(10, 2))
    unidad = Column(String(30))
    estado = Column(Enum(EstadoItem), default=EstadoItem.pendiente)
    precio_unitario = Column(Numeric(10, 2), nullable=True)  # Solo admin/supervisor

    # Relaciones
    etapa = relationship("Etapa", back_populates="items_trabajo")
```

## Services

### services/proyecto_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.models.proyecto import Proyecto, EstadoProyecto
from app.models.etapa import Etapa
from app.schemas.proyecto import ProyectoCreate, ProyectoUpdate

def obtener_proyectos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    estado: Optional[EstadoProyecto] = None,
    cliente_id: Optional[UUID] = None
) -> List[Proyecto]:
    query = db.query(Proyecto).filter(Proyecto.activo == True)

    if estado:
        query = query.filter(Proyecto.estado == estado)
    if cliente_id:
        query = query.filter(Proyecto.cliente_id == cliente_id)

    return query.offset(skip).limit(limit).all()

def obtener_proyecto(db: Session, proyecto_id: UUID) -> Optional[Proyecto]:
    return db.query(Proyecto).filter(
        Proyecto.id == proyecto_id,
        Proyecto.activo == True
    ).first()

def crear_proyecto(db: Session, proyecto: ProyectoCreate, usuario_id: UUID) -> Proyecto:
    db_proyecto = Proyecto(
        **proyecto.model_dump(),
        created_by=usuario_id
    )
    db.add(db_proyecto)
    db.commit()
    db.refresh(db_proyecto)
    return db_proyecto

def actualizar_proyecto(db: Session, proyecto_id: UUID, proyecto: ProyectoUpdate) -> Optional[Proyecto]:
    db_proyecto = obtener_proyecto(db, proyecto_id)
    if not db_proyecto:
        return None

    for field, value in proyecto.model_dump(exclude_unset=True).items():
        setattr(db_proyecto, field, value)

    db.commit()
    db.refresh(db_proyecto)
    return db_proyecto

def recalcular_avance_proyecto(db: Session, proyecto_id: UUID) -> Decimal:
    """
    Recalcula el porcentaje de avance global del proyecto
    en base al promedio de sus etapas.
    """
    resultado = db.query(func.avg(Etapa.porcentaje_avance)).filter(
        Etapa.proyecto_id == proyecto_id,
        Etapa.activo == True
    ).scalar()

    avance = Decimal(resultado or 0).quantize(Decimal('0.01'))

    db.query(Proyecto).filter(Proyecto.id == proyecto_id).update({
        "porcentaje_avance": avance
    })
    db.commit()

    return avance

def eliminar_proyecto(db: Session, proyecto_id: UUID) -> bool:
    """Soft delete del proyecto."""
    proyecto = obtener_proyecto(db, proyecto_id)
    if not proyecto:
        return False

    proyecto.activo = False
    db.commit()
    return True
```

## Endpoints

### api/v1/endpoints/proyectos.py
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario, RolUsuario
from app.models.proyecto import EstadoProyecto
from app.schemas.proyecto import ProyectoCreate, ProyectoUpdate, ProyectoResponse, ProyectoDetailResponse
from app.services import proyecto_service

router = APIRouter()

@router.get("/", response_model=List[ProyectoResponse])
def listar_proyectos(
    estado: Optional[EstadoProyecto] = None,
    cliente_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    # Cliente solo ve sus proyectos
    if usuario.rol == RolUsuario.cliente:
        cliente_id = usuario.id

    return proyecto_service.obtener_proyectos(db, skip, limit, estado, cliente_id)

@router.post("/", response_model=ProyectoResponse, status_code=status.HTTP_201_CREATED)
def crear_proyecto(
    proyecto: ProyectoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    return proyecto_service.crear_proyecto(db, proyecto, usuario.id)

@router.get("/{proyecto_id}", response_model=ProyectoDetailResponse)
def obtener_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    proyecto = proyecto_service.obtener_proyecto(db, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Cliente solo ve sus proyectos
    if usuario.rol == RolUsuario.cliente and proyecto.cliente_id != usuario.id:
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    return proyecto

@router.put("/{proyecto_id}", response_model=ProyectoResponse)
def actualizar_proyecto(
    proyecto_id: UUID,
    proyecto: ProyectoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    db_proyecto = proyecto_service.actualizar_proyecto(db, proyecto_id, proyecto)
    if not db_proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return db_proyecto

@router.delete("/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    if not proyecto_service.eliminar_proyecto(db, proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

@router.get("/{proyecto_id}/etapas", response_model=List[EtapaResponse])
def listar_etapas_proyecto(
    proyecto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    proyecto = proyecto_service.obtener_proyecto(db, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    if usuario.rol == RolUsuario.cliente and proyecto.cliente_id != usuario.id:
        raise HTTPException(status_code=403, detail="No tiene acceso a este proyecto")

    return proyecto.etapas
```

## Frontend Types

### types/proyecto.ts
```typescript
export type EstadoProyecto = 'planificacion' | 'en_ejecucion' | 'pausado' | 'finalizado';
export type EstadoEtapa = 'pendiente' | 'en_curso' | 'completada' | 'pausada';
export type EstadoItem = 'pendiente' | 'en_curso' | 'completado';

export interface Proyecto {
  id: string;
  nombre: string;
  descripcion?: string;
  clienteId?: string;
  ubicacion?: string;
  fechaInicio?: string;
  fechaFinEstimada?: string;
  fechaFinReal?: string;
  estado: EstadoProyecto;
  porcentajeAvance: number;
  montoContratado?: number; // Solo admin/supervisor
  createdAt: string;
}

export interface Etapa {
  id: string;
  proyectoId: string;
  nombre: string;
  descripcion?: string;
  orden: number;
  fechaInicioEst?: string;
  fechaFinEst?: string;
  fechaInicioReal?: string;
  fechaFinReal?: string;
  estado: EstadoEtapa;
  porcentajeAvance: number;
}

export interface ItemTrabajo {
  id: string;
  etapaId: string;
  descripcion: string;
  responsable?: string;
  cantidad?: number;
  unidad?: string;
  estado: EstadoItem;
  precioUnitario?: number; // Solo admin/supervisor
}
```

## Frontend Components

### components/proyectos/ProyectoCard.tsx
```typescript
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Proyecto } from '@/types/proyecto';
import { formatearFecha, formatearPorcentaje } from '@/utils/formatters';
import { MapPin, Calendar } from 'lucide-react';

const estadoColors = {
  planificacion: 'bg-gray-500',
  en_ejecucion: 'bg-primary',
  pausado: 'bg-yellow-500',
  finalizado: 'bg-green-500',
};

const estadoLabels = {
  planificacion: 'Planificación',
  en_ejecucion: 'En Ejecución',
  pausado: 'Pausado',
  finalizado: 'Finalizado',
};

interface Props {
  proyecto: Proyecto;
  onClick?: () => void;
}

export function ProyectoCard({ proyecto, onClick }: Props) {
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <h3 className="font-semibold text-lg">{proyecto.nombre}</h3>
          <Badge className={estadoColors[proyecto.estado]}>
            {estadoLabels[proyecto.estado]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {proyecto.ubicacion && (
          <div className="flex items-center text-muted text-sm mb-2">
            <MapPin className="h-4 w-4 mr-1" />
            {proyecto.ubicacion}
          </div>
        )}
        {proyecto.fechaFinEstimada && (
          <div className="flex items-center text-muted text-sm mb-3">
            <Calendar className="h-4 w-4 mr-1" />
            Entrega: {formatearFecha(proyecto.fechaFinEstimada)}
          </div>
        )}
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span>Avance</span>
            <span className="font-medium">{formatearPorcentaje(proyecto.porcentajeAvance)}</span>
          </div>
          <Progress value={proyecto.porcentajeAvance} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
}
```

## Checklist de Completado
- [ ] Modelo Proyecto con estados y relaciones
- [ ] Modelo Etapa con estados
- [ ] Modelo ItemTrabajo
- [ ] Schemas Pydantic completos
- [ ] Service con CRUD y cálculo de avance
- [ ] Endpoints con control de acceso
- [ ] Types TypeScript
- [ ] ProyectoCard component
- [ ] ProyectoList page
- [ ] ProyectoDetail page
- [ ] EtapaForm component
- [ ] ItemTrabajoList component
- [ ] Timeline de avance visual
