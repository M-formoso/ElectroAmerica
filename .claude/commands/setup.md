# /setup - Inicializar Proyecto Completo

Inicializa el proyecto completo de Electro América desde cero.

## Pasos a ejecutar:

### 1. Crear estructura del monorepo
```bash
mkdir -p electro-america-system/{frontend,backend,docs}
cd electro-america-system
```

### 2. Inicializar Backend (FastAPI)
Consultar `.claude/agents/backend-setup.md` y crear:
- Estructura de carpetas
- requirements.txt
- Configuración de FastAPI
- SQLAlchemy + Alembic
- Docker configuration

### 3. Inicializar Frontend (React + Vite)
Consultar `.claude/agents/frontend-setup.md` y ejecutar:
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npx tailwindcss init -p
npx shadcn-ui@latest init
```

### 4. Configurar Docker Compose
Crear `docker-compose.yml` con:
- PostgreSQL 15
- Redis
- Backend (FastAPI)
- Frontend (React)
- Nginx (producción)

### 5. Crear archivos de configuración
- `.env.example`
- `.gitignore`
- `README.md`

## Colores de la marca (usar en Tailwind):
- Rojo Principal: `#E53935`
- Rojo Oscuro: `#C62828`
- Rojo Claro: `#FFEBEE`
- Negro: `#1A1A1A`
- Gris: `#424242`
- Fondo: `#F5F5F5`

## Al finalizar:
1. Verificar que todo compile
2. Ejecutar `docker-compose up -d`
3. Verificar health check del backend
4. Verificar que el frontend cargue

---
*Referencia: `.claude/CLAUDE.md` para especificaciones completas*
