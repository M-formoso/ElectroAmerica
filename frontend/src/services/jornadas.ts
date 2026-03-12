import api from './api'

export interface Jornada {
  id: string
  usuario_id: string
  proyecto_id: string
  etapa_id?: string
  fecha: string
  horas_trabajadas: number
  horas_extra: number
  costo_hora: number
  costo_hora_extra?: number
  descripcion?: string
  notas?: string
  registrado_por_id: string
  created_at: string
  costo_total: number
  usuario_nombre?: string
  proyecto_nombre?: string
  etapa_nombre?: string
}

export interface JornadaCreate {
  usuario_id: string
  proyecto_id: string
  etapa_id?: string
  fecha: string
  horas_trabajadas: number
  horas_extra?: number
  costo_hora: number
  costo_hora_extra?: number
  descripcion?: string
  notas?: string
}

export interface JornadaUpdate {
  etapa_id?: string
  fecha?: string
  horas_trabajadas?: number
  horas_extra?: number
  costo_hora?: number
  costo_hora_extra?: number
  descripcion?: string
  notas?: string
}

export interface ResumenJornadasProyecto {
  proyecto_id: string
  proyecto_nombre: string
  total_horas: number
  total_horas_extra: number
  costo_total: number
  cantidad_jornadas: number
}

export interface ResumenJornadasUsuario {
  usuario_id: string
  usuario_nombre: string
  total_horas: number
  total_horas_extra: number
  costo_total: number
  cantidad_jornadas: number
}

export interface HorasPorEtapa {
  etapa_id: string
  etapa_nombre: string
  horas: number
  horas_extra: number
}

export const jornadasService = {
  getJornadas: async (params?: {
    proyecto_id?: string
    usuario_id?: string
    etapa_id?: string
    fecha_desde?: string
    fecha_hasta?: string
    skip?: number
    limit?: number
  }): Promise<Jornada[]> => {
    const response = await api.get('/jornadas', { params })
    return response.data
  },

  getJornada: async (id: string): Promise<Jornada> => {
    const response = await api.get(`/jornadas/${id}`)
    return response.data
  },

  createJornada: async (data: JornadaCreate): Promise<Jornada> => {
    const response = await api.post('/jornadas', data)
    return response.data
  },

  updateJornada: async (id: string, data: JornadaUpdate): Promise<Jornada> => {
    const response = await api.put(`/jornadas/${id}`, data)
    return response.data
  },

  deleteJornada: async (id: string): Promise<void> => {
    await api.delete(`/jornadas/${id}`)
  },

  getResumenProyecto: async (
    proyectoId: string,
    fechaDesde?: string,
    fechaHasta?: string
  ): Promise<ResumenJornadasProyecto> => {
    const params: any = {}
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta

    const response = await api.get(`/jornadas/proyecto/${proyectoId}/resumen`, { params })
    return response.data
  },

  getResumenUsuario: async (
    usuarioId: string,
    fechaDesde?: string,
    fechaHasta?: string
  ): Promise<ResumenJornadasUsuario> => {
    const params: any = {}
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta

    const response = await api.get(`/jornadas/usuario/${usuarioId}/resumen`, { params })
    return response.data
  },

  getHorasPorEtapa: async (proyectoId: string): Promise<HorasPorEtapa[]> => {
    const response = await api.get(`/jornadas/proyecto/${proyectoId}/por-etapa`)
    return response.data
  }
}

// Helpers
export const formatHoras = (horas: number): string => {
  const h = Math.floor(horas)
  const m = Math.round((horas - h) * 60)
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

export const calcularCostoTotal = (
  horasNormales: number,
  costoHora: number,
  horasExtra: number = 0,
  costoHoraExtra?: number
): number => {
  const costoNormal = horasNormales * costoHora
  const costoExtra = horasExtra * (costoHoraExtra || costoHora * 1.5)
  return costoNormal + costoExtra
}
