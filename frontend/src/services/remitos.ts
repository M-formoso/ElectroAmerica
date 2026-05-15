import api from './api'

export interface RemitoItemCreate {
  material_id: string
  cantidad: number
}

export interface RemitoItem {
  id: string
  material_id?: string
  material_codigo?: string
  material_nombre: string
  material_unidad: string
  cantidad: number
}

export interface RemitoCreate {
  fecha: string
  deposito_id: string
  proyecto_id?: string
  destinatario_texto?: string
  responsable_retira?: string
  direccion_entrega?: string
  transportista?: string
  observaciones?: string
  items: RemitoItemCreate[]
}

export interface Remito {
  id: string
  numero: number
  numero_formateado: string
  fecha: string
  deposito_id: string
  deposito_nombre?: string
  proyecto_id?: string
  proyecto_nombre?: string
  destinatario_texto?: string
  responsable_retira?: string
  direccion_entrega?: string
  transportista?: string
  observaciones?: string
  usuario_id?: string
  usuario_nombre?: string
  items: RemitoItem[]
  created_at: string
}

export interface RemitoListItem {
  id: string
  numero: number
  numero_formateado: string
  fecha: string
  deposito_id: string
  deposito_nombre?: string
  proyecto_id?: string
  proyecto_nombre?: string
  destinatario_texto?: string
  usuario_nombre?: string
  cantidad_items: number
  created_at: string
}

export interface RemitosFilters {
  deposito_id?: string
  proyecto_id?: string
  fecha_desde?: string
  fecha_hasta?: string
  busqueda?: string
  limit?: number
}

export const remitosService = {
  async listar(params: RemitosFilters = {}): Promise<RemitoListItem[]> {
    const res = await api.get<RemitoListItem[]>('/remitos', {
      params: { limit: 200, ...params },
    })
    return res.data
  },

  async obtener(id: string): Promise<Remito> {
    const res = await api.get<Remito>(`/remitos/${id}`)
    return res.data
  },

  async crear(data: RemitoCreate): Promise<Remito> {
    const res = await api.post<Remito>('/remitos', data)
    return res.data
  },

  async descargarPdf(id: string, numeroFormateado: string): Promise<void> {
    const res = await api.get(`/remitos/${id}/pdf`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${numeroFormateado}.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}
