import api from './api'

// ============== TIPOS ==============

export type EstadoJornada = 'planificada' | 'iniciada' | 'en_camino' | 'en_obra' | 'finalizada' | 'cancelada'
export type EstadoMaterialJornada = 'asignado' | 'pendiente_retiro' | 'cargado' | 'en_uso' | 'consumido' | 'devuelto_deposito' | 'devuelto_obra'
export type DestinoDevolucion = 'deposito' | 'obra' | 'otro_operario'
export type EstadoAsignacion = 'planificada' | 'confirmada' | 'en_curso' | 'completada' | 'cancelada'

export interface MaterialJornada {
  id: string
  jornada_id: string
  material_id: string
  cantidad_asignada: number
  cantidad_cargada?: number
  cantidad_consumida?: number
  cantidad_devuelta?: number
  estado: EstadoMaterialJornada
  destino_devolucion?: DestinoDevolucion
  notas?: string
  material_codigo?: string
  material_nombre?: string
  material_unidad?: string
}

export interface JornadaOperario {
  id: string
  operario_id: string
  fecha: string
  vehiculo_id?: string
  proyecto_id: string
  etapa_id?: string
  km_inicial?: number
  km_final?: number
  hora_inicio?: string
  hora_llegada_obra?: string
  hora_fin?: string
  horas_trabajadas?: number
  horas_extra?: number
  estado: EstadoJornada
  observaciones_inicio?: string
  observaciones_cierre?: string
  novedades?: string
  asignacion_diaria_id?: string
  created_at: string
  operario_nombre?: string
  vehiculo_nombre?: string
  vehiculo_patente?: string
  proyecto_nombre?: string
  etapa_nombre?: string
  km_recorridos?: number
  duracion_total?: number
  materiales: MaterialJornada[]
}

export interface JornadaOperarioList {
  id: string
  operario_id: string
  operario_nombre?: string
  fecha: string
  vehiculo_patente?: string
  proyecto_nombre?: string
  etapa_nombre?: string
  estado: EstadoJornada
  hora_inicio?: string
  hora_fin?: string
  hora_llegada_obra?: string
  km_recorridos?: number
}

export interface IniciarJornadaRequest {
  vehiculo_id: string
  proyecto_id: string
  etapa_id?: string
  km_inicial?: number
  observaciones?: string
  materiales: MaterialCargar[]
}

export interface MaterialCargar {
  material_id: string
  cantidad_cargada: number
  notas?: string
}

export interface MaterialRendir {
  material_id: string
  cantidad_consumida: number
  cantidad_devuelta?: number
  destino_devolucion?: DestinoDevolucion
  notas?: string
}

export interface CerrarJornadaRequest {
  km_final?: number
  horas_trabajadas?: number
  horas_extra?: number
  observaciones?: string
  materiales: MaterialRendir[]
}

export interface AsignacionDiaria {
  id: string
  fecha: string
  operario_id: string
  proyecto_id: string
  etapa_id?: string
  vehiculo_id?: string
  estado: EstadoAsignacion
  prioridad: string
  notas?: string
  tareas_planificadas?: any[]
  materiales_planificados?: any[]
  creado_por_id: string
  created_at: string
  operario_nombre?: string
  proyecto_nombre?: string
  etapa_nombre?: string
  vehiculo_nombre?: string
  vehiculo_patente?: string
  jornada_id?: string
  jornada_estado?: string
}

export interface EstadisticasJornadasDia {
  fecha: string
  total_operarios: number
  jornadas_planificadas: number
  jornadas_iniciadas: number
  jornadas_en_obra: number
  jornadas_finalizadas: number
}

// ============== SERVICIO ==============

