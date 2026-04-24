import api from './api'

// ============ Types ============

export interface ActividadTipoList {
  id: string
  codigo: string
  nombre: string
  categoria: string
  unidad_trabajo: string
  cantidad_materiales: number
  activo: boolean
}

export interface MaterialActividadTipo {
  id: string
  actividad_tipo_id: string
  material_id: string
  cantidad_por_unidad: number
  es_opcional: boolean
  notas?: string
  activo: boolean
  material_codigo?: string
  material_nombre?: string
  material_unidad?: string
  material_stock_actual?: number
}

export interface ActividadTipo {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  categoria: string
  unidad_trabajo: string
  activo: boolean
  materiales: MaterialActividadTipo[]
}

export interface ActividadTipoCreate {
  codigo: string
  nombre: string
  descripcion?: string
  categoria: string
  unidad_trabajo?: string
  materiales?: {
    material_id: string
    cantidad_por_unidad: number
    es_opcional?: boolean
    notas?: string
  }[]
}

export interface ActividadTipoUpdate {
  codigo?: string
  nombre?: string
  descripcion?: string
  categoria?: string
  unidad_trabajo?: string
  activo?: boolean
}

export interface CalcularMaterialesRequest {
  actividad_tipo_id: string
  cantidad_trabajo: number
}

export interface MaterialCalculado {
  material_id: string
  material_nombre: string
  material_unidad: string
  cantidad_necesaria: number
  stock_actual: number
  stock_suficiente: boolean
  faltante: number
}

export interface CalcularMaterialesResponse {
  actividad_nombre: string
  cantidad_trabajo: number
  materiales: MaterialCalculado[]
  hay_faltantes: boolean
}

// ============ Service ============

export const actividadesTipoService = {
  async getActividadesTipo(params?: {
    categoria?: string
    busqueda?: string
    skip?: number
    limit?: number
  }): Promise<ActividadTipoList[]> {
    const response = await api.get<ActividadTipoList[]>('/actividades-tipo', { params })
    return response.data
  },

  async getCategorias(): Promise<string[]> {
    const response = await api.get<{ categorias: string[] }>('/actividades-tipo/categorias')
    return response.data.categorias
  },

  async getActividadTipo(id: string): Promise<ActividadTipo> {
    const response = await api.get<ActividadTipo>(`/actividades-tipo/${id}`)
    return response.data
  },

  async createActividadTipo(data: ActividadTipoCreate): Promise<ActividadTipo> {
    const response = await api.post<ActividadTipo>('/actividades-tipo', data)
    return response.data
  },

  async updateActividadTipo(id: string, data: ActividadTipoUpdate): Promise<ActividadTipo> {
    const response = await api.put<ActividadTipo>(`/actividades-tipo/${id}`, data)
    return response.data
  },

  async deleteActividadTipo(id: string): Promise<void> {
    await api.delete(`/actividades-tipo/${id}`)
  },

  async calcularMateriales(
    actividadTipoId: string,
    cantidadTrabajo: number
  ): Promise<CalcularMaterialesResponse> {
    const response = await api.post<CalcularMaterialesResponse>('/actividades-tipo/calcular-materiales', {
      actividad_tipo_id: actividadTipoId,
      cantidad_trabajo: cantidadTrabajo,
    })
    return response.data
  },
}
