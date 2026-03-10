from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS - Use all_cors_origins to include env variable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }


@app.get("/", tags=["Root"])
def root():
    """Root endpoint."""
    return {
        "message": f"Bienvenido a {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "health": "/health"
    }
