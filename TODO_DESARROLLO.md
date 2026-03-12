# TODO - Desarrollo Pendiente

## SPRINT 1: Funcionalidades Core Faltantes

### 1.1 Línea de Tiempo Visual (Timeline)
- [ ] Crear componente `frontend/src/components/ui/timeline.tsx`
- [ ] Integrar en `ProyectoDetalle.tsx` - Tab "Avance"
- [ ] Mostrar etapas con fechas, estados y progreso
- [ ] Marcar hitos importantes
- [ ] Responsive para mobile

### 1.2 Sistema de Alertas
- [ ] Crear modelo `backend/app/models/alerta.py`
  - tipo: stock_minimo | demora_etapa | etapa_pendiente | limite_credito
  - referencia_id, referencia_tipo
  - mensaje, fecha, leida, usuario_id
- [ ] Crear migración para tabla alertas
- [ ] Crear `backend/app/services/alertas_service.py`
  - verificar_stock_minimo()
  - verificar_demoras_etapas()
  - verificar_limites_credito()
- [ ] Crear endpoint `backend/app/api/v1/endpoints/alertas.py`
- [ ] Crear componente `frontend/src/components/AlertasDropdown.tsx`
- [ ] Integrar en MainLayout.tsx (campana de notificaciones)
- [ ] Crear tarea Celery para verificación periódica

### 1.3 Sub-etapas
- [ ] Agregar campo `etapa_padre_id` en modelo Etapa
- [ ] Crear migración
- [ ] Actualizar schemas y endpoints
- [ ] Actualizar UI para mostrar jerarquía
- [ ] Permitir crear sub-etapas desde UI

### 1.4 Ítems de Trabajo Mejorados
- [ ] Agregar campos al modelo ItemTrabajo:
  - responsable_id (FK a usuarios)
  - fecha_estimada_inicio
  - fecha_estimada_fin
  - fecha_real_inicio
  - fecha_real_fin
- [ ] Crear migración
- [ ] Actualizar UI en ProyectoDetalle
- [ ] Agregar selector de responsable
- [ ] Agregar calendario de fechas

---

## SPRINT 2: Reportes Completos

### 2.1 Página de Reportes
- [ ] Crear `frontend/src/pages/Reportes.tsx`
- [ ] Agregar ruta en App.tsx
- [ ] Agregar en navegación MainLayout.tsx
- [ ] Funcionalidades:
  - Filtros: proyecto, fechas, tipo
  - Lista de reportes generados
  - Botón generar nuevo reporte
  - Preview de reporte
  - Descargar PDF/Excel
  - Compartir con cliente

### 2.2 Generación de PDF
- [ ] Instalar `weasyprint` o `reportlab` en backend
- [ ] Crear `backend/app/services/pdf_service.py`
- [ ] Diseñar template HTML para reporte
- [ ] Incluir: logo, datos proyecto, etapas, materiales, equipos, fotos, costos
- [ ] Endpoint para generar PDF

### 2.3 Generación de Excel
- [ ] Instalar `openpyxl` en backend
- [ ] Crear `backend/app/services/excel_service.py`
- [ ] Hojas: Resumen, Etapas, Materiales, Equipos, Gastos
- [ ] Endpoint para generar Excel

### 2.4 Reportes Automáticos Semanales
- [ ] Crear tarea Celery `backend/app/tasks/reportes_task.py`
- [ ] Configurar schedule semanal (lunes)
- [ ] Generar reporte de todos los proyectos activos
- [ ] Guardar en storage (Cloudinary o S3)
- [ ] Marcar como disponible para cliente

### 2.5 Reportes en Portal Cliente
- [ ] Crear `frontend/src/pages/portal/MisReportes.tsx`
- [ ] Listar reportes compartidos
- [ ] Permitir descarga de PDF/Excel

---

## SPRINT 3: Control de Stock Avanzado

### 3.1 Historial de Movimientos UI
- [ ] Agregar tab "Historial" en página Materiales
- [ ] Tabla con movimientos: fecha, tipo, cantidad, proyecto, usuario
- [ ] Filtros por fecha y tipo
- [ ] Paginación

### 3.2 Dashboard de Stock Crítico
- [ ] Widget en Dashboard principal
- [ ] Lista de materiales bajo stock mínimo
- [ ] Color rojo/amarillo según criticidad
- [ ] Link rápido a cada material

### 3.3 Ajustes de Inventario
- [ ] Modal para ajuste manual
- [ ] Tipos: inventario físico, merma, devolución
- [ ] Registro con motivo y usuario
- [ ] Recalcular stock automáticamente

