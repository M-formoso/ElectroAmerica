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
    materialId: string,
    cantidad: number,
    motivo?: string
  ): Promise<any> {
    const response = await api.post('/materiales/ingreso', {
      material_id: materialId,
      cantidad,
      motivo,
    })
    return response.data
  },

  async registrarSalida(
    materialId: string,
    cantidad: number,
    motivo?: string,
    proyectoId?: string
  ): Promise<any> {
    // Usamos asignar para registrar salida (requiere proyecto)
    const response = await api.post('/materiales/asignar', {
      material_id: materialId,
      proyecto_id: proyectoId,
      cantidad,
      observaciones: motivo,
    })
    return response.data
  },

  async getStockBajo(): Promise<Material[]> {
    const response = await api.get<Material[]>('/materiales/stock-bajo')
    return response.data
  },
}
