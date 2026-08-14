import api from './api'

// ============ TYPES ============

export type EstadoFactura = 'pendiente' | 'pagada'

export interface Factura {
  id: string
  cliente_id: string
  proyecto_id: string
  descripcion?: string | null
  fecha_inscripcion: string
  monto: number
  fecha_pago?: string | null
  estado: EstadoFactura
  transaccion_id?: string | null
  creado_por_id: string
  observaciones?: string | null
  cliente_nombre?: string | null
  proyecto_nombre?: string | null
}

export interface FacturaCreate {
  cliente_id: string
  proyecto_id: string
  descripcion?: string
  fecha_inscripcion: string
  monto: number
  observaciones?: string
}

export interface FacturaUpdate {
  cliente_id?: string
  proyecto_id?: string
  descripcion?: string
  fecha_inscripcion?: string
  monto?: number
  observaciones?: string
}

export interface MarcarPagadaRequest {
  fecha_pago: string
  observaciones?: string
}

export interface EmpresaFacturasResumen {
  id: string
  nombre: string
  cuit?: string | null
  email?: string | null
  telefono?: string | null
  cantidad_facturas: number
  cantidad_pendientes: number
  total_pendiente: number
  total_pagado: number
}

export interface EmpresaQuickCreate {
  razon_social: string
  nombre_fantasia?: string
  cuit?: string
  email?: string
  telefono?: string
}

export interface FacturaMesItem {
  anio: number
  mes: number
  label: string
  total: number
  cantidad: number
  facturas: Factura[]
}

// ============ EMPRESAS ============

const BASE = '/facturas-a-cobrar'

export const facturasService = {
  // Empresas
  listarEmpresas: async (): Promise<EmpresaFacturasResumen[]> => {
    const { data } = await api.get(`${BASE}/empresas`)
    return data
  },

  crearEmpresa: async (payload: EmpresaQuickCreate): Promise<EmpresaFacturasResumen> => {
    const { data } = await api.post(`${BASE}/empresas`, payload)
    return data
  },

  eliminarEmpresa: async (clienteId: string): Promise<void> => {
    await api.delete(`${BASE}/empresas/${clienteId}`)
  },

  // Facturas
  listar: async (params?: {
    cliente_id?: string
    proyecto_id?: string
    estado?: EstadoFactura
    fecha_desde?: string
    fecha_hasta?: string
  }): Promise<Factura[]> => {
    const { data } = await api.get(BASE, { params })
    return data
  },

  listarPendientes: async (): Promise<Factura[]> => {
    const { data } = await api.get(`${BASE}/pendientes`)
    return data
  },

  porMes: async (params?: { cliente_id?: string; anio?: number }): Promise<FacturaMesItem[]> => {
    const { data } = await api.get(`${BASE}/por-mes`, { params })
    return data
  },

  obtener: async (id: string): Promise<Factura> => {
    const { data } = await api.get(`${BASE}/${id}`)
    return data
  },

  crear: async (payload: FacturaCreate): Promise<Factura> => {
    const { data } = await api.post(BASE, payload)
    return data
  },

  actualizar: async (id: string, payload: FacturaUpdate): Promise<Factura> => {
    const { data } = await api.put(`${BASE}/${id}`, payload)
    return data
  },

  eliminar: async (id: string): Promise<void> => {
    await api.delete(`${BASE}/${id}`)
  },

  marcarPagada: async (id: string, payload: MarcarPagadaRequest): Promise<Factura> => {
    const { data } = await api.post(`${BASE}/${id}/marcar-pagada`, payload)
    return data
  },

  marcarPendiente: async (id: string): Promise<Factura> => {
    const { data } = await api.post(`${BASE}/${id}/marcar-pendiente`)
    return data
  },
}
