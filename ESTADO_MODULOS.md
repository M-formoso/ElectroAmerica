# Estado de Módulos - Sistema Electro América

**Última actualización:** 2026-03-12

---

## RESUMEN EJECUTIVO

| Módulo | Estado Backend | Estado Frontend | Completitud |
|--------|---------------|-----------------|-------------|
| 1. Gestión de Proyectos | Parcial | Parcial | 60% |
| 2. Reportes de Proyecto | Parcial | NO | 20% |
| 3. Control de Stock | Parcial | Básico | 40% |
| 4. Control de Equipos | OK | OK | 80% |
| 5. Costos y Precios | Parcial | Parcial | 50% |
| 6. Gastos Operativos | OK | Básico | 60% |
| 7. Portal de Clientes | OK | OK | 80% |
| 8. Usuarios y Permisos | OK | OK | 90% |
| 9. Clientes | OK | OK | 85% |
| 10. Finanzas | OK | Parcial | 70% |

---

## 1. GESTIÓN DE PROYECTOS Y AVANCE DE OBRAS

### Implementado ✅
- [x] Alta, edición de proyectos
- [x] Registro de etapas con estado (pendiente, en_progreso, completada, pausada)
- [x] Carga de porcentaje de avance por etapa
- [x] Subida de fotos por etapa y por proyecto
- [x] Ítems de trabajo por etapa (modelo existe)
- [x] Asignación de materiales a etapas

### Falta Implementar ❌
- [ ] **Sub-etapas** - No hay modelo ni UI para sub-etapas
- [ ] **Responsable por ítem vinculado a usuario** - Tiene campo `responsable` como texto, falta FK a usuarios
- [ ] **Fecha estimada por ítem** - No tiene fecha_estimada en ItemTrabajo
- [ ] **Línea de tiempo visual** - No hay componente Timeline en frontend
- [ ] **Alertas por demoras** - No hay sistema de alertas/notificaciones
- [ ] **Alertas por etapas pendientes** - No hay lógica de alertas
- [ ] **UI completa para gestión de ítems de trabajo** - Básica

### Archivos a modificar:
- `backend/app/models/item_trabajo.py` - Agregar responsable_id, fecha_estimada
- `backend/app/models/etapa.py` - Agregar soporte para sub-etapas (etapa_padre_id)
- `frontend/src/pages/ProyectoDetalle.tsx` - Agregar Timeline visual
- `frontend/src/components/Timeline.tsx` - CREAR componente
- `backend/app/services/alertas_service.py` - CREAR servicio de alertas

---

## 2. REPORTES DE PROYECTO (Semanales y Personalizados)

### Implementado ✅
- [x] Modelo Reporte existe en backend
- [x] Endpoint para generar reportes básicos
- [x] Service `reportes.ts` en frontend

### Falta Implementar ❌
- [ ] **Generación automática semanal** - No hay tarea programada (Celery task)
- [ ] **Reportes personalizados por rango de fechas** - Falta UI
- [ ] **Reportes por etapa** - Falta filtro
- [ ] **Reportes por tipo de recurso** - Falta filtro
- [ ] **Inclusión de materiales utilizados** - Parcial
- [ ] **Inclusión de equipos afectados** - Falta
- [ ] **Inclusión de ítems ejecutados** - Falta
- [ ] **Inclusión de horas de personal** - No hay modelo de horas/jornadas
- [ ] **Inclusión de fotos del período** - Falta
- [ ] **Exportación PDF** - No implementado
- [ ] **Exportación Excel** - No implementado
- [ ] **Compartir reporte con cliente** - Falta funcionalidad
- [ ] **Página de Reportes en frontend** - NO EXISTE

### Archivos a crear:
- `frontend/src/pages/Reportes.tsx` - Página completa de reportes
- `backend/app/tasks/reportes_task.py` - Tarea Celery para reportes semanales
- `backend/app/services/pdf_service.py` - Generación de PDF
- `backend/app/services/excel_service.py` - Generación de Excel

---

## 3. CONTROL DE STOCK DE MATERIALES