export const jornadasOperarioService = {
  // Obtener jornada activa del operario actual
  async getMiJornadaActiva(): Promise<JornadaOperario | null> {
    const response = await api.get<JornadaOperario | null>('/jornadas-operario/mi-jornada')
    return response.data
  },

  // Iniciar jornada
  async iniciarJornada(data: IniciarJornadaRequest, asignacionId?: string): Promise<JornadaOperario> {
    const params = asignacionId ? { asignacion_id: asignacionId } : {}
    const response = await api.post<JornadaOperario>('/jornadas-operario/iniciar', data, { params })
    return response.data
  },

  // Marcar en camino
  async marcarEnCamino(jornadaId: string): Promise<JornadaOperario> {
    const response = await api.post<JornadaOperario>(`/jornadas-operario/${jornadaId}/en-camino`)
    return response.data
  },

  // Marcar llegada a obra
  async marcarLlegada(jornadaId: string, observaciones?: string): Promise<JornadaOperario> {
    const response = await api.post<JornadaOperario>(`/jornadas-operario/${jornadaId}/llegada`, {
      observaciones,
    })
    return response.data
  },

  // Reportar novedad
  async reportarNovedad(jornadaId: string, novedad: string, esUrgente: boolean = false): Promise<JornadaOperario> {
    const response = await api.post<JornadaOperario>(`/jornadas-operario/${jornadaId}/novedad`, {
      novedad,
      es_urgente: esUrgente,
    })
    return response.data
  },

  // Cerrar jornada
  async cerrarJornada(jornadaId: string, data: CerrarJornadaRequest): Promise<JornadaOperario> {
    const response = await api.post<JornadaOperario>(`/jornadas-operario/${jornadaId}/cerrar`, data)
    return response.data
  },

  // Cancelar jornada (solo supervisor/admin)
  async cancelarJornada(jornadaId: string, motivo: string): Promise<JornadaOperario> {
    const response = await api.post<JornadaOperario>(`/jornadas-operario/${jornadaId}/cancelar`, null, {
      params: { motivo },
    })
    return response.data
  },

  // Listar jornadas activas (supervisor)
  async getJornadasActivas(): Promise<JornadaOperarioList[]> {
    const response = await api.get<JornadaOperarioList[]>('/jornadas-operario/activas')
    return response.data
  },

  // Listar jornadas con filtros
  async getJornadas(params?: {
    operario_id?: string
    proyecto_id?: string
    fecha?: string
    fecha_desde?: string
    fecha_hasta?: string
    estado?: EstadoJornada
    skip?: number
    limit?: number
  }): Promise<JornadaOperarioList[]> {
    const response = await api.get<JornadaOperarioList[]>('/jornadas-operario', { params })
    return response.data
  },

  // Obtener jornada por ID
  async getJornada(jornadaId: string): Promise<JornadaOperario> {
    const response = await api.get<JornadaOperario>(`/jornadas-operario/${jornadaId}`)
    return response.data
  },

  // Mi historial de jornadas
  async getMiHistorial(params?: {
    fecha_desde?: string
    fecha_hasta?: string
    skip?: number
    limit?: number
  }): Promise<JornadaOperarioList[]> {
    const response = await api.get<JornadaOperarioList[]>('/jornadas-operario/historial/mi-historial', { params })
    return response.data
  },

  // Estadísticas del día
  async getEstadisticasDia(fecha?: string): Promise<EstadisticasJornadasDia> {
    const params = fecha ? { fecha } : {}
    const response = await api.get<EstadisticasJornadasDia>('/jornadas-operario/estadisticas/dia', { params })
    return response.data
  },
}

// ============== ASIGNACIONES DIARIAS ==============

