import api from './api'
import type { Material } from '@/types'

export const materialesService = {
  async getMateriales(params?: {
    skip?: number
    limit?: number
  }): Promise<Material[]> {
    const response = await api.get<Material[]>('/materiales/', { params })
    return response.data
  },

  async getMaterial(id: string): Promise<Material> {
    const response = await api.get<Material>(`/materiales/${id}`)
    return response.data
  },

  async createMaterial(data: Partial<Material>): Promise<Material> {
    const response = await api.post<Material>('/materiales/', data)
    return response.data
  },

  async updateMaterial(id: string, data: Partial<Material>): Promise<Material> {
    const response = await api.put<Material>(`/materiales/${id}`, data)
    return response.data
  },

  async deleteMaterial(id: string): Promise<void> {
    await api.delete(`/materiales/${id}`)
  },

  async registrarEntrada(
    id: string,
    cantidad: number,
    motivo?: string,
    proyectoId?: string
  ): Promise<Material> {
    const response = await api.post<Material>(`/materiales/${id}/entrada`, {
      cantidad,
      motivo,
      proyecto_id: proyectoId,
    })
    return response.data
  },

  async registrarSalida(
    id: string,
    cantidad: number,
    motivo?: string,
    proyectoId?: string
  ): Promise<Material> {
    const response = await api.post<Material>(`/materiales/${id}/salida`, {
      cantidad,
      motivo,
      proyecto_id: proyectoId,
    })
    return response.data
  },

  async getStockBajo(): Promise<Material[]> {
    const response = await api.get<Material[]>('/materiales/stock-bajo')
    return response.data
  },
}
