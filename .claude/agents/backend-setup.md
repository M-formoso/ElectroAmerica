# Agente: Backend Setup

## Rol
Configuración inicial del backend con FastAPI, PostgreSQL, SQLAlchemy y toda la estructura base.

## Responsabilidades

### 1. Estructura de Carpetas
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py
│   │       └── endpoints/
│   │           └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── deps.py
│   │   └── celery_app.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── base_class.py
│   │   ├── session.py
│   │   └── init_db.py
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   └── tasks/
│       └── __init__.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── api/
├── alembic.ini
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

### 2. Archivos Base a Crear

#### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
pydantic==2.5.2
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
celery==5.3.4
redis==5.0.1
cloudinary==1.36.0
weasyprint==60.1
openpyxl==3.1.2
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

#### app/core/config.py
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Electro América API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
```

#### app/db/base_class.py
```python
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func
import uuid

class BaseModel:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    activo = Column(Boolean, default=True)
```

#### app/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.VERSION}
```

### 3. Comandos de Inicialización
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 4. Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Checklist de Completado
- [ ] Estructura de carpetas creada
- [ ] requirements.txt con dependencias
- [ ] Configuración Pydantic Settings
- [ ] Base class para modelos
- [ ] main.py con FastAPI
- [ ] Alembic configurado
- [ ] Dockerfile listo
- [ ] .env.example creado
