import api from './api'

// ============ TYPES ============

export type TipoTransaccion = 'ingreso' | 'egreso'
export type MetodoPago = 'efectivo' | 'transferencia' | 'tarjeta_debito' | 'tarjeta_credito' | 'cheque' | 'mercado_pago' | 'otro'
export type EstadoTransaccion = 'pendiente' | 'confirmada' | 'anulada'
export type TipoCuenta = 'caja' | 'banco' | 'mercado_pago' | 'otro'
export type TipoClienteProveedor = 'cliente' | 'proveedor' | 'ambos'

export interface Transaccion {
  id: string
  tipo: TipoTransaccion
  tipo_ingreso_id?: string | null
  tipo_ingreso_nombre?: string | null
  concepto: string
  descripcion?: string
  monto: number
  fecha: string
  metodo_pago: MetodoPago
  referencia_pago?: string
  estado: EstadoTransaccion
  numero_comprobante?: string
  tipo_comprobante?: string
  comprobante_url?: string
  proyecto_id?: string
  categoria_id?: string
  cuenta_id?: string
  cliente_proveedor_id?: string
  creado_por_id: string
  activo: boolean
  created_at: string
  proyecto_nombre?: string
  categoria_nombre?: string
  cuenta_nombre?: string
  cliente_proveedor_nombre?: string
  creador_nombre?: string
}

export interface TransaccionCreate {
  tipo: TipoTransaccion
  tipo_ingreso_id?: string | null
  concepto: string
  descripcion?: string
  monto: number
  fecha: string
  metodo_pago?: MetodoPago
  referencia_pago?: string
  estado?: EstadoTransaccion
  numero_comprobante?: string
  tipo_comprobante?: string
  comprobante_url?: string
  proyecto_id?: string
  categoria_id?: string
  cuenta_id?: string
  cliente_proveedor_id?: string
}

export interface TransaccionUpdate {
  tipo?: TipoTransaccion
  tipo_ingreso_id?: string | null
  concepto?: string
  descripcion?: string
  monto?: number
  fecha?: string
  metodo_pago?: MetodoPago
  referencia_pago?: string
  estado?: EstadoTransaccion
  numero_comprobante?: string
  tipo_comprobante?: string
  comprobante_url?: string
  proyecto_id?: string
  categoria_id?: string
  cuenta_id?: string
  cliente_proveedor_id?: string
}

export interface Cuenta {
  id: string
  nombre: string
  tipo: TipoCuenta
  descripcion?: string
  numero_cuenta?: string
  banco?: string
  cbu?: string
  alias?: string
  saldo_inicial: number
  activo: boolean
  saldo_actual: number
  total_ingresos: number
  total_egresos: number
}

export interface CuentaCreate {
  nombre: string
  tipo?: TipoCuenta
  descripcion?: string
  numero_cuenta?: string
  banco?: string
  cbu?: string
  alias?: string
  saldo_inicial?: number
}

export interface CuentaUpdate {
  nombre?: string
  tipo?: TipoCuenta
  descripcion?: string
  numero_cuenta?: string
  banco?: string
  cbu?: string
  alias?: string
  saldo_inicial?: number
}

export interface ClienteProveedor {
  id: string
  tipo: TipoClienteProveedor
  razon_social: string
  nombre_fantasia?: string
  cuit?: string
  direccion?: string
  telefono?: string
  email?: string
  notas?: string
  condicion_iva?: string
  usuario_id?: string
  activo: boolean
  saldo_cuenta_corriente: number
  total_facturado: number
}

export interface ClienteProveedorCreate {
  tipo?: TipoClienteProveedor
  razon_social: string
  nombre_fantasia?: string
  cuit?: string
  direccion?: string
  telefono?: string
  email?: string
  notas?: string
  condicion_iva?: string
  usuario_id?: string
}

export interface ClienteProveedorUpdate {
  tipo?: TipoClienteProveedor
  razon_social?: string
  nombre_fantasia?: string
  cuit?: string
  direccion?: string
  telefono?: string
  email?: string
  notas?: string
  condicion_iva?: string
  usuario_id?: string
}

export interface Presupuesto {
  id: string
  nombre: string
  descripcion?: string
  monto_total: number
  fecha_inicio?: string
  fecha_fin?: string
  proyecto_id?: string
  categoria_id?: string
  activo: boolean
  monto_ejecutado: number
  porcentaje_ejecutado: number
  saldo_disponible: number
}

export interface PresupuestoCreate {
  nombre: string
  descripcion?: string
  monto_total: number
  fecha_inicio?: string
  fecha_fin?: string
  proyecto_id?: string
  categoria_id?: string
}

export interface PresupuestoUpdate {
  nombre?: string
  descripcion?: string
  monto_total?: number
  fecha_inicio?: string
  fecha_fin?: string
  proyecto_id?: string
  categoria_id?: string
}

