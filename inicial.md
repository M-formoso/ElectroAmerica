# Agent Instructions — Sistema de Gestión de Obras y Construcción

## Contexto del Proyecto

Estás trabajando en un **Sistema de Gestión Integral para una Empresa de Construcción y Servicios de Ingeniería**. La empresa ejecuta obras públicas y privadas y necesita controlar:

- Proyectos/obras con etapas, porcentajes de avance, imágenes y documentación
- Stock de materiales con asignación por proyecto
- Equipos, maquinaria y camiones asignados a cada obra
- Ítems de trabajo por etapa y proyecto
- Costos, precios y recaudación por obra (visible solo para admin/supervisor)
- Gastos operativos (combustible, viáticos, insumos, etc.)
- Portal de clientes: cada cliente ve únicamente sus propios proyectos
- Reportes semanales o personalizados por proyecto (PDF + Excel)
- Gestión de usuarios con roles y permisos diferenciados
- Módulo de geolocalización (rastreo GPS al iniciar actividad, km recorridos) — **cotizado y desarrollado por separado**

**Usuarios del sistema:** administrador, supervisor, operarios, clientes externos
**Acceso:** Web responsive (desktop + mobile) + PWA para geolocalización

---

## Stack Tecnológico

### Backend
- Python 3.11+ con FastAPI 0.104+
- PostgreSQL 15+ como base de datos
- SQLAlchemy 2.0 como ORM
- Alembic para migraciones
- Pydantic v2 para validación
- JWT con python-jose para autenticación
- Celery + Redis para tareas asíncronas (alertas de stock, generación de reportes)
- Cloudinary para almacenamiento de imágenes de obras y etapas
- WeasyPrint para generación de reportes en PDF
- OpenPyXL para exportación a Excel
- Pytest para testing

### Frontend
- React 18 + TypeScript + Vite
- Tailwind CSS + shadcn/ui para componentes
- **Colores:** Azul construcción + naranja acento (`#1565C0`, `#E65100`, `#E3F2FD`)
- Zustand para state management
- TanStack Query (React Query) para data fetching
- React Hook Form + Zod para formularios
- TanStack Table para tablas
- React Router v6
- Axios como cliente HTTP
- Recharts para gráficos de avance y financieros

### Infraestructura
- Monorepo con Docker + Docker Compose
- Nginx como proxy reverso (producción)
- Deploy en VPS (Railway / DigitalOcean)
- Sentry para monitoreo de errores
- GitHub Actions para CI/CD (opcional)

---

## Estructura del Proyecto (Monorepo)

