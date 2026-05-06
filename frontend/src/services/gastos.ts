import api from './api'
import type { Gasto, CategoriaGasto } from '@/types'

export const gastosService = {
  async getGastos(params?: {
    proyecto_id?: string
    categoria_id?: string
    fecha_desde?: string
    fecha_hasta?: string
    skip?: number
    limit?: number
  }): Promise<Gasto[]> {
    const response = await api.get<Gasto[]>('/gastos/', { params })
    return response.data
  },

  async getGasto(id: string): Promise<Gasto> {
    const response = await api.get<Gasto>(`/gastos/${id}`)
    return response.data
  },

  async createGasto(data: Partial<Gasto>): Promise<Gasto> {
    const response = await api.post<Gasto>('/gastos/', data)
    return response.data
  },

  async updateGasto(id: string, data: Partial<Gasto>): Promise<Gasto> {
    const response = await api.put<Gasto>(`/gastos/${id}`, data)
    return response.data
  },

  async deleteGasto(id: string): Promise<void> {
    await api.delete(`/gastos/${id}`)
  },

  async getGastosPorProyecto(proyectoId: string): Promise<Gasto[]> {
    const response = await api.get<Gasto[]>(`/gastos/por-proyecto/${proyectoId}`)
    return response.data
  },

  // Categorías
  async getCategorias(): Promise<CategoriaGasto[]> {
    const response = await api.get<CategoriaGasto[]>('/gastos/categorias')
    return response.data
  },

  async createCategoria(data: Partial<CategoriaGasto>): Promise<CategoriaGasto> {
    const response = await api.post<CategoriaGasto>('/gastos/categorias', data)
    return response.data
  },
}
