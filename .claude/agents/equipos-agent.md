# Agente: Equipos, Maquinaria y Camiones

## Rol
Implementar el módulo completo de ABM de equipos, vehículos y maquinaria con asignación a proyectos.

## Modelos

### models/equipo.py
```python
from sqlalchemy import Column, String, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel
import enum

class TipoEquipo(str, enum.Enum):
    camion = "camion"
    excavadora = "excavadora"
    compactadora = "compactadora"
    hormigonera = "hormigonera"
    herramienta = "herramienta"
    otro = "otro"

class EstadoEquipo(str, enum.Enum):
    disponible = "disponible"
    asignado = "asignado"
    mantenimiento = "mantenimiento"
    fuera_servicio = "fuera_servicio"

class Equipo(Base, BaseModel):
    __tablename__ = "equipos"

    nombre = Column(String(255), nullable=False)
    tipo = Column(Enum(TipoEquipo), nullable=False)
    patente = Column(String(20), nullable=True)
    codigo_interno = Column(String(50), nullable=True)
    estado = Column(Enum(EstadoEquipo), default=EstadoEquipo.disponible)
    observaciones = Column(Text)

    # Relaciones
    asignaciones = relationship("AsignacionEquipo", back_populates="equipo")
```

### models/asignacion_equipo.py
```python
from sqlalchemy import Column, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel

class AsignacionEquipo(Base, BaseModel):
    __tablename__ = "asignaciones_equipo"

    equipo_id = Column(UUID(as_uuid=True), ForeignKey("equipos.id"), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    etapa_id = Column(UUID(as_uuid=True), ForeignKey("etapas.id"), nullable=True)
    fecha_desde = Column(Date, nullable=False)
    fecha_hasta = Column(Date, nullable=True)
    observaciones = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))

    # Relaciones
    equipo = relationship("Equipo", back_populates="asignaciones")
    proyecto = relationship("Proyecto")
    etapa = relationship("Etapa")
    creador = relationship("Usuario")
```

## Services

### services/equipo_service.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import HTTPException
from app.models.equipo import Equipo, EstadoEquipo, TipoEquipo
from app.models.asignacion_equipo import AsignacionEquipo
from app.schemas.equipo import EquipoCreate, EquipoUpdate, AsignacionEquipoCreate

def obtener_equipos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    tipo: Optional[TipoEquipo] = None,
    estado: Optional[EstadoEquipo] = None
) -> List[Equipo]:
    query = db.query(Equipo).filter(Equipo.activo == True)

    if tipo:
        query = query.filter(Equipo.tipo == tipo)
    if estado:
        query = query.filter(Equipo.estado == estado)

    return query.offset(skip).limit(limit).all()

def obtener_equipo(db: Session, equipo_id: UUID) -> Optional[Equipo]:
    return db.query(Equipo).filter(
        Equipo.id == equipo_id,
        Equipo.activo == True
    ).first()

def crear_equipo(db: Session, equipo: EquipoCreate) -> Equipo:
    db_equipo = Equipo(**equipo.model_dump())
    db.add(db_equipo)
    db.commit()
    db.refresh(db_equipo)
    return db_equipo

def actualizar_equipo(db: Session, equipo_id: UUID, equipo: EquipoUpdate) -> Optional[Equipo]:
    db_equipo = obtener_equipo(db, equipo_id)
    if not db_equipo:
        return None

    for field, value in equipo.model_dump(exclude_unset=True).items():
        setattr(db_equipo, field, value)

    db.commit()
    db.refresh(db_equipo)
    return db_equipo

def obtener_equipos_disponibles(db: Session, fecha: date = None) -> List[Equipo]:
    """
    Retorna equipos que están disponibles en una fecha específica.
    """
    if fecha is None:
        fecha = date.today()

    # Equipos que no están en mantenimiento ni fuera de servicio
    # y que no tienen asignación activa en la fecha
    equipos_ocupados = db.query(AsignacionEquipo.equipo_id).filter(
        AsignacionEquipo.fecha_desde <= fecha,
        or_(
            AsignacionEquipo.fecha_hasta.is_(None),
            AsignacionEquipo.fecha_hasta >= fecha
        )
    ).subquery()

    return db.query(Equipo).filter(
        Equipo.activo == True,
        Equipo.estado.in_([EstadoEquipo.disponible, EstadoEquipo.asignado]),
        ~Equipo.id.in_(equipos_ocupados)
    ).all()

