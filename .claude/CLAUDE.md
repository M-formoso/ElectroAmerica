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
11. **Jornadas de Operarios** - Control de jornadas con vehículos, zonas y materiales
12. **Actividades Tipo** - Catálogo de actividades con materiales predefinidos
13. **Alertas Inteligentes** - Materiales pendientes, tareas urgentes, stock bajo

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
- `jornadas-agent.md` — Jornadas de operarios y asignaciones
- `actividades-tipo-agent.md` — Catálogo de actividades con materiales

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

## Módulo: Jornadas de Operarios (NUEVO)

### Descripción
Sistema de control de jornadas laborales donde el operario al iniciar su día debe registrar:
- En qué vehículo/camión viaja
- A qué proyecto/obra se dirige
- Qué materiales lleva del depósito

### Flujo Completo

```
NOCHE ANTERIOR (Supervisor)
├── Planifica tareas del día siguiente
├── Asigna operarios a proyectos/zonas
├── Define materiales necesarios por tarea
└── Asigna vehículos
        │
        ▼
MAÑANA (Operario)
├── Abre app → Pantalla "Iniciar Jornada"
├── Selecciona vehículo asignado
├── Confirma proyecto/zona destino
├── Revisa lista de materiales a cargar
├── Confirma materiales cargados
└── Inicia jornada → Estado: EN_CAMINO
        │
        ▼
DURANTE EL DÍA (En obra)
├── Marca llegada → Estado: EN_OBRA
├── Registra avance de tareas
├── Sube fotos de progreso
├── Reporta novedades/faltantes
└── Puede solicitar materiales adicionales
        │
        ▼
FIN DE DÍA (Cierre)
├── Inicia cierre de jornada
├── Registra km final del vehículo
├── Rinde materiales (consumidos/sobrantes)
├── Indica destino de sobrantes (depósito/obra)
└── Finaliza → Sistema actualiza stock
```

### Modelos de Datos

**JornadaOperario**
- id, operario_id, fecha
- vehiculo_id (FK a Equipo tipo vehículo)
- proyecto_id, etapa_id (destino)
- km_inicial, km_final
- hora_inicio, hora_fin
- estado: PLANIFICADA | INICIADA | EN_CAMINO | EN_OBRA | FINALIZADA
- observaciones

**MaterialJornada**
- id, jornada_id, material_id
- cantidad_asignada (lo que debía llevar)
- cantidad_cargada (lo que confirmó)
- cantidad_consumida (lo que usó)
- cantidad_devuelta (sobrante)
- destino_devolucion: DEPOSITO | OBRA
- estado: ASIGNADO | CARGADO | EN_USO | CONSUMIDO | DEVUELTO

**AsignacionDiaria**
- id, fecha, operario_id
- proyecto_id, etapa_id, vehiculo_id
- estado: PLANIFICADA | CONFIRMADA | EN_CURSO | COMPLETADA
- creado_por_id (supervisor)

**ActividadTipo**
- id, codigo, nombre, descripcion
- categoria (instalacion, tendido, montaje, etc.)
- activo

**MaterialActividadTipo**
- id, actividad_tipo_id, material_id
- cantidad_por_unidad
- es_opcional
- notas

### Estados de Jornada

| Estado | Descripción | Quién lo activa |
|--------|-------------|-----------------|
| PLANIFICADA | Supervisor asignó al operario | Supervisor |
| INICIADA | Operario confirmó inicio | Operario |
| EN_CAMINO | Salió hacia la obra | Operario |
| EN_OBRA | Llegó y está trabajando | Operario |
| FINALIZADA | Cerró jornada y rindió materiales | Operario |

### Alertas del Módulo

**Para Operarios:**
- "Tenés materiales pendientes de retirar para mañana"
- "No olvidés cerrar tu jornada"
- "Tenés tareas urgentes asignadas"

**Para Supervisores:**
- "Juan Pérez inició jornada - Camión 01 - Obra Centro"
- "María García reporta falta de material"
- "3 operarios no cerraron jornada de ayer"
- "Stock bajo de Cable 2.5mm - 5 jornadas lo requieren mañana"