```
construccion-system/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── layout/              # Header, Sidebar, Footer
│   │   │   ├── proyectos/           # Componentes módulo proyectos
│   │   │   ├── etapas/              # Componentes etapas y avance
│   │   │   ├── materiales/          # Componentes stock materiales
│   │   │   ├── equipos/             # Componentes equipos y camiones
│   │   │   ├── gastos/              # Componentes gastos operativos
│   │   │   ├── finanzas/            # Componentes costos y recaudación
│   │   │   ├── reportes/            # Componentes reportes
│   │   │   └── shared/              # Componentes compartidos
│   │   ├── pages/
│   │   │   ├── auth/                # Login (admin + cliente)
│   │   │   ├── dashboard/           # Dashboard principal
│   │   │   ├── proyectos/           # CRUD proyectos y detalle
│   │   │   ├── materiales/          # Stock y movimientos
│   │   │   ├── equipos/             # ABM equipos y camiones
│   │   │   ├── gastos/              # Registro de gastos operativos
│   │   │   ├── finanzas/            # Costos, precios y recaudación
│   │   │   ├── reportes/            # Generación y descarga
│   │   │   ├── usuarios/            # ABM de usuarios y roles
│   │   │   └── portal-cliente/      # Vista del cliente (solo sus obras)
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── types/
│   │   └── utils/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py
│   │   │       │   ├── proyectos.py
│   │   │       │   ├── etapas.py
│   │   │       │   ├── items_trabajo.py
│   │   │       │   ├── materiales.py
│   │   │       │   ├── equipos.py
│   │   │       │   ├── gastos.py
│   │   │       │   ├── finanzas.py
│   │   │       │   ├── reportes.py
│   │   │       │   ├── usuarios.py
│   │   │       │   ├── fotos.py
│   │   │       │   └── dashboard.py
│   │   │       └── api.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── deps.py
│   │   │   └── celery_app.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── init_db.py
│   │   ├── models/
│   │   │   ├── usuario.py
│   │   │   ├── proyecto.py
│   │   │   ├── etapa.py
│   │   │   ├── item_trabajo.py
│   │   │   ├── material.py
│   │   │   ├── movimiento_stock.py
│   │   │   ├── equipo.py
│   │   │   ├── asignacion_equipo.py
│   │   │   ├── gasto.py
│   │   │   ├── precio_item.py
│   │   │   └── foto.py
│   │   ├── schemas/
│   │   ├── services/
│   │   └── tasks/
│   │       ├── reportes.py          # Generación async de PDFs
│   │       └── alertas.py           # Alertas de stock bajo
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docs/
│   └── agent.md                     # Este archivo
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Módulos del Sistema

### Módulo 1 — Gestión de Proyectos y Avance de Obras

**Descripción:** Control completo del ciclo de vida de cada proyecto/obra.

**Funcionalidades:**
- CRUD completo de proyectos
- Datos del proyecto: nombre, descripción, cliente asignado, ubicación, fecha de inicio, fecha estimada de fin
- Estado general: en planificación, en ejecución, pausado, finalizado
- Porcentaje de avance global (calculado automáticamente desde etapas)
- Galería de imágenes y documentación fotográfica por proyecto
- Línea de tiempo visual del avance
- Alertas automáticas por etapas demoradas

**Endpoints:**
```
GET    /api/v1/proyectos                      Listar proyectos (filtrable por estado/cliente)
POST   /api/v1/proyectos                      Crear proyecto
GET    /api/v1/proyectos/{id}                 Detalle del proyecto
PUT    /api/v1/proyectos/{id}                 Actualizar proyecto
DELETE /api/v1/proyectos/{id}                 Eliminar proyecto (soft delete)
GET    /api/v1/proyectos/{id}/etapas          Etapas del proyecto
GET    /api/v1/proyectos/{id}/materiales      Materiales asignados
GET    /api/v1/proyectos/{id}/equipos         Equipos/camiones asignados
GET    /api/v1/proyectos/{id}/gastos          Gastos asociados
GET    /api/v1/proyectos/{id}/resumen-costos  Costos y recaudación del proyecto
```

---

### Módulo 2 — Etapas, Ítems de Trabajo y Avance

**Descripción:** Desglose interno de cada proyecto en etapas e ítems ejecutables.

**Funcionalidades:**
- CRUD de etapas por proyecto
- Nombre, descripción, orden, fecha estimada de inicio/fin
- Estado: pendiente, en curso, completada, pausada
- Porcentaje de avance de la etapa (actualizable manualmente o por ítems)
- Fotos y documentación específicas de cada etapa
- Ítems de trabajo dentro de cada etapa: descripción, responsable, cantidad, unidad, estado
- El avance de la etapa impacta automáticamente en el avance global del proyecto

**Endpoints:**
```
GET    /api/v1/etapas                         Listar etapas (filtro por proyecto)
POST   /api/v1/etapas                         Crear etapa
GET    /api/v1/etapas/{id}                    Detalle de etapa
PUT    /api/v1/etapas/{id}                    Actualizar etapa (avance, estado)
DELETE /api/v1/etapas/{id}                    Eliminar etapa
POST   /api/v1/etapas/{id}/fotos              Subir fotos de la etapa
GET    /api/v1/items-trabajo                  Listar ítems (filtro por etapa)
POST   /api/v1/items-trabajo                  Crear ítem de trabajo
PUT    /api/v1/items-trabajo/{id}             Actualizar ítem (completar, editar)
DELETE /api/v1/items-trabajo/{id}             Eliminar ítem
```

---

### Módulo 3 — Reportes de Proyecto (Semanales y Personalizados)

**Descripción:** Generación de informes completos del avance de cada obra.

**Funcionalidades:**
- Reporte automático semanal por proyecto (generado cada lunes por Celery)
- Reporte personalizado por rango de fechas
- Contenido del reporte: resumen de avance por etapa, ítems ejecutados, materiales utilizados en el período, equipos/camiones afectados, fotos del período, gastos registrados
- Exportación a PDF (imprimible, con logo y datos de la empresa)
- Exportación a Excel
- Compartir reporte con el cliente desde el sistema

**Endpoints:**
```
GET    /api/v1/reportes/proyecto/{id}         Generar reporte del proyecto
POST   /api/v1/reportes/proyecto/{id}/pdf     Exportar reporte a PDF
POST   /api/v1/reportes/proyecto/{id}/excel   Exportar reporte a Excel
GET    /api/v1/reportes/semanal/{id}          Reporte semanal del proyecto
POST   /api/v1/reportes/compartir/{id}        Compartir reporte con cliente
```

---

### Módulo 4 — Control de Stock de Materiales

**Descripción:** Inventario de materiales con asignación a proyectos y alertas de stock.

**Funcionalidades:**
- CRUD de materiales (nombre, categoría, unidad, stock actual, stock mínimo, precio unitario)
- Asignación de materiales a proyectos/etapas con descuento automático del stock
- Registro de ingresos de stock (compras con proveedor y costo)
- Historial de movimientos por material (entradas, salidas, ajustes)
- Alerta automática cuando el stock llega al mínimo (Celery task)
- Valor total del inventario (stock × precio costo)
- Los materiales usados aparecen en los reportes del proyecto

**Endpoints:**
```
GET    /api/v1/materiales                     Listar materiales
POST   /api/v1/materiales                     Crear material
GET    /api/v1/materiales/{id}                Detalle del material
PUT    /api/v1/materiales/{id}                Actualizar material
DELETE /api/v1/materiales/{id}                Eliminar (soft delete)
GET    /api/v1/materiales/stock-bajo          Materiales bajo stock mínimo
GET    /api/v1/materiales/{id}/movimientos    Historial de movimientos
POST   /api/v1/materiales/asignar             Asignar material a proyecto/etapa
POST   /api/v1/materiales/ingreso             Registrar compra/ingreso de stock
GET    /api/v1/materiales/valor-total         Valor total del inventario
```

---

### Módulo 5 — Control de Equipos, Maquinaria y Camiones

**Descripción:** ABM de recursos físicos y su asignación a proyectos.

**Funcionalidades:**
- ABM de equipos, maquinaria y vehículos (nombre, tipo, patente/código, estado)
- Tipo: camión, excavadora, compactadora, hormigonera, herramienta, otro
- Estado: disponible, asignado, en mantenimiento, fuera de servicio
- Asignación a proyecto/etapa con fecha de inicio y fin de uso
- Historial de uso por equipo: qué proyectos, qué fechas, cuántos días
- Visualizable en el reporte del proyecto

**Endpoints:**
```
GET    /api/v1/equipos                        Listar equipos
POST   /api/v1/equipos                        Crear equipo
GET    /api/v1/equipos/{id}                   Detalle del equipo
PUT    /api/v1/equipos/{id}                   Actualizar equipo
DELETE /api/v1/equipos/{id}                   Eliminar (soft delete)
POST   /api/v1/equipos/{id}/asignar           Asignar equipo a proyecto
GET    /api/v1/equipos/{id}/historial         Historial de uso del equipo
GET    /api/v1/equipos/disponibles            Equipos disponibles hoy
```

---

### Módulo 6 — Costos, Precios y Recaudación (Admin/Supervisor)

**Descripción:** Control financiero de cada proyecto. Solo visible para administrador y supervisor.

**Funcionalidades:**
- El admin/supervisor carga el precio de cada ítem de trabajo, material utilizado, hora de equipo y mano de obra
- Cálculo automático del costo total por etapa y por proyecto
- Registro del monto contratado/recaudado por proyecto
- Rentabilidad estimada: recaudado − costo total
- Historial de modificaciones de precios
- Los operarios y clientes NO tienen acceso a este módulo

**Endpoints:**
```
GET    /api/v1/finanzas/proyecto/{id}         Resumen financiero del proyecto
POST   /api/v1/finanzas/precio-item           Cargar/actualizar precio de ítem
GET    /api/v1/finanzas/rentabilidad          Rentabilidad por proyecto
PUT    /api/v1/finanzas/proyecto/{id}/monto   Actualizar monto contratado
GET    /api/v1/finanzas/resumen-general       Resumen financiero de todos los proyectos
```

---

### Módulo 7 — Gastos Operativos

**Descripción:** Registro de egresos del día a día de la empresa y de cada obra.

**Funcionalidades:**
- Registro de gastos: combustible, viáticos, herramientas, servicios, materiales menores, etc.
- Categorías de gasto configurables
- Asociación de cada gasto a un proyecto específico o a la empresa en general
- Fecha, descripción, monto, responsable
- Adjuntar foto del comprobante/factura
- Reportes de egresos por período, por proyecto y por categoría

**Endpoints:**
```
GET    /api/v1/gastos                         Listar gastos (filtrable)
POST   /api/v1/gastos                         Registrar gasto
GET    /api/v1/gastos/{id}                    Detalle del gasto
PUT    /api/v1/gastos/{id}                    Actualizar gasto
DELETE /api/v1/gastos/{id}                    Eliminar gasto
GET    /api/v1/gastos/por-proyecto/{id}       Gastos de un proyecto
GET    /api/v1/gastos/categorias              Listar categorías configurables
POST   /api/v1/gastos/categorias              Crear categoría de gasto
```

---

### Módulo 8 — Portal del Cliente

**Descripción:** Acceso externo restringido para que cada cliente consulte sus obras.

**Funcionalidades:**
- Login con credenciales propias asignadas por el administrador
- El cliente ve ÚNICAMENTE sus proyectos, no los de otros clientes
- Vista del estado y porcentaje de avance de cada obra
- Detalle de etapas completadas y en curso
- Galería de fotos autorizadas por el admin
- Acceso al último reporte semanal generado
- Diseño simple y mobile-friendly para consulta sin asistencia
- El cliente NO ve costos, precios ni información financiera

**Endpoints:**
```
GET    /api/v1/portal/mis-proyectos           Proyectos del cliente autenticado
GET    /api/v1/portal/proyecto/{id}           Detalle de un proyecto del cliente
GET    /api/v1/portal/proyecto/{id}/etapas    Etapas del proyecto
GET    /api/v1/portal/proyecto/{id}/fotos     Fotos autorizadas del proyecto
GET    /api/v1/portal/proyecto/{id}/reporte   Último reporte disponible
```

---

### Módulo 9 — Gestión de Usuarios, Roles y Permisos

**Descripción:** ABM completo de usuarios del sistema con control de acceso por rol.

**Roles:**
- **Administrador:** acceso total, incluyendo costos, precios y recaudación
- **Supervisor:** acceso total excepto ABM de usuarios y configuración del sistema
- **Operario:** puede registrar avances, fotos, gastos y materiales usados. No ve finanzas
- **Cliente:** acceso solo al portal con sus propios proyectos

**Funcionalidades:**
- CRUD completo de usuarios
- Asignación de rol por usuario
- Asignación de proyectos a clientes (define qué ve cada cliente)
- Activar/desactivar usuarios
- Registro de actividad por usuario (log de acciones)
- Historial de acceso al sistema

**Endpoints:**
```
GET    /api/v1/usuarios                       Listar usuarios
POST   /api/v1/usuarios                       Crear usuario
GET    /api/v1/usuarios/{id}                  Detalle del usuario
PUT    /api/v1/usuarios/{id}                  Actualizar usuario
DELETE /api/v1/usuarios/{id}                  Eliminar (soft delete)
PUT    /api/v1/usuarios/{id}/rol              Cambiar rol del usuario
POST   /api/v1/usuarios/{id}/proyectos        Asignar proyectos a cliente
GET    /api/v1/usuarios/{id}/actividad        Log de actividad del usuario
```

---

### Módulo 10 — Dashboard Principal

**Descripción:** Vista general operativa del estado de la empresa.

**Widgets:**
- Proyectos activos y su estado de avance
- Materiales con stock bajo (alertas)
- Equipos asignados vs disponibles hoy
- Gastos del mes vs. mes anterior
- Resumen financiero general (solo admin/supervisor)
- Etapas con demoras o vencidas
- Últimas fotos subidas al sistema

**Endpoints:**
```
GET    /api/v1/dashboard/resumen              Resumen general del día
GET    /api/v1/dashboard/alertas              Alertas activas (stock, demoras)
GET    /api/v1/dashboard/proyectos-activos    Estado de todos los proyectos activos
GET    /api/v1/dashboard/financiero           Resumen financiero (solo admin/supervisor)
```

---

## Esquema de Base de Datos

### `usuarios`
```sql
id              UUID (PK)
email           VARCHAR(255) UNIQUE NOT NULL
password_hash   VARCHAR(255) NOT NULL
nombre          VARCHAR(100) NOT NULL
rol             ENUM ('administrador', 'supervisor', 'operario', 'cliente')
activo          BOOLEAN DEFAULT TRUE
ultimo_acceso   TIMESTAMP
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### `proyectos`
```sql
id                    UUID (PK)
nombre                VARCHAR(255) NOT NULL
descripcion           TEXT
cliente_id            UUID (FK usuarios)       -- usuario con rol cliente
ubicacion             VARCHAR(255)
fecha_inicio          DATE
fecha_fin_estimada    DATE
fecha_fin_real        DATE NULL
estado                ENUM ('planificacion', 'en_ejecucion', 'pausado', 'finalizado')
porcentaje_avance     DECIMAL(5,2)             -- calculado desde etapas
monto_contratado      DECIMAL(12,2) NULL       -- solo visible admin/supervisor
activo                BOOLEAN DEFAULT TRUE
created_by            UUID (FK usuarios)
created_at            TIMESTAMP
updated_at            TIMESTAMP
```