def asignar_equipo_a_proyecto(
    db: Session,
    asignacion: AsignacionEquipoCreate,
    usuario_id: UUID
) -> AsignacionEquipo:
    """
    Asigna un equipo a un proyecto y actualiza su estado.
    """
    equipo = obtener_equipo(db, asignacion.equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    if equipo.estado in [EstadoEquipo.mantenimiento, EstadoEquipo.fuera_servicio]:
        raise HTTPException(
            status_code=400,
            detail=f"El equipo está en {equipo.estado.value}"
        )

    # Verificar que no tenga asignación activa en las fechas
    conflicto = db.query(AsignacionEquipo).filter(
        AsignacionEquipo.equipo_id == asignacion.equipo_id,
        AsignacionEquipo.fecha_desde <= (asignacion.fecha_hasta or date(2100, 1, 1)),
        or_(
            AsignacionEquipo.fecha_hasta.is_(None),
            AsignacionEquipo.fecha_hasta >= asignacion.fecha_desde
        )
    ).first()

    if conflicto:
        raise HTTPException(
            status_code=400,
            detail="El equipo ya tiene una asignación en esas fechas"
        )

    # Crear asignación
    db_asignacion = AsignacionEquipo(
        equipo_id=asignacion.equipo_id,
        proyecto_id=asignacion.proyecto_id,
        etapa_id=asignacion.etapa_id,
        fecha_desde=asignacion.fecha_desde,
        fecha_hasta=asignacion.fecha_hasta,
        observaciones=asignacion.observaciones,
        created_by=usuario_id
    )
    db.add(db_asignacion)

    # Actualizar estado del equipo
    equipo.estado = EstadoEquipo.asignado

    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

def finalizar_asignacion(db: Session, asignacion_id: UUID) -> AsignacionEquipo:
    """
    Finaliza una asignación y libera el equipo.
    """
    asignacion = db.query(AsignacionEquipo).filter(
        AsignacionEquipo.id == asignacion_id
    ).first()

    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    asignacion.fecha_hasta = date.today()

    # Verificar si el equipo tiene otras asignaciones activas
    otras_asignaciones = db.query(AsignacionEquipo).filter(
        AsignacionEquipo.equipo_id == asignacion.equipo_id,
        AsignacionEquipo.id != asignacion_id,
        or_(
            AsignacionEquipo.fecha_hasta.is_(None),
            AsignacionEquipo.fecha_hasta >= date.today()
        )
    ).first()

    if not otras_asignaciones:
        asignacion.equipo.estado = EstadoEquipo.disponible

    db.commit()
    db.refresh(asignacion)
    return asignacion

def obtener_historial_equipo(
    db: Session,
    equipo_id: UUID,
    limit: int = 50
) -> List[AsignacionEquipo]:
    """
    Retorna el historial de asignaciones de un equipo.
    """
    return db.query(AsignacionEquipo).filter(
        AsignacionEquipo.equipo_id == equipo_id
    ).order_by(AsignacionEquipo.fecha_desde.desc()).limit(limit).all()
```

## Endpoints

### api/v1/endpoints/equipos.py
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.models.equipo import TipoEquipo, EstadoEquipo
from app.schemas.equipo import (
    EquipoCreate, EquipoUpdate, EquipoResponse,
    AsignacionEquipoCreate, AsignacionEquipoResponse
)
from app.services import equipo_service

router = APIRouter()

@router.get("/", response_model=List[EquipoResponse])
def listar_equipos(
    tipo: Optional[TipoEquipo] = None,
    estado: Optional[EstadoEquipo] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return equipo_service.obtener_equipos(db, skip, limit, tipo, estado)

@router.get("/disponibles", response_model=List[EquipoResponse])
def listar_equipos_disponibles(
    fecha: Optional[date] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return equipo_service.obtener_equipos_disponibles(db, fecha)

@router.post("/", response_model=EquipoResponse, status_code=status.HTTP_201_CREATED)
def crear_equipo(
    equipo: EquipoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    return equipo_service.crear_equipo(db, equipo)

@router.get("/{equipo_id}", response_model=EquipoResponse)
def obtener_equipo(
    equipo_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    equipo = equipo_service.obtener_equipo(db, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return equipo

@router.put("/{equipo_id}", response_model=EquipoResponse)
def actualizar_equipo(
    equipo_id: UUID,
    equipo: EquipoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_supervisor)
):
    db_equipo = equipo_service.actualizar_equipo(db, equipo_id, equipo)
    if not db_equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return db_equipo

@router.post("/{equipo_id}/asignar", response_model=AsignacionEquipoResponse)
def asignar_equipo(
    equipo_id: UUID,
    asignacion: AsignacionEquipoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    asignacion.equipo_id = equipo_id
    return equipo_service.asignar_equipo_a_proyecto(db, asignacion, usuario.id)

@router.get("/{equipo_id}/historial", response_model=List[AsignacionEquipoResponse])
def obtener_historial_equipo(
    equipo_id: UUID,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return equipo_service.obtener_historial_equipo(db, equipo_id, limit)
```

## Frontend Types

### types/equipo.ts
```typescript
export type TipoEquipo = 'camion' | 'excavadora' | 'compactadora' | 'hormigonera' | 'herramienta' | 'otro';
export type EstadoEquipo = 'disponible' | 'asignado' | 'mantenimiento' | 'fuera_servicio';

export interface Equipo {
  id: string;
  nombre: string;
  tipo: TipoEquipo;
  patente?: string;
  codigoInterno?: string;
  estado: EstadoEquipo;
  observaciones?: string;
  createdAt: string;
}

export interface AsignacionEquipo {
  id: string;
  equipoId: string;
  proyectoId: string;
  etapaId?: string;
  fechaDesde: string;
  fechaHasta?: string;
  observaciones?: string;
  equipo?: Equipo;
  proyecto?: { id: string; nombre: string };
}
```

## Frontend Components

### components/equipos/EquipoCard.tsx
```typescript
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Equipo, EstadoEquipo, TipoEquipo } from '@/types/equipo';
import { Truck, HardHat, Wrench, Package } from 'lucide-react';

const tipoIcons: Record<TipoEquipo, React.ReactNode> = {
  camion: <Truck className="h-5 w-5" />,
  excavadora: <HardHat className="h-5 w-5" />,
  compactadora: <HardHat className="h-5 w-5" />,
  hormigonera: <Package className="h-5 w-5" />,
  herramienta: <Wrench className="h-5 w-5" />,
  otro: <Package className="h-5 w-5" />,
};

const estadoColors: Record<EstadoEquipo, string> = {
  disponible: 'bg-green-500',
  asignado: 'bg-primary',
  mantenimiento: 'bg-yellow-500',
  fuera_servicio: 'bg-gray-500',
};

const estadoLabels: Record<EstadoEquipo, string> = {
  disponible: 'Disponible',
  asignado: 'Asignado',
  mantenimiento: 'Mantenimiento',
  fuera_servicio: 'Fuera de Servicio',
};

interface Props {
  equipo: Equipo;
  onClick?: () => void;
}

export function EquipoCard({ equipo, onClick }: Props) {
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-light rounded-lg text-primary">
              {tipoIcons[equipo.tipo]}
            </div>
            <div>
              <h3 className="font-semibold">{equipo.nombre}</h3>
              {equipo.patente && (
                <p className="text-sm text-muted">{equipo.patente}</p>
              )}
              {equipo.codigoInterno && (
                <p className="text-xs text-muted">Cód: {equipo.codigoInterno}</p>
              )}
            </div>
          </div>
          <Badge className={estadoColors[equipo.estado]}>
            {estadoLabels[equipo.estado]}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
```

## Checklist de Completado
- [ ] Modelo Equipo con tipos y estados
- [ ] Modelo AsignacionEquipo
- [ ] Schemas Pydantic
- [ ] Service con CRUD y lógica de asignación
- [ ] Endpoints con permisos
- [ ] Types TypeScript
- [ ] EquipoCard component
- [ ] EquipoList page
- [ ] EquipoForm modal
- [ ] AsignacionForm modal
- [ ] HistorialEquipo component
- [ ] Calendario de asignaciones