export interface DashboardFinanzas {
  total_ingresos_mes: number
  total_egresos_mes: number
  balance_mes: number
  saldo_total_cuentas: number
  transacciones_pendientes: number
  top_categorias_egreso: { nombre: string; total: number }[]
  ultimas_transacciones: Transaccion[]
  cuentas: Cuenta[]
}

export interface BalanceGeneral {
  fecha_desde: string
  fecha_hasta: string
  total_ingresos: number
  total_egresos: number
  balance: number
  ingresos_por_categoria: { nombre: string; total: number }[]
  egresos_por_categoria: { nombre: string; total: number }[]
  ingresos_por_metodo_pago: { metodo: string; total: number }[]
  egresos_por_metodo_pago: { metodo: string; total: number }[]
}

export interface FlujoCaja {
  fecha: string
  saldo_inicial: number
  ingresos: number
  egresos: number
  saldo_final: number
}

export interface ResumenMensual {
  periodo: string
  ingresos_totales: number
  egresos_totales: number
  balance: number
  variacion_vs_anterior: number
  top_categorias_ingreso: { nombre: string; total: number }[]
  top_categorias_egreso: { nombre: string; total: number }[]
  flujo_caja_diario: FlujoCaja[]
  cuentas: Cuenta[]
}

export interface CuentaCorriente {
  cliente_proveedor: ClienteProveedor
  transacciones: Transaccion[]
  saldo: number
}

// ============ API FUNCTIONS ============

// Dashboard
export const getDashboardFinanzas = async (): Promise<DashboardFinanzas> => {
  const response = await api.get('/finanzas/dashboard')
  return response.data
}

// Transacciones
export const getTransacciones = async (params?: {
  tipo?: TipoTransaccion
  fecha_desde?: string
  fecha_hasta?: string
  proyecto_id?: string
  categoria_id?: string
  cuenta_id?: string
  cliente_proveedor_id?: string
  estado?: EstadoTransaccion
  skip?: number
  limit?: number
}): Promise<Transaccion[]> => {
  const response = await api.get('/finanzas/transacciones', { params })
  return response.data
}

export const getTransaccion = async (id: string): Promise<Transaccion> => {
  const response = await api.get(`/finanzas/transacciones/${id}`)
  return response.data
}

export const createTransaccion = async (data: TransaccionCreate): Promise<Transaccion> => {
  const response = await api.post('/finanzas/transacciones', data)
  return response.data
}

export const updateTransaccion = async (id: string, data: TransaccionUpdate): Promise<Transaccion> => {
  const response = await api.put(`/finanzas/transacciones/${id}`, data)
  return response.data
}

export const deleteTransaccion = async (id: string): Promise<void> => {
  await api.delete(`/finanzas/transacciones/${id}`)
}

export const anularTransaccion = async (id: string): Promise<Transaccion> => {
  const response = await api.post(`/finanzas/transacciones/${id}/anular`)
  return response.data
}

// Cuentas
export const getCuentas = async (tipo?: TipoCuenta): Promise<Cuenta[]> => {
  const response = await api.get('/finanzas/cuentas', { params: { tipo } })
  return response.data
}

export const getCuenta = async (id: string): Promise<Cuenta> => {
  const response = await api.get(`/finanzas/cuentas/${id}`)
  return response.data
}

export const createCuenta = async (data: CuentaCreate): Promise<Cuenta> => {
  const response = await api.post('/finanzas/cuentas', data)
  return response.data
}

export const updateCuenta = async (id: string, data: CuentaUpdate): Promise<Cuenta> => {
  const response = await api.put(`/finanzas/cuentas/${id}`, data)
  return response.data
}

export const deleteCuenta = async (id: string): Promise<void> => {
  await api.delete(`/finanzas/cuentas/${id}`)
}

export interface MovimientoCuenta {
  id: string
  tipo: TipoTransaccion
  concepto: string
  descripcion?: string | null
  monto: number
  fecha: string
  metodo_pago?: MetodoPago | null
  referencia_pago?: string | null
  estado: EstadoTransaccion | string
  numero_comprobante?: string | null
  proyecto_nombre?: string | null
}

export interface MovimientosCuentaResponse {
  cuenta: Cuenta
  movimientos: MovimientoCuenta[]
}

export const getMovimientosCuenta = async (id: string, params?: {
  fecha_desde?: string
  fecha_hasta?: string
  skip?: number
  limit?: number
}): Promise<MovimientosCuentaResponse> => {
  const response = await api.get(`/finanzas/cuentas/${id}/movimientos`, { params })
  return response.data
}