### `etapas`
```sql
id                    UUID (PK)
proyecto_id           UUID (FK proyectos)
nombre                VARCHAR(255) NOT NULL
descripcion           TEXT
orden                 INTEGER
fecha_inicio_est      DATE
fecha_fin_est         DATE
fecha_inicio_real     DATE NULL
fecha_fin_real        DATE NULL
estado                ENUM ('pendiente', 'en_curso', 'completada', 'pausada')
porcentaje_avance     DECIMAL(5,2) DEFAULT 0
created_at            TIMESTAMP
updated_at            TIMESTAMP
```

### `items_trabajo`
```sql
id              UUID (PK)
etapa_id        UUID (FK etapas)
descripcion     VARCHAR(255) NOT NULL
responsable     VARCHAR(100)
cantidad        DECIMAL(10,2)
unidad          VARCHAR(30)
estado          ENUM ('pendiente', 'en_curso', 'completado')
precio_unitario DECIMAL(10,2) NULL    -- solo visible admin/supervisor
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### `materiales`
```sql
id                UUID (PK)
nombre            VARCHAR(255) NOT NULL
categoria         VARCHAR(100)
unidad            VARCHAR(30)
stock_actual      DECIMAL(10,3) NOT NULL
stock_minimo      DECIMAL(10,3) DEFAULT 0
precio_costo      DECIMAL(10,2)
proveedor         VARCHAR(255)
activo            BOOLEAN DEFAULT TRUE
created_at        TIMESTAMP
updated_at        TIMESTAMP
```

### `asignaciones_material`
```sql
id                    UUID (PK)
material_id           UUID (FK materiales)
proyecto_id           UUID (FK proyectos)
etapa_id              UUID (FK etapas) NULL
cantidad              DECIMAL(10,3) NOT NULL
precio_unitario       DECIMAL(10,2)
fecha                 DATE
observaciones         TEXT
created_by            UUID (FK usuarios)
created_at            TIMESTAMP
```

### `movimientos_stock`
```sql
id               UUID (PK)
material_id      UUID (FK materiales)
tipo             ENUM ('ingreso', 'egreso', 'ajuste')
cantidad         DECIMAL(10,3) NOT NULL
referencia_tipo  VARCHAR(50)     -- 'asignacion', 'compra', 'ajuste_manual'
referencia_id    UUID NULL
observaciones    TEXT
usuario_id       UUID (FK usuarios)
created_at       TIMESTAMP
```

### `equipos`
```sql
id              UUID (PK)
nombre          VARCHAR(255) NOT NULL
tipo            ENUM ('camion', 'excavadora', 'compactadora', 'hormigonera', 'herramienta', 'otro')
patente         VARCHAR(20) NULL
codigo_interno  VARCHAR(50) NULL
estado          ENUM ('disponible', 'asignado', 'mantenimiento', 'fuera_servicio')
observaciones   TEXT
activo          BOOLEAN DEFAULT TRUE
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### `asignaciones_equipo`
```sql
id              UUID (PK)
equipo_id       UUID (FK equipos)
proyecto_id     UUID (FK proyectos)
etapa_id        UUID (FK etapas) NULL
fecha_desde     DATE NOT NULL
fecha_hasta     DATE NULL
observaciones   TEXT
created_by      UUID (FK usuarios)
created_at      TIMESTAMP
```

