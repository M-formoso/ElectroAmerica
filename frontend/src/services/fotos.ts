import api from './api'
import type { Foto } from '@/types'

export interface FotoCreate {
  proyecto_id: string
  etapa_id?: string
  descripcion?: string
  visible_cliente?: boolean
}

export interface FotoUpdate {
  descripcion?: string
  visible_cliente?: boolean
}

export interface UploadResponse {
  id: string
  url: string
  thumbnail_url: string
  proyecto_id: string
  etapa_id?: string
  descripcion?: string
  fecha: string
  visible_cliente: boolean
  public_id: string
}

export const fotosService = {
  getFotos: async (proyectoId?: string, etapaId?: string): Promise<Foto[]> => {
    const params: Record<string, string> = {}
    if (proyectoId) params.proyecto_id = proyectoId
    if (etapaId) params.etapa_id = etapaId
    const response = await api.get('/fotos/', { params })
    return response.data
  },

  getFoto: async (fotoId: string): Promise<Foto> => {
    const response = await api.get(`/fotos/${fotoId}`)
    return response.data
  },

  updateFoto: async (fotoId: string, data: FotoUpdate): Promise<Foto> => {
    const response = await api.put(`/fotos/${fotoId}`, data)
    return response.data
  },

  deleteFoto: async (fotoId: string): Promise<void> => {
    await api.delete(`/fotos/${fotoId}`)
  },

  // Upload de imagen genérica
  uploadImagen: async (file: File, folder: string = 'general'): Promise<{ url: string; thumbnail_url: string; public_id: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder', folder)

    const response = await api.post('/upload/imagen', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  // Upload de foto de proyecto (crea registro en BD automáticamente)
  uploadFotoProyecto: async (
    file: File,
    proyectoId: string,
    etapaId?: string,
    descripcion?: string,
    visibleCliente: boolean = false
  ): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('proyecto_id', proyectoId)
    if (etapaId) formData.append('etapa_id', etapaId)
    if (descripcion) formData.append('descripcion', descripcion)
    formData.append('visible_cliente', String(visibleCliente))

    const response = await api.post('/upload/foto-proyecto', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  // Eliminar imagen de Cloudinary
  deleteImagen: async (publicId: string): Promise<void> => {
    await api.delete(`/upload/imagen/${encodeURIComponent(publicId)}`)
  },
}