export const asignacionesDiariasService = {
  // Mis asignaciones pendientes
  async getMisAsignacionesPendientes(): Promise<AsignacionDiaria[]> {
    const response = await api.get<AsignacionDiaria[]>('/asignaciones-diarias/mis-asignaciones')
    return response.data
  },

  // Mis asignaciones de hoy
  async getMisAsignacionesHoy(): Promise<AsignacionDiaria[]> {
    const response = await api.get<AsignacionDiaria[]>('/asignaciones-diarias/mis-asignaciones/hoy')
    return response.data
  },

  // Listar asignaciones con filtros
  async getAsignaciones(params?: {
    fecha?: string
    fecha_desde?: string
    fecha_hasta?: string
    operario_id?: string
    proyecto_id?: string
    estado?: EstadoAsignacion
    skip?: number
    limit?: number
  }): Promise<AsignacionDiaria[]> {
    const response = await api.get<AsignacionDiaria[]>('/asignaciones-diarias', { params })
    return response.data
  },

  // Obtener asignación por ID
  async getAsignacion(asignacionId: string): Promise<AsignacionDiaria> {
    const response = await api.get<AsignacionDiaria>(`/asignaciones-diarias/${asignacionId}`)
    return response.data
  },

  // Crear asignación (supervisor)
  async crearAsignacion(data: {
    fecha: string
    operario_id: string
    proyecto_id: string
    etapa_id?: string
    vehiculo_id?: string
    prioridad?: string
    notas?: string
    tareas_planificadas?: any[]
    materiales_planificados?: any[]
  }): Promise<AsignacionDiaria> {
    const response = await api.post<AsignacionDiaria>('/asignaciones-diarias', data)
    return response.data
  },

  // Actualizar asignación
  async actualizarAsignacion(asignacionId: string, data: Partial<AsignacionDiaria>): Promise<AsignacionDiaria> {
    const response = await api.put<AsignacionDiaria>(`/asignaciones-diarias/${asignacionId}`, data)
    return response.data
  },

  // Confirmar asignación (operario)
  async confirmarAsignacion(asignacionId: string): Promise<AsignacionDiaria> {
    const response = await api.post<AsignacionDiaria>(`/asignaciones-diarias/${asignacionId}/confirmar`)
    return response.data
  },

  // Cancelar asignación
  async cancelarAsignacion(asignacionId: string): Promise<AsignacionDiaria> {
    const response = await api.post<AsignacionDiaria>(`/asignaciones-diarias/${asignacionId}/cancelar`)
    return response.data
  },

  // Eliminar asignación
  async eliminarAsignacion(asignacionId: string): Promise<void> {
    await api.delete(`/asignaciones-diarias/${asignacionId}`)
  },

  // Asignaciones de una fecha
  async getAsignacionesFecha(fecha: string): Promise<AsignacionDiaria[]> {
    const response = await api.get<AsignacionDiaria[]>(`/asignaciones-diarias/fecha/${fecha}`)
    return response.data
  },

  // Resumen del día
  async getResumenDia(fecha?: string): Promise<any> {
    const params = fecha ? { fecha } : {}
    const response = await api.get('/asignaciones-diarias/resumen/dia', { params })
    return response.data
  },
}

// ============== ACTIVIDADES TIPO ==============

export interface MaterialActividadTipo {
  material_id: string
  cantidad_default: number
  material_nombre?: string
  material_unidad?: string
}

export interface ActividadTipo {
  id: string
  nombre: string
  descripcion?: string
  categoria?: string
  activo: boolean
  created_at: string
  materiales?: MaterialActividadTipo[]
}

export interface ActividadTipoCreate {
  nombre: string
  descripcion?: string
  categoria?: string
  materiales?: { material_id: string; cantidad_default: number }[]
}

export interface AsignacionDiariaCreate {
  fecha: string
  operario_id: string
  proyecto_id: string
  etapa_id?: string
  vehiculo_id?: string
  prioridad?: 'normal' | 'urgente' | 'baja'
  notas?: string
  tareas_planificadas?: any[]
  materiales_planificados?: any[]
}

export const actividadesTipoService = {
  // Listar actividades tipo
  async getActividadesTipo(params?: {
    categoria?: string
    activo?: boolean
    skip?: number
    limit?: number
  }): Promise<ActividadTipo[]> {
    const response = await api.get<ActividadTipo[]>('/actividades-tipo', { params })
    return response.data
  },

  // Obtener actividad por ID
  async getActividadTipo(id: string): Promise<ActividadTipo> {
    const response = await api.get<ActividadTipo>(`/actividades-tipo/${id}`)
    return response.data
  },

  // Crear actividad tipo
  async crearActividadTipo(data: ActividadTipoCreate): Promise<ActividadTipo> {
    const response = await api.post<ActividadTipo>('/actividades-tipo', data)
    return response.data
  },

  // Actualizar actividad tipo
  async actualizarActividadTipo(id: string, data: ActividadTipoCreate): Promise<ActividadTipo> {
    const response = await api.put<ActividadTipo>(`/actividades-tipo/${id}`, data)
    return response.data
  },

  // Eliminar actividad tipo (soft delete)
  async eliminarActividadTipo(id: string): Promise<void> {
    await api.delete(`/actividades-tipo/${id}`)
  },

  // Obtener categorías
  async getCategorias(): Promise<string[]> {
    const response = await api.get<string[]>('/actividades-tipo/categorias')
    return response.data
  },
}

export default jornadasOperarioService