### `gastos`
```sql
id               UUID (PK)
fecha            DATE NOT NULL
categoria        VARCHAR(100)    -- combustible, viaticos, herramientas, servicios, otro
descripcion      TEXT NOT NULL
monto            DECIMAL(10,2) NOT NULL
proyecto_id      UUID (FK proyectos) NULL    -- NULL = gasto general de empresa
responsable_id   UUID (FK usuarios)
comprobante_url  VARCHAR(500) NULL
created_by       UUID (FK usuarios)
created_at       TIMESTAMP
```

### `fotos`
```sql
id                  UUID (PK)
proyecto_id         UUID (FK proyectos)
etapa_id            UUID (FK etapas) NULL
url                 VARCHAR(500)        -- URL en Cloudinary
descripcion         VARCHAR(255)
fecha               DATE
visible_cliente     BOOLEAN DEFAULT FALSE
created_by          UUID (FK usuarios)
created_at          TIMESTAMP
```

### `configuracion`
```sql
id              UUID (PK)
clave           VARCHAR(100) UNIQUE NOT NULL
valor           JSONB NOT NULL
descripcion     TEXT
updated_by      UUID (FK usuarios)
updated_at      TIMESTAMP
```

---

## Principios de Desarrollo

### Arquitectura Backend
- Capas: Endpoints → Services → Models (NUNCA lógica de negocio en endpoints)
- Dependency injection de FastAPI para DB, auth y permisos
- Validación Pydantic v2 en todos los endpoints
- Soft deletes con campo `activo` — nunca eliminar registros operativos
- Transacciones de BD para operaciones críticas (asignación de material → descuento de stock)

