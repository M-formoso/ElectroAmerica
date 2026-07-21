import api from './api'
import type { TipoIngreso } from './finanzas'

// ============ TYPES ============

export interface Socio {
  id: string
  nombre: string
  apellido?: string | null
  porcentaje_participacion: number
  email?: string | null
  telefono?: string | null
  notas?: string | null
  usuario_id?: string | null
  activo: boolean
}

export interface SocioCreate {
  nombre: string
  apellido?: string
  porcentaje_participacion?: number
  email?: string
  telefono?: string
  notas?: string
  usuario_id?: string
}

export interface SocioUpdate {
  nombre?: string
  apellido?: string
  porcentaje_participacion?: number
  email?: string
  telefono?: string
  notas?: string
  usuario_id?: string
}

export interface AporteSocio {
  id: string
  socio_id: string
  socio_nombre?: string | null
  monto: number
  fecha: string
  concepto?: string | null
  observaciones?: string | null
  cuenta_id?: string | null
  cuenta_nombre?: string | null
  creado_por_id: string
}

export interface AporteSocioCreate {
  socio_id: string
  monto: number
  fecha: string
  concepto?: string
  observaciones?: string
  cuenta_id?: string
}

export interface AporteSocioUpdate {
  monto?: number
  fecha?: string
  concepto?: string
  observaciones?: string
  cuenta_id?: string
}

export interface RetiroSocio {
  id: string
  socio_id: string
  socio_nombre?: string | null
  monto: number
  fecha: string
  concepto?: string | null
  observaciones?: string | null
  cuenta_id?: string | null
  cuenta_nombre?: string | null
  creado_por_id: string
}

export interface RetiroSocioCreate {
  socio_id: string
  monto: number
  fecha: string
  concepto?: string
  observaciones?: string
  cuenta_id?: string
}

export interface RetiroSocioUpdate {
  monto?: number
  fecha?: string
  concepto?: string
  observaciones?: string
  cuenta_id?: string
}

export interface ItemPlanilla {
  id: string
  concepto: string
  monto: number
  fecha: string
  referencia?: string | null
}

export interface PlanillaIngresos {
  tipo: TipoIngreso
  label: string
  total: number
  cantidad: number
  items: ItemPlanilla[]
}

export interface PlanillaGastos {
  categoria_id?: string | null
  categoria: string
  total: number
  cantidad: number
  items: ItemPlanilla[]
}

export interface SaldoSocio {
  socio_id: string
  nombre: string
  porcentaje_participacion: number
  ganancia_asignada: number
  total_retiros: number
  saldo_disponible: number
  retiros: ItemPlanilla[]
}

export interface ResumenPanelSocios {
  fecha_desde: string
  fecha_hasta: string
  total_ingresos: number
  planillas_ingresos: PlanillaIngresos[]
  total_gastos: number
  planillas_gastos: PlanillaGastos[]
  ganancia: number
  socios: SaldoSocio[]
}

// ============ API ============

export const getResumenPanel = async (params: {
  fecha_desde: string
  fecha_hasta: string
}): Promise<ResumenPanelSocios> => {
  const response = await api.get('/panel-socios/resumen', { params })
  return response.data
}

// Socios
export const getSocios = async (): Promise<Socio[]> => {
  const response = await api.get('/panel-socios/socios')
  return response.data
}

export const createSocio = async (data: SocioCreate): Promise<Socio> => {
  const response = await api.post('/panel-socios/socios', data)
  return response.data
}

export const updateSocio = async (id: string, data: SocioUpdate): Promise<Socio> => {
  const response = await api.put(`/panel-socios/socios/${id}`, data)
  return response.data
}

export const deleteSocio = async (id: string): Promise<void> => {
  await api.delete(`/panel-socios/socios/${id}`)
}

// Aportes
export const getAportes = async (params?: {
  socio_id?: string
  fecha_desde?: string
  fecha_hasta?: string
}): Promise<AporteSocio[]> => {
  const response = await api.get('/panel-socios/aportes', { params })
  return response.data
}

export const createAporte = async (data: AporteSocioCreate): Promise<AporteSocio> => {
  const response = await api.post('/panel-socios/aportes', data)
  return response.data
}

export const updateAporte = async (id: string, data: AporteSocioUpdate): Promise<AporteSocio> => {
  const response = await api.put(`/panel-socios/aportes/${id}`, data)
  return response.data
}

export const deleteAporte = async (id: string): Promise<void> => {
  await api.delete(`/panel-socios/aportes/${id}`)
}

// Retiros
export const getRetiros = async (params?: {
  socio_id?: string
  fecha_desde?: string
  fecha_hasta?: string
}): Promise<RetiroSocio[]> => {
  const response = await api.get('/panel-socios/retiros', { params })
  return response.data
}

export const createRetiro = async (data: RetiroSocioCreate): Promise<RetiroSocio> => {
  const response = await api.post('/panel-socios/retiros', data)
  return response.data
}

export const updateRetiro = async (id: string, data: RetiroSocioUpdate): Promise<RetiroSocio> => {
  const response = await api.put(`/panel-socios/retiros/${id}`, data)
  return response.data
}

export const deleteRetiro = async (id: string): Promise<void> => {
  await api.delete(`/panel-socios/retiros/${id}`)
}

// Helpers
export const getTipoIngresoLabel = (tipo: TipoIngreso): string => {
  const labels: Record<TipoIngreso, string> = {
    cobro_factura_obra: 'Cobro factura obras',
    cobro_factura_venta: 'Cobro factura ventas',
    aporte_socio: 'Aportes de socios',
    otro: 'Otros ingresos',
  }
  return labels[tipo] || tipo
}
