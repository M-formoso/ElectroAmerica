import api from './api'

export interface Usuario {
  id: string
  email: string
  nombre: string
  apellido: string
  telefono?: string
  rol: 'administrador' | 'supervisor' | 'operario' | 'cliente'
  activo: boolean
  created_at: string
}

export interface UsuarioCreate {
  email: string
  password: string
  nombre: string
  apellido: string
  telefono?: string
  rol: string
}

export const usuariosService = {
  async getUsuarios(params?: {
    rol?: string
    skip?: number
    limit?: number
  }): Promise<Usuario[]> {
    const response = await api.get<Usuario[]>('/usuarios/', { params })
    return response.data
  },

  async getUsuario(id: string): Promise<Usuario> {
    const response = await api.get<Usuario>(`/usuarios/${id}`)
    return response.data
  },

  async createUsuario(data: UsuarioCreate): Promise<Usuario> {
    const response = await api.post<Usuario>('/usuarios/', data)
    return response.data
  },

  async updateUsuario(id: string, data: Partial<UsuarioCreate>): Promise<Usuario> {
    const response = await api.put<Usuario>(`/usuarios/${id}`, data)
    return response.data
  },

  async deleteUsuario(id: string): Promise<void> {
    await api.delete(`/usuarios/${id}`)
  },

  async getClientes(): Promise<Usuario[]> {
    const response = await api.get<Usuario[]>('/usuarios/clientes')
    return response.data
  },
}
