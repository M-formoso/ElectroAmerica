import api from './api'
import type { Proyecto, Etapa, ItemTrabajo } from '@/types'

export const proyectosService = {
  // Proyectos
  async getProyectos(params?: {
    estado?: string
    skip?: number
    limit?: number
  }): Promise<Proyecto[]> {
    const response = await api.get<Proyecto[]>('/proyectos/', { params })
    return response.data
  },

  async getProyecto(id: string): Promise<Proyecto> {
    const response = await api.get<Proyecto>(`/proyectos/${id}`)
    return response.data
  },

  async createProyecto(data: Partial<Proyecto>): Promise<Proyecto> {
    const response = await api.post<Proyecto>('/proyectos/', data)
    return response.data
  },

  async verificarStockDeposito(
    deposito_id: string,
    actividades: { actividad_tipo_id: string; cantidad_planificada: number }[]
  ): Promise<{
    ok: boolean
    faltantes: {
      material_id: string
      material_nombre: string
      material_codigo?: string
      unidad?: string
      necesario: number
      disponible: number
      faltante: number
    }[]
  }> {
    const response = await api.post('/proyectos/verificar-stock-deposito', {
      deposito_id,
      actividades,
    })
    return response.data
  },

  async updateProyecto(id: string, data: Partial<Proyecto>): Promise<Proyecto> {
    const response = await api.put<Proyecto>(`/proyectos/${id}`, data)
    return response.data
  },

  async deleteProyecto(id: string): Promise<void> {
    await api.delete(`/proyectos/${id}`)
  },

  async cambiarEstado(id: string, nuevoEstado: string): Promise<Proyecto> {
    const response = await api.put<Proyecto>(
      `/proyectos/${id}/estado`,
      null,
      { params: { nuevo_estado: nuevoEstado } }
    )
    return response.data
  },

  // Etapas
  async getEtapas(proyectoId: string): Promise<Etapa[]> {
    const response = await api.get<Etapa[]>(`/etapas/proyecto/${proyectoId}`)
    return response.data
  },

  async getEtapa(id: string): Promise<Etapa> {
    const response = await api.get<Etapa>(`/etapas/${id}`)
    return response.data
  },

  async createEtapa(data: Partial<Etapa>): Promise<Etapa> {
    const response = await api.post<Etapa>('/etapas/', data)
    return response.data
  },

  async updateEtapa(id: string, data: Partial<Etapa>): Promise<Etapa> {
    const response = await api.put<Etapa>(`/etapas/${id}`, data)
    return response.data
  },

  async deleteEtapa(id: string): Promise<void> {
    await api.delete(`/etapas/${id}`)
  },

  async actualizarAvanceEtapa(id: string, porcentaje: number): Promise<Etapa> {
    const response = await api.put<Etapa>(
      `/etapas/${id}/avance`,
      null,
      { params: { porcentaje } }
    )
    return response.data
  },

  // Items de trabajo
  async getItemsTrabajo(etapaId: string): Promise<ItemTrabajo[]> {
    const response = await api.get<ItemTrabajo[]>(`/items-trabajo/etapa/${etapaId}`)
    return response.data
  },

  async createItemTrabajo(data: Partial<ItemTrabajo>): Promise<ItemTrabajo> {
    const response = await api.post<ItemTrabajo>('/items-trabajo/', data)
    return response.data
  },

  async updateItemTrabajo(id: string, data: Partial<ItemTrabajo>): Promise<ItemTrabajo> {
    const response = await api.put<ItemTrabajo>(`/items-trabajo/${id}`, data)
    return response.data
  },

  async actualizarCantidadEjecutada(id: string, cantidad: number): Promise<ItemTrabajo> {
    const response = await api.put<ItemTrabajo>(
      `/items-trabajo/${id}/ejecutado`,
      null,
      { params: { cantidad_ejecutada: cantidad } }
    )
    return response.data
  },
}
