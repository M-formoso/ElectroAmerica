# CLAUDE.md — Agente Principal Sistema Electro América

## Identidad del Proyecto

**Nombre:** Sistema de Gestión Electro América
**Empresa:** Electro América - Servicios de Ingeniería y Construcción
**Ubicación:** Argentina

### Identidad Visual
- **Rojo Principal:** `#E53935` (logo rayo)
- **Rojo Oscuro:** `#C62828` (hover/activo)
- **Negro:** `#1A1A1A` (texto principal)
- **Gris Oscuro:** `#424242` (texto secundario)
- **Fondo Claro:** `#F5F5F5`
- **Blanco:** `#FFFFFF`
- **Rojo Claro:** `#FFEBEE` (backgrounds sutiles)

### Logo
- Isotipo: Rayo estilizado "EA" en rojo sobre fondo blanco/gris claro
- Logotipo: "ELECTRO" + isotipo + "AMERICA" en negro

---

## Contexto del Sistema

Sistema de Gestión Integral para empresa de construcción e ingeniería eléctrica que ejecuta obras públicas y privadas. Controla:

- Proyectos/obras con etapas, avance, imágenes y documentación
- Stock de materiales con asignación por proyecto
- Equipos, maquinaria y camiones asignados a cada obra
- Ítems de trabajo por etapa y proyecto
- Costos, precios y recaudación (solo admin/supervisor)
- Gastos operativos
- Portal de clientes
- Reportes semanales (PDF + Excel)
- Gestión de usuarios con roles

**Usuarios:** Administrador, Supervisor, Operarios, Clientes externos
**Acceso:** Web responsive + PWA

---

## Stack Tecnológico

### Backend
- Python 3.11+ / FastAPI 0.104+
- PostgreSQL 15+ / SQLAlchemy 2.0 / Alembic
- Pydantic v2 / JWT (python-jose)
- Celery + Redis
- Cloudinary (imágenes)
- WeasyPrint (PDF) / OpenPyXL (Excel)
- Pytest

### Frontend
- React 18 + TypeScript + Vite
- Tailwind CSS + shadcn/ui
- Zustand / TanStack Query / React Hook Form + Zod
- TanStack Table / React Router v6
- Axios / Recharts

### Infraestructura
- Docker + Docker Compose
- Nginx (producción)
- VPS deploy

---

## Módulos del Sistema

1. **Proyectos y Avance** - Ciclo de vida completo de obras
2. **Etapas e Ítems** - Desglose interno y seguimiento
3. **Reportes** - PDF/Excel semanales y personalizados
4. **Stock de Materiales** - Inventario y asignación
5. **Equipos y Maquinaria** - ABM y asignación
6. **Finanzas** - Costos, precios, recaudación (admin only)
7. **Gastos Operativos** - Egresos por proyecto/empresa
8. **Portal Cliente** - Vista restringida por cliente
9. **Usuarios y Roles** - ABM con permisos
10. **Dashboard** - Vista general operativa

---

## Roles y Permisos

| Rol | Acceso |
|-----|--------|
| **Administrador** | Total, incluyendo finanzas y ABM usuarios |
| **Supervisor** | Todo excepto ABM usuarios |
| **Operario** | Avances, fotos, gastos, materiales. NO finanzas |
| **Cliente** | Solo portal con SUS proyectos |

---

## Fases de Desarrollo

| Fase | Módulos |
|------|---------|
| **Fase 1** | Setup: Monorepo, Docker, PostgreSQL, FastAPI, React+Vite |
| **Fase 2** | Auth: Usuario, roles, JWT, login, layouts |
| **Fase 3** | Proyectos: CRUD, etapas, ítems, fotos, avance |
| **Fase 4** | Inventario: Stock, equipos, asignaciones |
| **Fase 5** | Finanzas: Gastos, precios, costos, rentabilidad |
| **Fase 6** | Portal: Vista cliente restringida |
| **Fase 7** | Reportes: PDF/Excel, Celery automático |
| **Fase 8** | Dashboard: Widgets, alertas, gráficos |

---

## Estructura del Monorepo

```
electro-america-system/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── services/
│       ├── stores/
│       ├── types/
│       └── utils/
├── backend/
│   └── app/
│       ├── api/v1/endpoints/
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       └── tasks/
├── docs/
├── docker-compose.yml
└── .env.example
```

---

## Agentes Especializados

El desarrollo está organizado por **subagentes especializados** ubicados en `.claude/agents/`:

- `backend-setup.md` — Configuración inicial backend
- `frontend-setup.md` — Configuración inicial frontend
- `auth-agent.md` — Autenticación y autorización
- `proyectos-agent.md` — Módulo proyectos/etapas
- `materiales-agent.md` — Stock y materiales
- `equipos-agent.md` — Equipos y maquinaria
- `finanzas-agent.md` — Costos y recaudación
- `gastos-agent.md` — Gastos operativos
- `portal-agent.md` — Portal del cliente
- `reportes-agent.md` — Generación de reportes
- `dashboard-agent.md` — Dashboard principal

---

## Comandos Disponibles

Los slash commands están en `.claude/commands/`:

- `/setup` — Inicializar proyecto completo
- `/backend` — Operaciones backend
- `/frontend` — Operaciones frontend
- `/db` — Operaciones de base de datos
- `/test` — Ejecutar tests
- `/deploy` — Preparar deploy

---

## Principios de Desarrollo

### Backend
- Capas: Endpoints → Services → Models
- Validación Pydantic v2 en todos los endpoints
- Soft deletes (campo `activo`)
- Transacciones para operaciones críticas

### Frontend
- Componentes pequeños y reutilizables
- TypeScript estricto (prohibido `any`)
- Loading states y error handling
- Layouts separados: admin vs cliente

### Seguridad
- Validación de permisos en TODOS los endpoints
- Cliente solo accede a `/portal/*` y sus proyectos
- Finanzas solo para admin/supervisor
- Passwords con bcrypt
- JWT con expiración

---

## Convenciones

### Python
```python
# Nombres en español
def obtener_proyectos_por_cliente(cliente_id: UUID) -> List[ProyectoSchema]:
    pass

# Type hints SIEMPRE
# Docstrings para funciones públicas
```

### TypeScript
```typescript
// Interfaces descriptivas
interface EtapaFormData {
  proyectoId: string;
  nombre: string;
}

// Formateo argentino
const formatearMonto = (monto: number): string => {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(monto);
};
```

---

## Variables de Entorno

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/electro_america
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379/0
CLOUDINARY_CLOUD_NAME=your-cloud
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Para Empezar

1. Usar `/setup` para inicializar el proyecto
2. Seguir las fases en orden
3. Cada módulo tiene su agente especializado
4. Consultar `inicial.md` para especificaciones completas

---

*Sistema Electro América — Gestión Integral de Obras*