---

## SPRINT 4: Costos y Precios

### 4.1 Precios de Equipos
- [ ] Agregar campos en modelo Equipo:
  - costo_por_hora
  - costo_por_dia
  - costo_mantenimiento_mensual
- [ ] Crear migración
- [ ] Actualizar UI de Equipos
- [ ] Calcular costo de uso en asignaciones

### 4.2 Mano de Obra
- [ ] Crear modelo `backend/app/models/jornada.py`
  - usuario_id, proyecto_id, etapa_id
  - fecha, horas_trabajadas
  - costo_hora (según rol o manual)
- [ ] Crear migración
- [ ] Crear endpoints
- [ ] Crear UI para cargar jornadas
- [ ] Incluir en costos de proyecto

### 4.3 Historial de Precios
- [ ] Crear modelo `backend/app/models/historial_precio.py`
  - tabla_referencia, referencia_id
  - campo_modificado, valor_anterior, valor_nuevo
  - fecha, usuario_id
- [ ] Trigger o service para guardar cambios
- [ ] UI para ver historial

### 4.4 UI de Gestión de Precios
- [ ] Sección en Finanzas o página dedicada
- [ ] Lista de ítems con precios actuales
- [ ] Edición inline o modal
- [ ] Importar/exportar precios Excel

---

## SPRINT 5: Mejoras Varias

### 5.1 Upload de Comprobantes
- [ ] Agregar botón upload en formulario de gasto
- [ ] Integrar con Cloudinary
- [ ] Mostrar thumbnail del comprobante
- [ ] Permitir ver/descargar

### 5.2 Auditoría de Usuarios
- [ ] Crear modelo `backend/app/models/audit_log.py`
  - usuario_id, accion, tabla, registro_id
  - datos_anteriores (JSON), datos_nuevos (JSON)
  - ip, user_agent, fecha
- [ ] Middleware o decorador para logging
- [ ] Página de visualización (solo admin)
- [ ] Filtros por usuario, fecha, acción

### 5.3 Asignación de Equipos a Etapas
- [ ] Agregar campo opcional etapa_id en AsignacionEquipo
- [ ] Actualizar endpoints y schemas
- [ ] Actualizar UI

### 5.4 Notificaciones Email
- [ ] Configurar servicio de email (SendGrid/SES)
- [ ] Crear templates de email
- [ ] Notificar: nuevo reporte, alerta crítica, proyecto completado
- [ ] Preferencias de notificación por usuario

---

## ARCHIVOS A CREAR (RESUMEN)

### Backend - Modelos
- `backend/app/models/alerta.py`
- `backend/app/models/jornada.py`
- `backend/app/models/historial_precio.py`
- `backend/app/models/audit_log.py`

### Backend - Services
- `backend/app/services/alertas_service.py`
- `backend/app/services/pdf_service.py`
- `backend/app/services/excel_service.py`
- `backend/app/services/email_service.py`
- `backend/app/services/audit_service.py`

### Backend - Endpoints
- `backend/app/api/v1/endpoints/alertas.py`
- `backend/app/api/v1/endpoints/jornadas.py`

### Backend - Tasks
- `backend/app/tasks/reportes_task.py`
- `backend/app/tasks/alertas_task.py`

### Frontend - Pages
- `frontend/src/pages/Reportes.tsx`
- `frontend/src/pages/portal/MisReportes.tsx`
- `frontend/src/pages/AuditLog.tsx`

### Frontend - Components
- `frontend/src/components/ui/timeline.tsx`
- `frontend/src/components/AlertasDropdown.tsx`
- `frontend/src/components/UploadComprobante.tsx`

---

## MIGRACIONES PENDIENTES

1. `005_add_alertas.py` - Tabla alertas
2. `006_add_subetapas.py` - Campo etapa_padre_id
3. `007_add_items_fechas.py` - Campos de fecha en items_trabajo
4. `008_add_jornadas.py` - Tabla jornadas
5. `009_add_equipos_costos.py` - Campos de costo en equipos
6. `010_add_historial_precios.py` - Tabla historial_precio
7. `011_add_audit_log.py` - Tabla audit_log
8. `012_add_asignacion_etapa.py` - Campo etapa_id en asignaciones_equipo

---

## DEPENDENCIAS A INSTALAR

### Backend (requirements.txt)
```
weasyprint  # Para PDF
openpyxl    # Para Excel
```

### Frontend (package.json)
```
# Ya tiene todo lo necesario
```
