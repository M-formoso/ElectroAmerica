import api from './api'

// ============ TYPES ============

export type TipoCliente = 'particular' | 'empresa' | 'gobierno' | 'constructora' | 'consorcio' | 'otro'
export type CondicionIVA = 'responsable_inscripto' | 'monotributo' | 'exento' | 'consumidor_final' | 'no_responsable'

export interface Cliente {
  id: string
  codigo: string
  tipo: TipoCliente
  razon_social: string
  nombre_fantasia?: string
  cuit?: string
  condicion_iva: CondicionIVA
  email?: string
  telefono?: string
  celular?: string
  contacto_nombre?: string
  contacto_cargo?: string
  direccion?: string
  ciudad?: string
  provincia?: string
  codigo_postal?: string
  descuento_general: number
  limite_credito?: number
  dias_credito: number
  enviar_notificaciones: boolean
  notas?: string
  notas_internas?: string
  saldo_cuenta_corriente: number
  fecha_alta?: string
  fecha_ultimo_proyecto?: string
  usuario_id?: string
  activo: boolean
  nombre_display: string
  tiene_deuda: boolean
  cantidad_proyectos: number
  usuario_email?: string
}

export interface ClienteListItem {
  id: string
  codigo: string
  razon_social: string
  nombre_fantasia?: string
  tipo: TipoCliente
  cuit?: string
  telefono?: string
  email?: string
  ciudad?: string
  saldo_cuenta_corriente: number
  activo: boolean
}

export interface ClienteCreate {
  tipo?: TipoCliente
  razon_social: string
  nombre_fantasia?: string
  cuit?: string
  condicion_iva?: CondicionIVA
  email?: string
  telefono?: string
  celular?: string
  contacto_nombre?: string
  contacto_cargo?: string
  direccion?: string
  ciudad?: string
  provincia?: string
  codigo_postal?: string
  descuento_general?: number
  limite_credito?: number
  dias_credito?: number
  enviar_notificaciones?: boolean
  notas?: string
  notas_internas?: string
}

export interface ClienteUpdate {
  tipo?: TipoCliente
  razon_social?: string
  nombre_fantasia?: string
  cuit?: string
  condicion_iva?: CondicionIVA
  email?: string
  telefono?: string
  celular?: string
  contacto_nombre?: string
  contacto_cargo?: string
  direccion?: string
  ciudad?: string
  provincia?: string
  codigo_postal?: string
  descuento_general?: number
  limite_credito?: number
  dias_credito?: number
  enviar_notificaciones?: boolean
  notas?: string
  notas_internas?: string
}

export interface EstadoCuentaCliente {
  cliente_id: string
  cliente_nombre: string
  saldo_actual: number
  limite_credito?: number
  credito_disponible?: number
  total_facturado_mes: number
  total_pagado_mes: number
  proyectos_activos: number
  dias_factura_mas_antigua?: number
}

export interface MovimientoCuentaCorriente {
  id: string
  tipo: 'cargo' | 'pago' | 'ajuste'
  concepto: string
  monto: number
  fecha: string
  saldo_anterior: number
  saldo_posterior: number
  referencia?: string
  proyecto_nombre?: string
}

export interface RegistroPagoCreate {
  monto: number
  fecha: string
  metodo_pago?: string
  referencia?: string
  notas?: string
  proyecto_id?: string
}

export interface PagoResponse {
  id: string
  cliente_id: string
  monto: number
  fecha: string
  metodo_pago: string
  referencia?: string
  numero_recibo: string
  saldo_anterior: number
  saldo_posterior: number
}

export interface UsuarioClienteCreate {
  email: string
  nombre: string
  apellido?: string
  telefono?: string
  password?: string
}

export interface UsuarioClienteResponse {
  id: string
  email: string
  nombre: string
  apellido?: string
  activo: boolean
  password_visible?: string
}

export interface ProyectoClienteResumen {
  id: string
  nombre: string
  estado: string
  porcentaje_avance: number
  fecha_inicio?: string
  fecha_fin_estimada?: string
  monto_contratado?: number
}

export interface ClienteConProyectos extends Cliente {
  proyectos: ProyectoClienteResumen[]
}

export interface EstadisticasClientes {
  total_clientes: number
  clientes_con_deuda: number
  total_deuda: number
  por_tipo: { tipo: string; cantidad: number }[]
}

// ============ API FUNCTIONS ============

// CRUD Clientes
export const getClientes = async (params?: {
  tipo?: TipoCliente
  activo?: boolean
  con_deuda?: boolean
  buscar?: string
  skip?: number
  limit?: number
}): Promise<ClienteListItem[]> => {
  const response = await api.get('/clientes', { params })
  return response.data
}

