# /backend - Operaciones Backend

Ejecuta operaciones comunes del backend.

## Argumentos:
- `run` - Ejecutar servidor de desarrollo
- `migrate` - Crear y aplicar migraciones
- `test` - Ejecutar tests
- `shell` - Abrir shell de Python

## Comandos:

### Ejecutar servidor
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Crear migración
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Descripción del cambio"
alembic upgrade head
```

### Ejecutar tests
```bash
cd backend
source venv/bin/activate
pytest -v
pytest --cov=app tests/
```

### Instalar dependencias
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

## Estructura esperada:
```
backend/
├── app/
│   ├── api/v1/endpoints/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── tasks/
├── alembic/
├── tests/
└── requirements.txt
```

## Endpoints base:
- `GET /health` - Health check
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Usuario actual

---
*Referencia: `.claude/agents/backend-setup.md`*