### Arquitectura Frontend
- Componentes pequeños y reutilizables
- Custom hooks para lógica compartida
- TypeScript SIEMPRE — prohibido usar `any`
- Loading states y error handling en todas las operaciones
- El portal del cliente y el panel administrativo tienen layouts completamente separados

### Control de Acceso por Rol
- **Administrador:** acceso total
- **Supervisor:** igual que admin excepto ABM de usuarios
- **Operario:** puede operar (registrar avances, fotos, gastos, materiales). NO ve finanzas ni costos
- **Cliente:** solo accede a `/portal/*` y solo ve SUS proyectos
- Validar en CADA endpoint que el cliente no accede a datos de otros proyectos

---

## Flujos Críticos

### Flujo de Registro de Avance de Etapa
1. Operario/supervisor selecciona proyecto → etapa
2. Actualiza porcentaje de avance de la etapa
3. Marca ítems de trabajo como completados
4. Sube fotos del avance (Cloudinary)
5. Sistema recalcula automáticamente el porcentaje global del proyecto
6. Si la etapa tiene demora (fecha estimada vencida y no completada) → alerta en dashboard

### Flujo de Asignación de Materiales a Proyecto
1. Admin/supervisor asigna materiales a un proyecto o etapa con cantidad
2. Sistema valida stock disponible
3. Sistema descuenta automáticamente del stock actual
4. Crea movimiento de stock tipo `egreso` vinculado al proyecto
5. Si el material queda en stock mínimo → alerta automática via Celery
6. El material aparece registrado en el reporte del proyecto

