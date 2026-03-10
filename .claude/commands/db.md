# /db - Operaciones de Base de Datos

Ejecuta operaciones de base de datos PostgreSQL.

## Argumentos:
- `migrate` - Aplicar migraciones pendientes
- `revision` - Crear nueva migración
- `seed` - Cargar datos de prueba
- `reset` - Reiniciar base de datos

## Comandos:

### Aplicar migraciones
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### Crear nueva migración
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "descripción"
```

### Ver historial de migraciones
```bash
cd backend
source venv/bin/activate
alembic history
alembic current
```

### Revertir última migración
```bash
cd backend
source venv/bin/activate
alembic downgrade -1
```

### Reiniciar base de datos (dev)
```bash
docker-compose down -v
docker-compose up -d postgres
sleep 5
cd backend && alembic upgrade head
```

## Esquema de la base de datos:

### Tablas principales:
- `usuarios` - Usuarios del sistema
- `proyectos` - Proyectos/obras
- `etapas` - Etapas de cada proyecto
- `items_trabajo` - Ítems dentro de etapas
- `materiales` - Inventario de materiales
- `movimientos_stock` - Historial de stock
- `asignaciones_material` - Materiales asignados
- `equipos` - Equipos y maquinaria
- `asignaciones_equipo` - Equipos asignados
- `gastos` - Gastos operativos
- `fotos` - Fotos de obras
- `reportes` - Reportes generados

### Soft deletes:
Todas las tablas tienen `activo = Boolean` para soft delete.

---
*Referencia: `.claude/CLAUDE.md` para esquema completo*
