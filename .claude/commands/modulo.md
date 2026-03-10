# /modulo - Crear Nuevo Módulo

Crea la estructura completa de un nuevo módulo siguiendo los estándares del proyecto.

## Uso:
```
/modulo [nombre]
```

## Estructura a crear:

### Backend
```
backend/app/
├── models/{nombre}.py
├── schemas/{nombre}.py
├── services/{nombre}_service.py
├── api/v1/endpoints/{nombre}.py
└── tests/api/test_{nombre}.py
```

### Frontend
```
frontend/src/
├── components/{nombre}/
│   ├── {Nombre}List.tsx
│   ├── {Nombre}Form.tsx
│   ├── {Nombre}Detail.tsx
│   └── index.ts
├── pages/{nombre}/
│   ├── index.tsx
│   ├── create.tsx
│   └── [id].tsx
├── services/{nombre}Service.ts
└── types/{nombre}.ts
```

## Template: Model (Backend)
```python
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base, BaseModel

class {Nombre}(Base, BaseModel):
    __tablename__ = "{nombre}s"

    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    # Agregar campos específicos
```

## Template: Schema (Backend)
```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class {Nombre}Base(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class {Nombre}Create({Nombre}Base):
    pass

class {Nombre}Update(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class {Nombre}Response({Nombre}Base):
    id: UUID
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

## Template: Service (Backend)
```python
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.models.{nombre} import {Nombre}
from app.schemas.{nombre} import {Nombre}Create, {Nombre}Update

def obtener_{nombre}s(db: Session, skip: int = 0, limit: int = 100) -> List[{Nombre}]:
    return db.query({Nombre}).filter({Nombre}.activo == True).offset(skip).limit(limit).all()

def obtener_{nombre}(db: Session, {nombre}_id: UUID) -> Optional[{Nombre}]:
    return db.query({Nombre}).filter({Nombre}.id == {nombre}_id, {Nombre}.activo == True).first()

def crear_{nombre}(db: Session, {nombre}: {Nombre}Create) -> {Nombre}:
    db_{nombre} = {Nombre}(**{nombre}.model_dump())
    db.add(db_{nombre})
    db.commit()
    db.refresh(db_{nombre})
    return db_{nombre}

def actualizar_{nombre}(db: Session, {nombre}_id: UUID, {nombre}: {Nombre}Update) -> Optional[{Nombre}]:
    db_{nombre} = obtener_{nombre}(db, {nombre}_id)
    if not db_{nombre}:
        return None
    for field, value in {nombre}.model_dump(exclude_unset=True).items():
        setattr(db_{nombre}, field, value)
    db.commit()
    db.refresh(db_{nombre})
    return db_{nombre}

def eliminar_{nombre}(db: Session, {nombre}_id: UUID) -> bool:
    {nombre} = obtener_{nombre}(db, {nombre}_id)
    if not {nombre}:
        return False
    {nombre}.activo = False
    db.commit()
    return True
```

## Template: Endpoint (Backend)
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.deps import get_db, get_usuario_actual, require_staff
from app.models.usuario import Usuario
from app.schemas.{nombre} import {Nombre}Create, {Nombre}Update, {Nombre}Response
from app.services import {nombre}_service

router = APIRouter()

@router.get("/", response_model=List[{Nombre}Response])
def listar_{nombre}s(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return {nombre}_service.obtener_{nombre}s(db, skip, limit)

@router.post("/", response_model={Nombre}Response, status_code=status.HTTP_201_CREATED)
def crear_{nombre}(
    {nombre}: {Nombre}Create,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    return {nombre}_service.crear_{nombre}(db, {nombre})

@router.get("/{{nombre}_id}", response_model={Nombre}Response)
def obtener_{nombre}(
    {nombre}_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    db_{nombre} = {nombre}_service.obtener_{nombre}(db, {nombre}_id)
    if not db_{nombre}:
        raise HTTPException(status_code=404, detail="{Nombre} no encontrado")
    return db_{nombre}
```

## Registrar en API
Agregar en `backend/app/api/v1/api.py`:
```python
from app.api.v1.endpoints import {nombre}
api_router.include_router({nombre}.router, prefix="/{nombre}s", tags=["{Nombre}s"])
```

---
*Referencia: `.claude/CLAUDE.md` para convenciones completas*