### Flujo de Generación de Reporte
1. Se dispara manualmente (botón) o automáticamente cada lunes (Celery beat)
2. Sistema recopila: etapas del período, ítems completados, materiales usados, equipos asignados, gastos registrados, fotos subidas
3. Genera PDF con WeasyPrint (con logo y datos de la empresa) y Excel con OpenPyXL
4. El reporte queda disponible para descarga en el sistema
5. El admin puede compartirlo con el cliente desde el sistema

### Flujo de Acceso del Cliente al Portal
1. El admin crea el usuario cliente y le asigna los proyectos que puede ver
2. El cliente ingresa con sus credenciales
3. Ve solo sus proyectos asignados — ningún otro dato del sistema
4. Puede ver avance, etapas, fotos autorizadas y último reporte
5. NO ve costos, precios, recaudación ni información de otros clientes

---

## Convenciones de Código

### Python
```python
# Nombres descriptivos en español
def obtener_proyectos_por_cliente(cliente_id: UUID) -> List[ProyectoSchema]:
    pass

# Type hints SIEMPRE
def asignar_material_a_proyecto(
    db: Session,
    proyecto_id: UUID,
    material_id: UUID,
    cantidad: Decimal,
    usuario_id: UUID
) -> AsignacionMaterial:
    pass

# Docstrings para funciones públicas
def actualizar_avance_proyecto(db: Session, proyecto_id: UUID) -> None:
    """
    Recalcula el porcentaje de avance global del proyecto
    en base al promedio ponderado de sus etapas.

    Args:
        db: Sesión de base de datos
        proyecto_id: ID del proyecto a recalcular
    """
    pass
```

