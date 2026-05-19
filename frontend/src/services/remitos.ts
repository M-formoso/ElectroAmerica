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
  deposito_padre_nombre?: string
  es_subdeposito?: boolean
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
  anulado?: boolean
  anulado_at?: string | null
  anulado_por_nombre?: string | null
  motivo_anulacion?: string | null
  editado?: boolean
  editado_at?: string | null
  editado_por_nombre?: string | null
}

export interface RemitoListItem {
  id: string
  numero: number
  numero_formateado: string
  fecha: string
  deposito_id: string
  deposito_nombre?: string
  deposito_padre_nombre?: string
  es_subdeposito?: boolean
  proyecto_id?: string
  proyecto_nombre?: string
  destinatario_texto?: string
  usuario_nombre?: string
  cantidad_items: number
  created_at: string
  anulado?: boolean
  editado?: boolean
}

export interface RemitoUpdate {
  fecha?: string
  proyecto_id?: string | null
  destinatario_texto?: string | null
  responsable_retira?: string | null
  direccion_entrega?: string | null
  transportista?: string | null
  observaciones?: string | null
}

export interface RemitoItemsUpdate {
  items: RemitoItemCreate[]
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

  async actualizar(id: string, data: RemitoUpdate): Promise<Remito> {
    const res = await api.put<Remito>(`/remitos/${id}`, data)
    return res.data
  },

  async actualizarItems(id: string, data: RemitoItemsUpdate): Promise<Remito> {
    const res = await api.put<Remito>(`/remitos/${id}/items`, data)
    return res.data
  },

  async anular(id: string, motivo: string): Promise<Remito> {
    const res = await api.post<Remito>(`/remitos/${id}/anular`, { motivo })
    return res.data
  },
}
