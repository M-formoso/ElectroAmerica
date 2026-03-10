import api from './api'
import type { Equipo } from '@/types'

export const equiposService = {
  async getEquipos(params?: {
    estado?: string
    tipo?: string
    skip?: number
    limit?: number
  }): Promise<Equipo[]> {
    const response = await api.get<Equipo[]>('/equipos/', { params })
    return response.data
  },

  async getEquipo(id: string): Promise<Equipo> {
    const response = await api.get<Equipo>(`/equipos/${id}`)
    return response.data
  },

  async createEquipo(data: Partial<Equipo>): Promise<Equipo> {
    const response = await api.post<Equipo>('/equipos/', data)
    return response.data
  },

  async updateEquipo(id: string, data: Partial<Equipo>): Promise<Equipo> {
    const response = await api.put<Equipo>(`/equipos/${id}`, data)
    return response.data
  },

  async deleteEquipo(id: string): Promise<void> {
    await api.delete(`/equipos/${id}`)
  },

  async asignarEquipo(
    id: string,
    proyectoId: string,
    fechaDevolucionEst?: string
  ): Promise<Equipo> {
    const response = await api.post<Equipo>(`/equipos/${id}/asignar`, {
      proyecto_id: proyectoId,
      fecha_devolucion_est: fechaDevolucionEst,
    })
    return response.data
  },

  async devolverEquipo(id: string): Promise<Equipo> {
    const response = await api.post<Equipo>(`/equipos/${id}/devolver`)
    return response.data
  },

  async cambiarEstado(id: string, nuevoEstado: string): Promise<Equipo> {
    const response = await api.put<Equipo>(
      `/equipos/${id}/estado`,
      null,
      { params: { nuevo_estado: nuevoEstado } }
    )
    return response.data
  },

  async getDisponibles(): Promise<Equipo[]> {
    const response = await api.get<Equipo[]>('/equipos/', {
      params: { estado: 'disponible' },
    })
    return response.data
  },
}
