from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.core.deps import get_db, get_usuario_actual, require_staff
from app.models.usuario import Usuario
from app.schemas.etapa import EtapaCreate, EtapaUpdate, EtapaResponse
from app.schemas.foto import FotoResponse
from app.services import etapa_service, proyecto_service, foto_service

router = APIRouter()


@router.get("/", response_model=List[EtapaResponse])
def listar_etapas(
    proyecto_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista etapas, opcionalmente filtradas por proyecto."""
    return etapa_service.obtener_etapas(db, proyecto_id, skip, limit)


@router.post("/", response_model=EtapaResponse, status_code=status.HTTP_201_CREATED)
def crear_etapa(
    etapa: EtapaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Crea una nueva etapa."""
    # Verificar que el proyecto existe
    proyecto = proyecto_service.obtener_proyecto(db, etapa.proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return etapa_service.crear_etapa(db, etapa)


@router.get("/demoradas", response_model=List[EtapaResponse])
def listar_etapas_demoradas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista etapas cuya fecha estimada ha pasado y no están completadas."""
    return etapa_service.obtener_etapas_demoradas(db)


@router.get("/{etapa_id}", response_model=EtapaResponse)
def obtener_etapa(
    etapa_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Obtiene una etapa por ID."""
    etapa = etapa_service.obtener_etapa(db, etapa_id)
    if not etapa:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    return etapa


@router.put("/{etapa_id}", response_model=EtapaResponse)
def actualizar_etapa(
    etapa_id: UUID,
    etapa: EtapaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Actualiza una etapa."""
    db_etapa = etapa_service.actualizar_etapa(db, etapa_id, etapa)
    if not db_etapa:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    return db_etapa


@router.delete("/{etapa_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_etapa(
    etapa_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Elimina una etapa (soft delete)."""
    if not etapa_service.eliminar_etapa(db, etapa_id):
        raise HTTPException(status_code=404, detail="Etapa no encontrada")


@router.put("/{etapa_id}/avance")
def actualizar_avance_etapa(
    etapa_id: UUID,
    porcentaje: Decimal = Query(..., ge=0, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Actualiza el porcentaje de avance de una etapa."""
    etapa = etapa_service.actualizar_avance_etapa(db, etapa_id, porcentaje)
    if not etapa:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")

    return {
        "etapa_id": str(etapa.id),
        "porcentaje_avance": float(etapa.porcentaje_avance),
        "estado": etapa.estado.value
    }


@router.get("/{etapa_id}/fotos", response_model=List[FotoResponse])
def listar_fotos_etapa(
    etapa_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Lista las fotos de una etapa."""
    etapa = etapa_service.obtener_etapa(db, etapa_id)
    if not etapa:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")

    return foto_service.obtener_fotos(db, etapa_id=etapa_id)


@router.post("/reordenar")
def reordenar_etapas(
    proyecto_id: UUID,
    orden_ids: List[UUID],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_staff)
):
    """Reordena las etapas de un proyecto."""
    etapa_service.reordenar_etapas(db, proyecto_id, orden_ids)
    return {"message": "Etapas reordenadas"}
