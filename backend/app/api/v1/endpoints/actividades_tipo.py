from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.deps import get_db, get_usuario_actual, require_staff, require_admin_or_supervisor
from app.models.usuario import Usuario
from app.schemas.actividad_tipo import (
    ActividadTipoCreate, ActividadTipoUpdate, ActividadTipoResponse,
    ActividadTipoListResponse, MaterialActividadTipoCreate, MaterialActividadTipoUpdate,
    MaterialActividadTipoResponse, CalcularMaterialesRequest, CalcularMaterialesResponse,
    ListarCategoriasResponse
)
from app.services import actividad_tipo_service

router = APIRouter()


# ============== CRUD ACTIVIDADES TIPO ==============

@router.get("", response_model=List[ActividadTipoListResponse])
async def listar_actividades_tipo(
    categoria: Optional[str] = None,
    busqueda: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Lista actividades tipo con filtros."""
    actividades = actividad_tipo_service.get_actividades_tipo(
        db, categoria=categoria, busqueda=busqueda, skip=skip, limit=limit
    )

    return [
        ActividadTipoListResponse(
            id=a.id,
            codigo=a.codigo,
            nombre=a.nombre,
            categoria=a.categoria,
            unidad_trabajo=a.unidad_trabajo,
            cantidad_materiales=len([m for m in a.materiales if m.activo]),
            activo=a.activo
        )
        for a in actividades
    ]


@router.get("/categorias", response_model=ListarCategoriasResponse)
async def listar_categorias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Lista las categorías de actividades existentes."""
    categorias = actividad_tipo_service.get_categorias(db)
    return ListarCategoriasResponse(categorias=categorias)


@router.get("/{actividad_id}", response_model=ActividadTipoResponse)
async def obtener_actividad_tipo(
    actividad_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Obtiene una actividad tipo con sus materiales."""
    actividad = actividad_tipo_service.get_actividad_tipo(db, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad tipo no encontrada")
    return actividad_tipo_service.enrich_actividad_response(db, actividad)


@router.post("", response_model=ActividadTipoResponse)
async def crear_actividad_tipo(
    actividad: ActividadTipoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Crea una nueva actividad tipo con sus materiales (solo supervisor/admin)."""
    try:
        nueva = actividad_tipo_service.create_actividad_tipo(db, actividad)
        return actividad_tipo_service.enrich_actividad_response(db, nueva)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{actividad_id}", response_model=ActividadTipoResponse)
async def actualizar_actividad_tipo(
    actividad_id: UUID,
    actividad: ActividadTipoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza una actividad tipo (solo supervisor/admin)."""
    try:
        actualizada = actividad_tipo_service.update_actividad_tipo(db, actividad_id, actividad)
        if not actualizada:
            raise HTTPException(status_code=404, detail="Actividad tipo no encontrada")
        return actividad_tipo_service.enrich_actividad_response(db, actualizada)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{actividad_id}")
async def eliminar_actividad_tipo(
    actividad_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina una actividad tipo (solo supervisor/admin)."""
    if not actividad_tipo_service.delete_actividad_tipo(db, actividad_id):
        raise HTTPException(status_code=404, detail="Actividad tipo no encontrada")
    return {"message": "Actividad tipo eliminada"}


# ============== MATERIALES DE ACTIVIDAD ==============

@router.get("/{actividad_id}/materiales", response_model=List[MaterialActividadTipoResponse])
async def listar_materiales_actividad(
    actividad_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """Lista los materiales de una actividad tipo."""
    actividad = actividad_tipo_service.get_actividad_tipo(db, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad tipo no encontrada")

    enriched = actividad_tipo_service.enrich_actividad_response(db, actividad)
    return enriched.get("materiales", [])


@router.post("/{actividad_id}/materiales", response_model=MaterialActividadTipoResponse)
async def agregar_material_actividad(
    actividad_id: UUID,
    material: MaterialActividadTipoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Agrega un material a una actividad tipo (solo supervisor/admin)."""
    try:
        nuevo = actividad_tipo_service.add_material_actividad(db, actividad_id, material)

        # Obtener datos del material para la respuesta
        from app.models.material import Material
        mat = db.query(Material).filter(Material.id == nuevo.material_id).first()

        return MaterialActividadTipoResponse(
            id=nuevo.id,
            actividad_tipo_id=nuevo.actividad_tipo_id,
            material_id=nuevo.material_id,
            cantidad_por_unidad=float(nuevo.cantidad_por_unidad),
            es_opcional=nuevo.es_opcional,
            notas=nuevo.notas,
            activo=nuevo.activo,
            material_codigo=mat.codigo if mat else None,
            material_nombre=mat.nombre if mat else None,
            material_unidad=mat.unidad if mat else None,
            material_stock_actual=float(mat.stock_actual) if mat else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/materiales/{material_actividad_id}", response_model=MaterialActividadTipoResponse)
async def actualizar_material_actividad(
    material_actividad_id: UUID,
    material: MaterialActividadTipoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Actualiza un material de una actividad tipo (solo supervisor/admin)."""
    actualizado = actividad_tipo_service.update_material_actividad(db, material_actividad_id, material)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Material de actividad no encontrado")

    from app.models.material import Material
    mat = db.query(Material).filter(Material.id == actualizado.material_id).first()

    return MaterialActividadTipoResponse(
        id=actualizado.id,
        actividad_tipo_id=actualizado.actividad_tipo_id,
        material_id=actualizado.material_id,
        cantidad_por_unidad=float(actualizado.cantidad_por_unidad),
        es_opcional=actualizado.es_opcional,
        notas=actualizado.notas,
        activo=actualizado.activo,
        material_codigo=mat.codigo if mat else None,
        material_nombre=mat.nombre if mat else None,
        material_unidad=mat.unidad if mat else None,
        material_stock_actual=float(mat.stock_actual) if mat else None
    )


@router.delete("/materiales/{material_actividad_id}")
async def eliminar_material_actividad(
    material_actividad_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_supervisor)
):
    """Elimina un material de una actividad tipo (solo supervisor/admin)."""
    if not actividad_tipo_service.remove_material_actividad(db, material_actividad_id):
        raise HTTPException(status_code=404, detail="Material de actividad no encontrado")
    return {"message": "Material eliminado de la actividad"}


# ============== CÁLCULO DE MATERIALES ==============

@router.post("/calcular-materiales", response_model=CalcularMaterialesResponse)
async def calcular_materiales(
    request: CalcularMaterialesRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_staff)
):
    """
    Calcula los materiales necesarios para una cantidad de trabajo.

    Ejemplo:
    - actividad_tipo_id: UUID de "Instalación tablero monofásico"
    - cantidad_trabajo: 3 (instalar 3 tableros)

    Retorna la lista de materiales con cantidades calculadas y alertas de stock.
    """
    try:
        return actividad_tipo_service.calcular_materiales_actividad(
            db, request.actividad_tipo_id, request.cantidad_trabajo
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