**Para Depósito:**
- "8 pedidos de materiales para mañana"
- "Solicitud urgente de material adicional en obra"

### Endpoints API

```
POST   /jornadas/iniciar              # Operario inicia jornada
PUT    /jornadas/{id}/llegada         # Marca llegada a obra
PUT    /jornadas/{id}/cerrar          # Cierra jornada con rendición
GET    /jornadas/activas              # Jornadas en curso (supervisor)
GET    /jornadas/mi-jornada           # Jornada actual del operario
GET    /jornadas/historial            # Historial con filtros

POST   /asignaciones-diarias          # Supervisor planifica
GET    /asignaciones-diarias/fecha    # Asignaciones de un día
PUT    /asignaciones-diarias/{id}     # Modifica asignación

GET    /actividades-tipo              # Catálogo de actividades
POST   /actividades-tipo              # Crear actividad tipo
GET    /actividades-tipo/{id}/materiales  # Materiales de una actividad
POST   /actividades-tipo/{id}/materiales  # Agregar material a actividad
```

### Pantallas Frontend

**Operario:**
1. `/operario/iniciar-jornada` - Selección de vehículo, destino, materiales
2. `/operario/jornada-activa` - Estado actual, tareas, reportar novedades
3. `/operario/cerrar-jornada` - Rendición de materiales, observaciones

**Supervisor:**
1. `/admin/planificacion-diaria` - Calendario de asignaciones
2. `/admin/monitor-jornadas` - Vista en tiempo real de operarios
3. `/admin/actividades-tipo` - ABM de actividades con materiales

---

## Módulo: Actividades Tipo con Materiales (NUEVO)

### Descripción
Catálogo de actividades estándar que se repiten en las obras. Cada actividad tiene una lista predefinida de materiales necesarios, permitiendo calcular automáticamente qué materiales se necesitan al asignar tareas.

### Ejemplo de Actividad Tipo

**Actividad:** Instalación de tablero monofásico 6 módulos
**Categoría:** Instalación eléctrica
**Materiales:**
- Tablero 6 módulos × 1 unidad
- Disyuntor 20A × 2 unidades
- Cable 2.5mm² × 5 metros
- Bornera × 2 unidades
- Tornillos 6mm × 8 unidades

### Flujo de Cálculo Automático

1. Supervisor crea tarea "Instalar 3 tableros monofásicos"
2. Selecciona actividad tipo "Instalación tablero monofásico"
3. Indica cantidad: 3
4. Sistema calcula automáticamente:
   - Tablero 6 módulos × 3 = 3 unidades
   - Disyuntor 20A × 6 = 6 unidades
   - Cable 2.5mm² × 15 = 15 metros
   - etc.
5. Supervisor puede ajustar cantidades manualmente
6. Sistema verifica stock y genera alertas si falta material

---

## Módulo: Alertas de Materiales Pendientes (MEJORA)

### Tipos de Alerta Nuevos

| Tipo | Prioridad | Descripción |
|------|-----------|-------------|
| MATERIAL_PENDIENTE_RETIRO | ALTA | Material asignado que no fue retirado |
| MATERIAL_FALTANTE_JORNADA | CRITICA | No hay stock para jornadas de mañana |
| TAREA_URGENTE | ALTA/CRITICA | Tarea con prioridad urgente sin asignar |
| JORNADA_SIN_CERRAR | MEDIA | Operario no cerró jornada |
| VEHICULO_SIN_DEVOLVER | ALTA | Vehículo no regresó al depósito |

### Orden de Urgencia para Tareas

Las tareas se ordenan por:
1. **Prioridad:** CRITICA > URGENTE > ALTA > MEDIA > BAJA
2. **Fecha límite:** Más próxima primero
3. **Dependencias:** Si bloquea otras tareas, sube prioridad
4. **Cliente VIP:** Proyectos de clientes prioritarios

---

*Sistema Electro América — Gestión Integral de Obras*