// Clientes/Proveedores
export const getClientesProveedores = async (tipo?: TipoClienteProveedor): Promise<ClienteProveedor[]> => {
  const response = await api.get('/finanzas/clientes-proveedores', { params: { tipo } })
  return response.data
}

export const getClienteProveedor = async (id: string): Promise<ClienteProveedor> => {
  const response = await api.get(`/finanzas/clientes-proveedores/${id}`)
  return response.data
}

export const createClienteProveedor = async (data: ClienteProveedorCreate): Promise<ClienteProveedor> => {
  const response = await api.post('/finanzas/clientes-proveedores', data)
  return response.data
}

export const updateClienteProveedor = async (id: string, data: ClienteProveedorUpdate): Promise<ClienteProveedor> => {
  const response = await api.put(`/finanzas/clientes-proveedores/${id}`, data)
  return response.data
}

export const deleteClienteProveedor = async (id: string): Promise<void> => {
  await api.delete(`/finanzas/clientes-proveedores/${id}`)
}

export const getCuentaCorriente = async (id: string, params?: {
  fecha_desde?: string
  fecha_hasta?: string
}): Promise<CuentaCorriente> => {
  const response = await api.get(`/finanzas/clientes-proveedores/${id}/cuenta-corriente`, { params })
  return response.data
}

// Reportes
export const getBalanceGeneral = async (params: {
  fecha_desde: string
  fecha_hasta: string
  proyecto_id?: string
}): Promise<BalanceGeneral> => {
  const response = await api.get('/finanzas/balance', { params })
  return response.data
}

export const getFlujoCaja = async (params: {
  fecha_desde: string
  fecha_hasta: string
  cuenta_id?: string
}): Promise<FlujoCaja[]> => {
  const response = await api.get('/finanzas/flujo-caja', { params })
  return response.data
}

export const getResumenMensual = async (mes?: number, anio?: number): Promise<ResumenMensual> => {
  const response = await api.get('/finanzas/resumen-mensual', { params: { mes, anio } })
  return response.data
}

// Presupuestos
export const getPresupuestos = async (params?: {
  proyecto_id?: string
  categoria_id?: string
  skip?: number
  limit?: number
}): Promise<Presupuesto[]> => {
  const response = await api.get('/finanzas/presupuestos', { params })
  return response.data
}

export const getPresupuesto = async (id: string): Promise<Presupuesto> => {
  const response = await api.get(`/finanzas/presupuestos/${id}`)
  return response.data
}

export const createPresupuesto = async (data: PresupuestoCreate): Promise<Presupuesto> => {
  const response = await api.post('/finanzas/presupuestos', data)
  return response.data
}

export const updatePresupuesto = async (id: string, data: PresupuestoUpdate): Promise<Presupuesto> => {
  const response = await api.put(`/finanzas/presupuestos/${id}`, data)
  return response.data
}

export const deletePresupuesto = async (id: string): Promise<void> => {
  await api.delete(`/finanzas/presupuestos/${id}`)
}

// Helper functions
export const formatMonto = (monto: number): string => {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(monto)
}

export const getMetodoPagoLabel = (metodo: MetodoPago): string => {
  const labels: Record<MetodoPago, string> = {
    efectivo: 'Efectivo',
    transferencia: 'Transferencia',
    tarjeta_debito: 'Tarjeta de Débito',
    tarjeta_credito: 'Tarjeta de Crédito',
    cheque: 'Cheque',
    mercado_pago: 'Mercado Pago',
    otro: 'Otro',
  }
  return labels[metodo] || metodo
}

export const getTipoCuentaLabel = (tipo: TipoCuenta): string => {
  const labels: Record<TipoCuenta, string> = {
    caja: 'Caja',
    banco: 'Banco',
    mercado_pago: 'Mercado Pago',
    otro: 'Otro',
  }
  return labels[tipo] || tipo
}

export const getEstadoTransaccionLabel = (estado: EstadoTransaccion): string => {
  const labels: Record<EstadoTransaccion, string> = {
    pendiente: 'Pendiente',
    confirmada: 'Confirmada',
    anulada: 'Anulada',
  }
  return labels[estado] || estado
}

export const getEstadoTransaccionColor = (estado: EstadoTransaccion): string => {
  const colors: Record<EstadoTransaccion, string> = {
    pendiente: 'bg-yellow-100 text-yellow-800',
    confirmada: 'bg-green-100 text-green-800',
    anulada: 'bg-red-100 text-red-800',
  }
  return colors[estado] || 'bg-gray-100 text-gray-800'
}

export const getTipoClienteProveedorLabel = (tipo: TipoClienteProveedor): string => {
  const labels: Record<TipoClienteProveedor, string> = {
    cliente: 'Cliente',
    proveedor: 'Proveedor',
    ambos: 'Cliente y Proveedor',
  }
  return labels[tipo] || tipo
}
