from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.deps import get_db, get_usuario_actual, require_staff
from app.models.usuario import Usuario
from app.schemas.gasto import (
    GastoCreate, GastoUpdate, GastoResponse,
    CategoriaGastoCreate, CategoriaGastoResponse,
    ResumenGastosPeriodo
)
from app.services import gasto_service

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
    """Lista gastos con filtros opcionales."""
    gastos = gasto_service.obtener_gastos(
        db, skip, limit, proyecto_id, categoria, fecha_desde, fecha_hasta
    )

    return [
        GastoResponse(
            id=g.id,
            fecha=g.fecha,
            categoria=g.categoria,
            descripcion=g.descripcion,
            monto=g.monto,
            proyecto_id=g.proyecto_id,
            responsable_id=g.responsable_id,
            comprobante_url=g.comprobante_url,
            activo=g.activo,
            created_at=g.created_at,
            proyecto_nombre=g.proyecto.nombre if g.proyecto else None,
            responsable_nombre=g.responsable.nombre if g.responsable else None
        )
        for g in gastos
    ]


@router.get("/resumen", response_model=ResumenGastosPeriodo)
def obtener_resumen(
    fecha_desde: date,
    fecha_hasta: date,
    proyecto_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene resumen de gastos por período."""
    return gasto_service.obtener_resumen_gastos(db, fecha_desde, fecha_hasta, proyecto_id)


@router.get("/por-proyecto/{proyecto_id}", response_model=List[GastoResponse])
def listar_gastos_proyecto(
    proyecto_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista los gastos de un proyecto específico."""
    gastos = gasto_service.obtener_gastos(db, skip, limit, proyecto_id=proyecto_id)

    return [
        GastoResponse(
            id=g.id,
            fecha=g.fecha,
            categoria=g.categoria,
            descripcion=g.descripcion,
            monto=g.monto,
            proyecto_id=g.proyecto_id,
            responsable_id=g.responsable_id,
            comprobante_url=g.comprobante_url,
            activo=g.activo,
            created_at=g.created_at,
            proyecto_nombre=g.proyecto.nombre if g.proyecto else None,
            responsable_nombre=g.responsable.nombre if g.responsable else None
        )
        for g in gastos
    ]


@router.get("/categorias", response_model=List[CategoriaGastoResponse])
def listar_categorias(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista las categorías de gasto."""
    return gasto_service.obtener_categorias(db)


@router.post("/categorias", response_model=CategoriaGastoResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    categoria: CategoriaGastoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Crea una nueva categoría de gasto."""
    return gasto_service.crear_categoria(db, categoria)


@router.post("/", response_model=GastoResponse, status_code=status.HTTP_201_CREATED)
def crear_gasto(
    gasto: GastoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Crea un nuevo gasto."""
    db_gasto = gasto_service.crear_gasto(db, gasto, usuario.id)

    return GastoResponse(
        id=db_gasto.id,
        fecha=db_gasto.fecha,
        categoria=db_gasto.categoria,
        descripcion=db_gasto.descripcion,
        monto=db_gasto.monto,
        proyecto_id=db_gasto.proyecto_id,
        responsable_id=db_gasto.responsable_id,
        comprobante_url=db_gasto.comprobante_url,
        activo=db_gasto.activo,
        created_at=db_gasto.created_at,
        proyecto_nombre=db_gasto.proyecto.nombre if db_gasto.proyecto else None,
        responsable_nombre=db_gasto.responsable.nombre if db_gasto.responsable else None
    )


@router.get("/{gasto_id}", response_model=GastoResponse)
def obtener_gasto(
    gasto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene un gasto por ID."""
    gasto = gasto_service.obtener_gasto(db, gasto_id)
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    return GastoResponse(
        id=gasto.id,
        fecha=gasto.fecha,
        categoria=gasto.categoria,
        descripcion=gasto.descripcion,
        monto=gasto.monto,
        proyecto_id=gasto.proyecto_id,
        responsable_id=gasto.responsable_id,
        comprobante_url=gasto.comprobante_url,
        activo=gasto.activo,
        created_at=gasto.created_at,
        proyecto_nombre=gasto.proyecto.nombre if gasto.proyecto else None,
        responsable_nombre=gasto.responsable.nombre if gasto.responsable else None
    )


@router.put("/{gasto_id}", response_model=GastoResponse)
def actualizar_gasto(
    gasto_id: UUID,
    gasto: GastoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Actualiza un gasto."""
    db_gasto = gasto_service.actualizar_gasto(db, gasto_id, gasto)
    if not db_gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    return GastoResponse(
        id=db_gasto.id,
        fecha=db_gasto.fecha,
        categoria=db_gasto.categoria,
        descripcion=db_gasto.descripcion,
        monto=db_gasto.monto,
        proyecto_id=db_gasto.proyecto_id,
        responsable_id=db_gasto.responsable_id,
        comprobante_url=db_gasto.comprobante_url,
        activo=db_gasto.activo,
        created_at=db_gasto.created_at,
        proyecto_nombre=db_gasto.proyecto.nombre if db_gasto.proyecto else None,
        responsable_nombre=db_gasto.responsable.nombre if db_gasto.responsable else None
    )


@router.delete("/{gasto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_gasto(
    gasto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Elimina un gasto (soft delete)."""
    if not gasto_service.eliminar_gasto(db, gasto_id):
        raise HTTPException(status_code=404, detail="Gasto no encontrado")


@router.post("/inicializar-categorias")
def inicializar_categorias(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Inicializa las categorías por defecto."""
    gasto_service.inicializar_categorias(db)
    return {"message": "Categorías inicializadas"}
