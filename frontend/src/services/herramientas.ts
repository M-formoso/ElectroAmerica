import api from './api'

// ============ Types ============

export type EstadoHerramienta = 'buen_estado' | 'en_reparacion' | 'rota'
export type EstadoPrestamo = 'disponible' | 'en_uso'

export interface Herramienta {
  id: string
  nombre: string
  descripcion?: string
  estado: EstadoHerramienta
  estado_prestamo: EstadoPrestamo
  activo: boolean
  created_at: string
  foto_url?: string | null
  foto_public_id?: string | null
  // Datos del préstamo activo (si existe)
  retirado_por?: string
  fecha_retiro?: string
}

export interface Prestamo {
  id: string
  herramienta_id: string
  retirado_por: string
  fecha_retiro: string
  fecha_devolucion?: string
  notas_devolucion?: string
  registrado_por_id?: string
  activo: boolean
  created_at: string
}

export interface HerramientaCreate {
  nombre: string
  descripcion?: string
  estado?: EstadoHerramienta
}

export interface HerramientaUpdate {
  nombre?: string
  descripcion?: string
  estado?: EstadoHerramienta
}

export interface PrestamoCreate {
  herramienta_id: string
  retirado_por: string
  fecha_retiro: string
}

export interface PrestamoDevolucion {
  fecha_devolucion: string
  notas_devolucion?: string
}

export interface PrestamoUpdate {
  retirado_por?: string
  fecha_retiro?: string
  fecha_devolucion?: string
  notas_devolucion?: string
}

// ============ Service ============

export const herramientasService = {
  // Herramientas CRUD
  async getHerramientas(params?: {
    estado?: EstadoHerramienta
    estado_prestamo?: EstadoPrestamo
    skip?: number
    limit?: number
  }): Promise<Herramienta[]> {
    const response = await api.get<Herramienta[]>('/herramientas/', { params })
    return response.data
  },

  async getHerramienta(id: string): Promise<Herramienta> {
    const response = await api.get<Herramienta>(`/herramientas/${id}`)
    return response.data
  },

  async createHerramienta(data: HerramientaCreate): Promise<Herramienta> {
    const response = await api.post<Herramienta>('/herramientas/', data)
    return response.data
  },

  async updateHerramienta(id: string, data: HerramientaUpdate): Promise<Herramienta> {
    const response = await api.put<Herramienta>(`/herramientas/${id}`, data)
    return response.data
  },

  async deleteHerramienta(id: string): Promise<void> {
    await api.delete(`/herramientas/${id}`)
  },

  async subirFotoHerramienta(id: string, file: File): Promise<Herramienta> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<Herramienta>(
      `/herramientas/${id}/foto`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    return response.data
  },

  async quitarFotoHerramienta(id: string): Promise<Herramienta> {
    const response = await api.delete<Herramienta>(`/herramientas/${id}/foto`)
    return response.data
  },

  // Préstamos
  async registrarPrestamo(data: PrestamoCreate): Promise<Prestamo> {
    const response = await api.post<Prestamo>('/herramientas/prestamos', data)
    return response.data
  },

  async registrarDevolucion(prestamoId: string, data: PrestamoDevolucion): Promise<Prestamo> {
    const response = await api.post<Prestamo>(`/herramientas/prestamos/${prestamoId}/devolver`, data)
    return response.data
  },

  async getHistorialPrestamos(herramientaId: string, limit: number = 50): Promise<Prestamo[]> {
    const response = await api.get<Prestamo[]>(`/herramientas/${herramientaId}/historial`, {
      params: { limit }
    })
    return response.data
  },

  async updatePrestamo(prestamoId: string, data: PrestamoUpdate): Promise<Prestamo> {
    const response = await api.put<Prestamo>(`/herramientas/prestamos/${prestamoId}`, data)
    return response.data
  },

  async deletePrestamo(prestamoId: string): Promise<void> {
    await api.delete(`/herramientas/prestamos/${prestamoId}`)
  },
}
