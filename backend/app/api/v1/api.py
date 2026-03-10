from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    usuarios,
    proyectos,
    etapas,
    items_trabajo,
    materiales,
    equipos,
    gastos,
    fotos,
    finanzas,
    reportes,
    portal,
    dashboard
)

api_router = APIRouter()

# Auth
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticación"]
)

# Usuarios
api_router.include_router(
    usuarios.router,
    prefix="/usuarios",
    tags=["Usuarios"]
)

# Proyectos
api_router.include_router(
    proyectos.router,
    prefix="/proyectos",
    tags=["Proyectos"]
)

# Etapas
api_router.include_router(
    etapas.router,
    prefix="/etapas",
    tags=["Etapas"]
)

# Items de trabajo
api_router.include_router(
    items_trabajo.router,
    prefix="/items-trabajo",
    tags=["Ítems de Trabajo"]
)

# Materiales
api_router.include_router(
    materiales.router,
    prefix="/materiales",
    tags=["Materiales"]
)

# Equipos
api_router.include_router(
    equipos.router,
    prefix="/equipos",
    tags=["Equipos"]
)

# Gastos
api_router.include_router(
    gastos.router,
    prefix="/gastos",
    tags=["Gastos"]
)

# Fotos
api_router.include_router(
    fotos.router,
    prefix="/fotos",
    tags=["Fotos"]
)

# Finanzas (solo admin/supervisor)
api_router.include_router(
    finanzas.router,
    prefix="/finanzas",
    tags=["Finanzas"]
)

# Reportes
api_router.include_router(
    reportes.router,
    prefix="/reportes",
    tags=["Reportes"]
)

# Portal del cliente
api_router.include_router(
    portal.router,
    prefix="/portal",
    tags=["Portal Cliente"]
)

# Dashboard
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)
