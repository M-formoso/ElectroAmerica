import api from './api'
import type { Etapa, EstadoEtapa } from '@/types'

export interface EtapaCreate {
  proyecto_id: string
  nombre: string
  descripcion?: string
  orden?: number
  fecha_inicio_est?: string
  fecha_fin_est?: string
  estado?: EstadoEtapa
}

export interface EtapaUpdate {
  nombre?: string
  descripcion?: string
  orden?: number
  fecha_inicio_est?: string
  fecha_fin_est?: string
  fecha_inicio_real?: string
  fecha_fin_real?: string
  estado?: EstadoEtapa
  porcentaje_avance?: number
}

export const etapasService = {
  getEtapas: async (proyectoId?: string): Promise<Etapa[]> => {
    const params = proyectoId ? { proyecto_id: proyectoId } : {}
    const response = await api.get('/etapas/', { params })
    return response.data
  },

  getEtapa: async (etapaId: string): Promise<Etapa> => {
    const response = await api.get(`/etapas/${etapaId}`)
    return response.data
  },

  createEtapa: async (data: EtapaCreate): Promise<Etapa> => {
    const response = await api.post('/etapas/', data)
    return response.data
  },

  updateEtapa: async (etapaId: string, data: EtapaUpdate): Promise<Etapa> => {
    const response = await api.put(`/etapas/${etapaId}`, data)
    return response.data
  },

  deleteEtapa: async (etapaId: string): Promise<void> => {
    await api.delete(`/etapas/${etapaId}`)
  },

  updateAvance: async (etapaId: string, porcentaje: number): Promise<{ etapa_id: string; porcentaje_avance: number; estado: string }> => {
    const response = await api.put(`/etapas/${etapaId}/avance`, null, {
      params: { porcentaje }
    })
    return response.data
  },

  reordenarEtapas: async (proyectoId: string, ordenIds: string[]): Promise<void> => {
    await api.post('/etapas/reordenar', {
      proyecto_id: proyectoId,
      orden_ids: ordenIds
    })
  },

  getEtapasDemoradas: async (): Promise<Etapa[]> => {
    const response = await api.get('/etapas/demoradas')
    return response.data
  },
}
