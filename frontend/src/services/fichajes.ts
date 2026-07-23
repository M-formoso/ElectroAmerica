import { api } from './api'

export type EstadoFichaje = 'activo' | 'completado' | 'cancelado'

export interface FichajeResponse {
  id: string
  operario_id: string
  operario_nombre?: string
  operario_apellido?: string
  fecha: string
  hora_inicio: string
  hora_fin?: string
  horas_trabajadas?: number
  estado: EstadoFichaje
  proyecto_id?: string
  proyecto_nombre?: string
  notas_inicio?: string
  notas_fin?: string
  created_at: string
  updated_at: string
}

export interface FichajeListItem {
  id: string
  operario_id: string
  operario_nombre?: string
  operario_apellido?: string
  fecha: string
  hora_inicio: string
  hora_fin?: string
  horas_trabajadas?: number
  estado: EstadoFichaje
  proyecto_id?: string
  proyecto_nombre?: string
}

export interface ResumenFichajes {
  total_fichajes: number
  fichajes_activos: number
  fichajes_completados: number
  horas_totales: number
  promedio_horas: number
}

export interface IniciarFichajeRequest {
  proyecto_id?: string
  notas_inicio?: string
}

export interface FinalizarFichajeRequest {
  notas_fin?: string
}

export const fichajesService = {
  async iniciar(data: IniciarFichajeRequest = {}): Promise<FichajeResponse> {
    const res = await api.post('/fichajes/iniciar', data)
    return res.data
  },

  async obtenerActivo(): Promise<FichajeResponse | null> {
    const res = await api.get('/fichajes/activo')
    return res.data
  },

  async finalizar(id: string, data: FinalizarFichajeRequest = {}): Promise<FichajeResponse> {
    const res = await api.post(`/fichajes/${id}/finalizar`, data)
    return res.data
  },

  async cancelar(id: string): Promise<FichajeResponse> {
    const res = await api.post(`/fichajes/${id}/cancelar`)
    return res.data
  },

  async misFichajes(limit = 30): Promise<FichajeListItem[]> {
    const res = await api.get('/fichajes/mis-fichajes', { params: { limit } })
    return res.data
  },

  async listar(params?: {
    fecha_desde?: string
    fecha_hasta?: string
    operario_id?: string
    estado?: EstadoFichaje
    skip?: number
    limit?: number
  }): Promise<FichajeListItem[]> {
    const res = await api.get('/fichajes/', { params })
    return res.data
  },

  async resumen(params?: {
    fecha_desde?: string
    fecha_hasta?: string
    operario_id?: string
  }): Promise<ResumenFichajes> {
    const res = await api.get('/fichajes/resumen', { params })
    return res.data
  },
}