export const getClientesLista = async (): Promise<ClienteListItem[]> => {
  const response = await api.get('/clientes/lista')
  return response.data
}

export const getCliente = async (id: string): Promise<Cliente> => {
  const response = await api.get(`/clientes/${id}`)
  return response.data
}

export const getClienteCompleto = async (id: string): Promise<ClienteConProyectos> => {
  const response = await api.get(`/clientes/${id}/completo`)
  return response.data
}

export const createCliente = async (data: ClienteCreate): Promise<Cliente> => {
  const response = await api.post('/clientes', data)
  return response.data
}

export const updateCliente = async (id: string, data: ClienteUpdate): Promise<Cliente> => {
  const response = await api.put(`/clientes/${id}`, data)
  return response.data
}

export const deleteCliente = async (id: string): Promise<void> => {
  await api.delete(`/clientes/${id}`)
}

// Tipos y condiciones
export const getTiposCliente = async (): Promise<{ value: string; label: string }[]> => {
  const response = await api.get('/clientes/tipos')
  return response.data
}

export const getCondicionesIVA = async (): Promise<{ value: string; label: string }[]> => {
  const response = await api.get('/clientes/condiciones-iva')
  return response.data
}

// Estadísticas
export const getEstadisticasClientes = async (): Promise<EstadisticasClientes> => {
  const response = await api.get('/clientes/estadisticas')
  return response.data
}

// Cuenta Corriente
export const getEstadoCuenta = async (clienteId: string): Promise<EstadoCuentaCliente> => {
  const response = await api.get(`/clientes/${clienteId}/cuenta-corriente`)
  return response.data
}

export const getMovimientosCuenta = async (
  clienteId: string,
  params?: {
    fecha_desde?: string
    fecha_hasta?: string
    skip?: number
    limit?: number
  }
): Promise<MovimientoCuentaCorriente[]> => {
  const response = await api.get(`/clientes/${clienteId}/movimientos`, { params })
  return response.data
}

export const registrarPago = async (clienteId: string, data: RegistroPagoCreate): Promise<PagoResponse> => {
  const response = await api.post(`/clientes/${clienteId}/pagos`, data)
  return response.data
}

// Usuario Cliente
export const getUsuarioCliente = async (clienteId: string): Promise<UsuarioClienteResponse | null> => {
  const response = await api.get(`/clientes/${clienteId}/usuario`)
  return response.data
}

export const crearUsuarioCliente = async (
  clienteId: string,
  data: UsuarioClienteCreate
): Promise<UsuarioClienteResponse> => {
  const response = await api.post(`/clientes/${clienteId}/usuario`, data)
  return response.data
}

export const resetPasswordUsuario = async (clienteId: string): Promise<{ password: string }> => {
  const response = await api.post(`/clientes/${clienteId}/usuario/reset-password`)
  return response.data
}

// Proyectos del cliente
export const getProyectosCliente = async (clienteId: string): Promise<ProyectoClienteResumen[]> => {
  const response = await api.get(`/clientes/${clienteId}/proyectos`)
  return response.data
}

// ============ HELPERS ============

export const getTipoClienteLabel = (tipo: TipoCliente): string => {
  const labels: Record<TipoCliente, string> = {
    particular: 'Particular',
    empresa: 'Empresa',
    gobierno: 'Gobierno',
    constructora: 'Constructora',
    consorcio: 'Consorcio',
    otro: 'Otro',
  }
  return labels[tipo] || tipo
}

export const getCondicionIVALabel = (condicion: CondicionIVA): string => {
  const labels: Record<CondicionIVA, string> = {
    responsable_inscripto: 'Responsable Inscripto',
    monotributo: 'Monotributo',
    exento: 'Exento',
    consumidor_final: 'Consumidor Final',
    no_responsable: 'No Responsable',
  }
  return labels[condicion] || condicion
}

export const getTipoClienteColor = (tipo: TipoCliente): string => {
  const colors: Record<TipoCliente, string> = {
    particular: 'bg-blue-100 text-blue-800',
    empresa: 'bg-purple-100 text-purple-800',
    gobierno: 'bg-amber-100 text-amber-800',
    constructora: 'bg-orange-100 text-orange-800',
    consorcio: 'bg-teal-100 text-teal-800',
    otro: 'bg-gray-100 text-gray-800',
  }
  return colors[tipo] || 'bg-gray-100 text-gray-800'
}

export const formatCUIT = (cuit?: string): string => {
  if (!cuit) return '-'
  // Formato: XX-XXXXXXXX-X
  const clean = cuit.replace(/\D/g, '')
  if (clean.length !== 11) return cuit
  return `${clean.slice(0, 2)}-${clean.slice(2, 10)}-${clean.slice(10)}`
}
