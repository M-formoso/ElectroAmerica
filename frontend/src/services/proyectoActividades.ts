import api from './api'

// ============ Types ============

export interface MaterialCalculado {
  material_id: string
  material_nombre: string
  material_codigo?: string
  cantidad_total: number
  unidad: string
}

export interface MaterialConsumido {
  material_id: string
  material_nombre: string
  cantidad: number
  unidad: string
}

export interface ProyectoActividadList {
  id: string
  actividad_tipo_id: string
  actividad_codigo: string
  actividad_nombre: string
  actividad_categoria: string
  unidad_trabajo: string
  cantidad_planificada: number
  cantidad_ejecutada: number
  porcentaje_avance: number
  orden: number
}

export interface ProyectoActividad {
  id: string
  proyecto_id: string
  actividad_tipo_id: string
  cantidad_planificada: number
  cantidad_ejecutada: number
  orden: number
  observaciones?: string
  materiales_calculados?: MaterialCalculado[]
  porcentaje_avance: number
  cantidad_pendiente: number
  activo: boolean
  created_at: string
  actividad_codigo?: string
  actividad_nombre?: string
  actividad_categoria?: string
  unidad_trabajo?: string
}

export interface ProyectoActividadCreate {
  actividad_tipo_id: string
  cantidad_planificada?: number
  observaciones?: string
  orden?: number
}

export interface ProyectoActividadUpdate {
  cantidad_planificada?: number
  observaciones?: string
  orden?: number
}

export interface AvanceActividad {
  id: string
  proyecto_actividad_id: string
  fecha: string
  cantidad: number
  observaciones?: string
  materiales_consumidos?: MaterialConsumido[]
  registrado_por_id?: string
  registrado_por_nombre?: string
  created_at: string
}

export interface AvanceActividadCreate {
  fecha: string
  cantidad: number
  observaciones?: string
  materiales_consumidos?: MaterialConsumido[]
}

export interface AvanceActividadUpdate {
  cantidad?: number
  observaciones?: string
  materiales_consumidos?: MaterialConsumido[]
}

export interface ProyectoHerramienta {
  id: string
  proyecto_id: string
  herramienta_id: string
  herramienta_nombre?: string
  herramienta_codigo?: string
  fecha_asignacion?: string
  observaciones?: string
  activo: boolean
}

export interface ResumenActividadesProyecto {
  total_actividades: number
  actividades_completadas: number
  actividades_en_progreso: number
  actividades_pendientes: number
  porcentaje_avance_global: number
  materiales_totales: MaterialCalculado[]
}

// ============ Service ============

export const proyectoActividadesService = {
  // Actividades de proyecto
  async getActividades(proyectoId: string): Promise<ProyectoActividadList[]> {
    const response = await api.get<ProyectoActividadList[]>(`/proyectos/${proyectoId}/actividades`)
    return response.data
  },

  async getActividad(proyectoId: string, actividadId: string): Promise<ProyectoActividad> {
    const response = await api.get<ProyectoActividad>(`/proyectos/${proyectoId}/actividades/${actividadId}`)
    return response.data
  },

  async createActividad(proyectoId: string, data: ProyectoActividadCreate): Promise<ProyectoActividad> {
    const response = await api.post<ProyectoActividad>(`/proyectos/${proyectoId}/actividades`, data)
    return response.data
  },

  async createActividadesBulk(
    proyectoId: string,
    actividades: ProyectoActividadCreate[]
  ): Promise<ProyectoActividad[]> {
    const response = await api.post<ProyectoActividad[]>(`/proyectos/${proyectoId}/actividades/bulk`, {
      actividades,
    })
    return response.data
  },

  async updateActividad(
    proyectoId: string,
    actividadId: string,
    data: ProyectoActividadUpdate
  ): Promise<ProyectoActividad> {
    const response = await api.put<ProyectoActividad>(
      `/proyectos/${proyectoId}/actividades/${actividadId}`,
      data
    )
    return response.data
  },

  async deleteActividad(proyectoId: string, actividadId: string): Promise<void> {
    await api.delete(`/proyectos/${proyectoId}/actividades/${actividadId}`)
  },

  // Avances
  async getAvances(proyectoId: string, actividadId: string): Promise<AvanceActividad[]> {
    const response = await api.get<AvanceActividad[]>(
      `/proyectos/${proyectoId}/actividades/${actividadId}/avances`
    )
    return response.data
  },

  async createAvance(
    proyectoId: string,
    actividadId: string,
    data: AvanceActividadCreate
  ): Promise<AvanceActividad> {
    const response = await api.post<AvanceActividad>(
      `/proyectos/${proyectoId}/actividades/${actividadId}/avances`,
      data
    )
    return response.data
  },

  async updateAvance(
    proyectoId: string,
    actividadId: string,
    avanceId: string,
    data: AvanceActividadUpdate
  ): Promise<AvanceActividad> {
    const response = await api.put<AvanceActividad>(
      `/proyectos/${proyectoId}/actividades/${actividadId}/avances/${avanceId}`,
      data
    )
    return response.data
  },

  async deleteAvance(proyectoId: string, actividadId: string, avanceId: string): Promise<void> {
    await api.delete(`/proyectos/${proyectoId}/actividades/${actividadId}/avances/${avanceId}`)
  },

  // Resumen
  async getResumen(proyectoId: string): Promise<ResumenActividadesProyecto> {
    const response = await api.get<ResumenActividadesProyecto>(
      `/proyectos/${proyectoId}/resumen-actividades`
    )
    return response.data
  },

  // Herramientas
  async getHerramientas(proyectoId: string): Promise<ProyectoHerramienta[]> {
    const response = await api.get<ProyectoHerramienta[]>(`/proyectos/${proyectoId}/herramientas`)
    return response.data
  },

  async asignarHerramientas(proyectoId: string, herramientasIds: string[]): Promise<ProyectoHerramienta[]> {
    const response = await api.post<ProyectoHerramienta[]>(`/proyectos/${proyectoId}/herramientas/bulk`, {
      herramientas_ids: herramientasIds,
    })
    return response.data
  },

  async desasignarHerramienta(proyectoId: string, herramientaId: string): Promise<void> {
    await api.delete(`/proyectos/${proyectoId}/herramientas/${herramientaId}`)
  },
}