### Implementado ✅
- [x] Modelo Material con stock_actual, stock_minimo
- [x] Modelo MovimientoStock para historial
- [x] Asignación de materiales a proyectos/etapas
- [x] Descuento automático de stock al asignar
- [x] Endpoint para movimientos de stock
- [x] Página Materiales.tsx básica

### Falta Implementar ❌
- [ ] **Alertas automáticas por stock mínimo** - No hay sistema de alertas
- [ ] **Historial de movimientos visible en UI** - Falta tab/sección en frontend
- [ ] **Vinculación de materiales con costos** - Parcial (falta mostrar costo total por proyecto)
- [ ] **Dashboard de stock crítico** - Falta
- [ ] **Ajustes de inventario** - Falta UI para ajustes manuales

### Archivos a modificar:
- `frontend/src/pages/Materiales.tsx` - Agregar tab de movimientos/historial
- `frontend/src/pages/Dashboard.tsx` - Agregar widget de stock crítico
- `backend/app/services/alertas_service.py` - Alertas de stock mínimo

---

## 4. CONTROL DE EQUIPOS, CAMIONES Y RECURSOS

### Implementado ✅
- [x] ABM de equipos (herramienta, vehiculo, maquinaria, otro)
- [x] Estados: disponible, asignado, mantenimiento, fuera_servicio
- [x] Asignación de equipos a proyectos
- [x] Registro de fechas de asignación/devolución
- [x] Historial de uso por equipo (endpoint existe)
- [x] Página Equipos.tsx funcional

### Falta Implementar ❌
- [ ] **Asignación a etapas específicas** - Solo se asigna a proyecto, no a etapa
- [ ] **Visible en reportes del proyecto** - Falta incluir en reportes
- [ ] **Costo por uso de equipo** - No hay cálculo de costo/hora o costo/día
- [ ] **Mantenimiento programado** - No hay calendario de mantenimiento

### Archivos a modificar:
- `backend/app/models/asignacion_equipo.py` - Agregar etapa_id opcional
- `backend/app/schemas/equipo.py` - Agregar campos de costo
- `frontend/src/pages/Equipos.tsx` - Agregar historial visual, costos

---

## 5. MÓDULO DE COSTOS Y PRECIOS (Administrador)

### Implementado ✅
- [x] Modelo PrecioItem para precios de ítems
- [x] Endpoint para cargar precios
- [x] Cálculo de costo por proyecto (en finanzas_service)
- [x] Rentabilidad básica por proyecto

### Falta Implementar ❌
- [ ] **Precios de materiales** - Solo hay costo_unitario en Material, falta precio de venta
- [ ] **Precios de equipos (costo/hora)** - No existe
- [ ] **Precios de mano de obra** - No hay modelo de mano de obra
- [ ] **Historial de modificaciones de precios** - No hay auditoría de precios
- [ ] **Cálculo automático de costo por etapa** - Parcial
- [ ] **UI completa para gestión de precios** - Falta sección dedicada
- [ ] **Lo recaudado vs invertido visual** - Falta gráficos comparativos

### Archivos a crear:
- `frontend/src/pages/Precios.tsx` - Gestión de precios (o sección en Finanzas)
- `backend/app/models/historial_precio.py` - Auditoría de cambios de precio
- `backend/app/models/mano_obra.py` - Modelo para costos de personal

---

## 6. MÓDULO DE GASTOS OPERATIVOS

### Implementado ✅
- [x] Modelo Gasto con categorías
- [x] Modelo CategoriaGasto configurable
- [x] Asociación de gasto a proyecto
- [x] Endpoint CRUD de gastos
- [x] Registro de gastos en ProyectoDetalle

### Falta Implementar ❌
- [ ] **Gastos de empresa general (sin proyecto)** - Falta UI clara
- [ ] **Adjuntar comprobante/foto de factura** - Modelo tiene comprobante_url pero falta UI de upload
- [ ] **Reportes de egresos por período** - Falta UI específica
- [ ] **Reportes de egresos por proyecto** - Integrado en Finanzas pero básico
- [ ] **Página dedicada de Gastos** - Se eliminó, ahora está en Finanzas