### TypeScript
```typescript
// Interfaces descriptivas
interface EtapaFormData {
  proyectoId: string;
  nombre: string;
  descripcion: string;
  orden: number;
  fechaInicioEst: Date;
  fechaFinEst: Date;
}

// Formateo argentino
const formatearMonto = (monto: number): string => {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(monto);
};

const formatearFecha = (fecha: Date): string => {
  return new Intl.DateTimeFormat('es-AR').format(fecha);
};

// Cálculo de avance global
const calcularAvanceProyecto = (etapas: Etapa[]): number => {
  if (!etapas.length) return 0;
  const suma = etapas.reduce((acc, e) => acc + e.porcentajeAvance, 0);
  return Math.round(suma / etapas.length);
};
```

---

## Estructura de Archivos por Módulo

### Backend — al crear nuevo módulo:
```
1. models/{modulo}.py
2. schemas/{modulo}.py
3. services/{modulo}_service.py
4. api/v1/endpoints/{modulo}.py
5. tests/api/test_{modulo}.py
```

### Frontend — por feature:
```
src/
├── components/{modulo}/
│   ├── {Modulo}List.tsx
│   ├── {Modulo}Form.tsx
│   ├── {Modulo}Detail.tsx
│   └── index.ts
├── pages/{modulo}/
│   ├── index.tsx
│   ├── create.tsx
│   └── [id].tsx
├── services/{modulo}Service.ts
└── types/{modulo}.ts
```

