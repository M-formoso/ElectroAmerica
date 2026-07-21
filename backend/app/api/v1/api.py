from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    usuarios,
    clientes,
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
    dashboard,
    upload,
    alertas,
    jornadas,
    auditoria,
    jornadas_operario,
    asignaciones_diarias,
    actividades_tipo,
    herramientas,
    requerimientos_material,
    proyecto_actividades,
    depositos,
    remitos,
    listas_precio,
    panel_socios,
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

# Clientes
api_router.include_router(
    clientes.router,
    prefix="/clientes",
    tags=["Clientes"]
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

# Upload de archivos
api_router.include_router(
    upload.router,
    prefix="/upload",
    tags=["Upload"]
)

# Alertas
api_router.include_router(
    alertas.router,
    prefix="/alertas",
    tags=["Alertas"]
)

# Jornadas (mano de obra)
api_router.include_router(
    jornadas.router,
    prefix="/jornadas",
    tags=["Jornadas"]
)

# Auditoría (solo admin)
api_router.include_router(
    auditoria.router,
    prefix="/auditoria",
    tags=["Auditoría"]
)

# Jornadas de operarios (nuevo módulo)
api_router.include_router(
    jornadas_operario.router,
    prefix="/jornadas-operario",
    tags=["Jornadas Operario"]
)

# Asignaciones diarias (planificación)
api_router.include_router(
    asignaciones_diarias.router,
    prefix="/asignaciones-diarias",
    tags=["Asignaciones Diarias"]
)

# Actividades tipo (catálogo)
api_router.include_router(
    actividades_tipo.router,
    prefix="/actividades-tipo",
    tags=["Actividades Tipo"]
)

# Herramientas y préstamos
api_router.include_router(
    herramientas.router,
    prefix="/herramientas",
    tags=["Herramientas"]
)

# Requerimientos de material
api_router.include_router(
    requerimientos_material.router,
    prefix="/requerimientos-material",
    tags=["Requerimientos Material"]
)

# Actividades de proyecto y avances
api_router.include_router(
    proyecto_actividades.router,
    prefix="/proyectos",
    tags=["Actividades de Proyecto"]
)

# Depositos por cliente
api_router.include_router(
    depositos.router,
    prefix="/depositos",
    tags=["Depositos"]
)

# Remitos de salida
api_router.include_router(
    remitos.router,
    prefix="/remitos",
    tags=["Remitos"]
)

# Listas de precios
api_router.include_router(
    listas_precio.router,
    prefix="/listas-precio",
    tags=["Listas de Precio"]
)

# Panel de Socios (control gerencial)
api_router.include_router(
    panel_socios.router,
    prefix="/panel-socios",
    tags=["Panel Socios"]
)