### Archivos a modificar:
- `frontend/src/pages/Finanzas.tsx` - Agregar upload de comprobantes
- `backend/app/api/v1/endpoints/gastos.py` - Endpoint para upload de comprobante

---

## 7. PORTAL DE CLIENTES

### Implementado ✅
- [x] Acceso con usuario/contraseña propio (rol cliente)
- [x] Cada cliente ve solo sus proyectos
- [x] Vista de estado de avance y etapas
- [x] Vista de porcentaje completado
- [x] Vista de fotos (las marcadas como visible_cliente)
- [x] Diseño simple e intuitivo
- [x] Páginas: MisProyectos.tsx, DetalleProyecto.tsx en /portal

### Falta Implementar ❌
- [ ] **Acceso al reporte semanal** - Falta sección de reportes en portal
- [ ] **Descarga de reportes PDF** - Falta
- [ ] **Notificaciones por email** - No hay sistema de emails

### Archivos a crear:
- `frontend/src/pages/portal/Reportes.tsx` - Reportes para clientes
- `backend/app/services/email_service.py` - Envío de notificaciones

---

## 8. GESTIÓN DE USUARIOS, ROLES Y PERMISOS

### Implementado ✅
- [x] ABM completo de usuarios
- [x] Roles: administrador, supervisor, operario, cliente
- [x] Control de acceso por módulo según rol
- [x] Solo admin/supervisor accede a precios y costos
- [x] Clientes solo ven sus proyectos
- [x] Página Usuarios.tsx funcional

### Falta Implementar ❌
- [ ] **Registro de actividad por usuario** - No hay audit log
- [ ] **Ver quién hizo qué y cuándo** - Falta sistema de auditoría

### Archivos a crear:
- `backend/app/models/audit_log.py` - Modelo de auditoría
- `backend/app/services/audit_service.py` - Servicio de logging
- `frontend/src/pages/AuditLog.tsx` - Visualización de actividad

---

## 9. GESTIÓN DE CLIENTES

### Implementado ✅
- [x] ABM de clientes (particular, empresa, gobierno, etc.)
- [x] Datos fiscales (CUIT, condición IVA)
- [x] Datos de contacto
- [x] Cuenta corriente y saldo
- [x] Límite de crédito
- [x] Usuario vinculado para portal
- [x] Página Clientes.tsx completa

### Falta Implementar ❌
- [ ] **Historial de pagos visual** - Falta UI en detalle de cliente
- [ ] **Resumen de proyectos por cliente** - Parcial

---

## 10. FINANZAS (Módulo Nuevo)

### Implementado ✅
- [x] Transacciones (ingresos/egresos)
- [x] Cuentas (caja, banco, mercado_pago)
- [x] Clientes/Proveedores financieros
- [x] Presupuestos
- [x] Dashboard financiero
- [x] Balance general
- [x] Flujo de caja
- [x] Página Finanzas.tsx

### Falta Implementar ❌
- [ ] **Facturación** - No hay modelo de facturas
- [ ] **Integración con AFIP** - No existe
- [ ] **Conciliación bancaria** - No existe

---

## PRIORIDADES DE DESARROLLO

### Alta Prioridad (Funcionalidad Core)
1. **Línea de tiempo visual** - ProyectoDetalle
2. **Sistema de alertas** - Stock mínimo, demoras, pendientes
3. **Reportes completos** - Con PDF/Excel
4. **Sub-etapas** - Modelo y UI
5. **Historial de movimientos de stock** - UI en Materiales

### Media Prioridad (Mejoras Importantes)
6. **Responsable por ítem de trabajo**
7. **Costo por uso de equipo**
8. **Upload de comprobantes de gastos**
9. **Auditoría de actividad de usuarios**
10. **Precios y costos de mano de obra**

### Baja Prioridad (Nice to Have)
11. Notificaciones por email
12. Mantenimiento programado de equipos
13. Integración AFIP
14. App móvil

---

## SIGUIENTE PASO RECOMENDADO

Comenzar por implementar:
1. **Línea de tiempo visual en ProyectoDetalle** - Impacto visual alto
2. **Sistema de alertas** - Funcionalidad crítica para gestión
3. **Página de Reportes completa** - Funcionalidad core solicitada