---

## Tareas Celery

### Alerta de stock bajo
```python
@shared_task
def alerta_stock_bajo(material_id: str):
    """Notifica a admin y supervisor cuando un material llega al stock mínimo."""
    pass
```

### Reporte semanal automático
```python
@shared_task
def generar_reporte_semanal():
    """Se ejecuta cada lunes. Genera reporte de la semana anterior para cada proyecto activo."""
    pass
```

### Alerta de etapa demorada
```python
@shared_task
def verificar_etapas_demoradas():
    """Se ejecuta diariamente. Detecta etapas cuya fecha estimada venció y no están completadas."""
    pass
```

---

## Seguridad

- ✅ Validación de permisos en TODOS los endpoints
- ✅ El cliente solo accede a `/portal/*` y solo a sus proyectos asignados
- ✅ Costos, precios y recaudación visibles únicamente para admin y supervisor
- ✅ Passwords hasheados con bcrypt
- ✅ JWT con expiración (access: 30min, refresh: 7 días)
- ✅ Soft delete obligatorio — nunca eliminar registros operativos
- ✅ Log de actividad por usuario en operaciones críticas

---

## Variables de Entorno (`.env.example`)

```bash
# Base de datos
DATABASE_URL=postgresql://user:password@localhost:5432/construccion_system

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Celery & Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Cloudinary (fotos de obras y etapas)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email (envío de reportes a clientes)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=sistema@empresa.com
SMTP_PASSWORD=your-app-password

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Comandos Útiles

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Docker
docker-compose up -d
docker-compose logs -f backend
docker-compose exec backend alembic upgrade head

# Tests
pytest
pytest tests/api/test_proyectos.py -v
pytest --cov=app tests/

# Celery
celery -A app.core.celery_app worker --loglevel=info
celery -A app.core.celery_app beat --loglevel=info  # para tareas programadas
```

---

## Fases de Desarrollo

| Fase | Contenido |
|---|---|
| Fase 1 — Setup | Estructura monorepo, Docker Compose, PostgreSQL, FastAPI base, React + Vite |
| Fase 2 — Auth | Modelo Usuario, roles, JWT, login, layouts separados por rol |
| Fase 3 — Proyectos y Etapas | CRUD proyectos, etapas, ítems de trabajo, fotos, cálculo de avance |
| Fase 4 — Materiales y Equipos | Stock, movimientos, alertas, asignación a proyectos, ABM equipos |
| Fase 5 — Gastos y Finanzas | Gastos operativos, precios, costos, recaudación y rentabilidad |
| Fase 6 — Portal Cliente | Vista restringida del cliente a sus proyectos y reportes |
| Fase 7 — Reportes | Generación PDF/Excel, reporte semanal automático (Celery) |
| Fase 8 — Dashboard | Widgets, alertas, gráficos de avance y financieros |

---

**¿Listo para empezar? Indicá qué módulo querés implementar primero y te doy el código completo.**

---

*Desarrollado por Developnet — developnet.com.ar — Villa Gesell, Buenos Aires, Argentina*