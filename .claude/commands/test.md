# /test - Ejecutar Tests

Ejecuta la suite de tests del proyecto.

## Argumentos:
- `all` - Ejecutar todos los tests
- `backend` - Solo tests del backend
- `frontend` - Solo tests del frontend
- `coverage` - Con reporte de cobertura

## Backend Tests

### Ejecutar todos los tests
```bash
cd backend
source venv/bin/activate
pytest -v
```

### Con cobertura
```bash
cd backend
source venv/bin/activate
pytest --cov=app tests/ --cov-report=html
```

### Test específico
```bash
pytest tests/api/test_proyectos.py -v
pytest tests/api/test_auth.py::test_login -v
```

### Tests por módulo
```bash
pytest tests/api/test_auth.py -v
pytest tests/api/test_proyectos.py -v
pytest tests/api/test_materiales.py -v
pytest tests/api/test_equipos.py -v
pytest tests/api/test_gastos.py -v
```

## Frontend Tests

### Ejecutar tests
```bash
cd frontend
npm run test
```

### Con cobertura
```bash
cd frontend
npm run test:coverage
```

## Estructura de tests:

### Backend
```
backend/tests/
├── conftest.py          # Fixtures compartidas
├── api/
│   ├── test_auth.py
│   ├── test_proyectos.py
│   ├── test_materiales.py
│   ├── test_equipos.py
│   ├── test_gastos.py
│   └── test_portal.py   # Tests de seguridad del portal
└── services/
    └── test_*.py
```

### Frontend
```
frontend/src/
├── __tests__/
│   ├── components/
│   └── pages/
└── *.test.tsx
```

## Tests críticos de seguridad:
1. Cliente no accede a proyectos de otros
2. Operario no ve finanzas
3. Tokens JWT expiran correctamente
4. Soft delete funciona

---
*Referencia: Documentación de cada agente para tests específicos*
