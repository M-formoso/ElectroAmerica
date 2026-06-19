import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Plus,
  Search,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Wallet,
  Users,
  CreditCard,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  MoreVertical,
  Edit,
  Trash2,
  Ban,
  Building2,
  Calendar,
  FileText,
  Receipt,
  PiggyBank,
  ListOrdered,
  ClipboardCheck,
} from 'lucide-react'
import { ListasPrecioTab } from '@/components/finanzas/ListasPrecioTab'
import { PresupuestosTab } from '@/components/finanzas/PresupuestosTab'
import { FacturacionTab } from '@/components/finanzas/FacturacionTab'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from 'recharts'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin } from '@/store/auth'
import { formatCurrency, formatDate } from '@/lib/utils'
import { proyectosService } from '@/services/proyectos'
import { gastosService } from '@/services/gastos'
import * as finanzasService from '@/services/finanzas'
import type {
  Transaccion,
  TransaccionCreate,
  Cuenta,
  CuentaCreate,
  ClienteProveedor,
  ClienteProveedorCreate,
  TipoTransaccion,
  MetodoPago,
  TipoCuenta,
  TipoClienteProveedor,
} from '@/services/finanzas'

// Schemas
const transaccionSchema = z.object({
  tipo: z.enum(['ingreso', 'egreso']),
  concepto: z.string().min(1, 'Concepto requerido'),
  descripcion: z.string().optional(),
  monto: z.number().min(0.01, 'Monto debe ser mayor a 0'),
  fecha: z.string().min(1, 'Fecha requerida'),
  metodo_pago: z.enum(['efectivo', 'transferencia', 'tarjeta_debito', 'tarjeta_credito', 'cheque', 'mercado_pago', 'otro']).optional(),
  numero_comprobante: z.string().optional(),
  proyecto_id: z.string().optional(),
  categoria_id: z.string().optional(),
  cuenta_id: z.string().optional(),
  cliente_proveedor_id: z.string().optional(),
})

const cuentaSchema = z.object({
  nombre: z.string().min(1, 'Nombre requerido'),
  tipo: z.enum(['caja', 'banco', 'mercado_pago', 'otro']),
  descripcion: z.string().optional(),
  numero_cuenta: z.string().optional(),
  banco: z.string().optional(),
  cbu: z.string().optional(),
  alias: z.string().optional(),
  saldo_inicial: z.number().optional(),
})

const clienteProveedorSchema = z.object({
  tipo: z.enum(['cliente', 'proveedor', 'ambos']),
  razon_social: z.string().min(1, 'Razón social requerida'),
  nombre_fantasia: z.string().optional(),
  cuit: z.string().optional(),
  direccion: z.string().optional(),
  telefono: z.string().optional(),
  email: z.string().email().optional().or(z.literal('')),
  notas: z.string().optional(),
  condicion_iva: z.string().optional(),
})

type TransaccionForm = z.infer<typeof transaccionSchema>
type CuentaForm = z.infer<typeof cuentaSchema>
type ClienteProveedorForm = z.infer<typeof clienteProveedorSchema>

const COLORS = ['#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4']

export function FinanzasPage() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [search, setSearch] = useState('')
  const [tipoFilter, setTipoFilter] = useState<string>('todos')
  const [isCreateTransaccionOpen, setIsCreateTransaccionOpen] = useState(false)
  const [isCreateCuentaOpen, setIsCreateCuentaOpen] = useState(false)
  const [isCreateClienteProveedorOpen, setIsCreateClienteProveedorOpen] = useState(false)
  const [transaccionTipo, setTransaccionTipo] = useState<TipoTransaccion>('ingreso')

  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  // Queries
  const { data: dashboard, isLoading: loadingDashboard } = useQuery({
    queryKey: ['finanzas-dashboard'],
    queryFn: finanzasService.getDashboardFinanzas,
  })

  const { data: transacciones, isLoading: loadingTransacciones } = useQuery({
    queryKey: ['transacciones', tipoFilter],
    queryFn: () => finanzasService.getTransacciones({
      tipo: tipoFilter !== 'todos' ? tipoFilter as TipoTransaccion : undefined,
    }),
  })

  const { data: cuentas } = useQuery({
    queryKey: ['cuentas'],
    queryFn: () => finanzasService.getCuentas(),
  })

  const { data: clientesProveedores } = useQuery({
    queryKey: ['clientes-proveedores'],
    queryFn: () => finanzasService.getClientesProveedores(),
  })

  const { data: proyectos } = useQuery({
    queryKey: ['proyectos'],
    queryFn: () => proyectosService.getProyectos(),
  })

  const { data: categorias } = useQuery({
    queryKey: ['categorias-gasto'],
    queryFn: gastosService.getCategorias,
  })

  const { data: resumenMensual } = useQuery({
    queryKey: ['resumen-mensual'],
    queryFn: () => finanzasService.getResumenMensual(),
  })

  // Mutations
  const createTransaccionMutation = useMutation({
    mutationFn: finanzasService.createTransaccion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transacciones'] })
      queryClient.invalidateQueries({ queryKey: ['finanzas-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cuentas'] })
      toast({ title: 'Transacción registrada correctamente' })
      setIsCreateTransaccionOpen(false)
      transaccionForm.reset()
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al registrar transacción' })
    },
  })

  const deleteTransaccionMutation = useMutation({
    mutationFn: finanzasService.deleteTransaccion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transacciones'] })
      queryClient.invalidateQueries({ queryKey: ['finanzas-dashboard'] })
      toast({ title: 'Transacción eliminada' })
    },
  })

  const anularTransaccionMutation = useMutation({
    mutationFn: finanzasService.anularTransaccion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transacciones'] })
      queryClient.invalidateQueries({ queryKey: ['finanzas-dashboard'] })
      toast({ title: 'Transacción anulada' })
    },
  })

  const createCuentaMutation = useMutation({
    mutationFn: finanzasService.createCuenta,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cuentas'] })
      toast({ title: 'Cuenta creada correctamente' })
      setIsCreateCuentaOpen(false)
      cuentaForm.reset()
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al crear cuenta' })
    },
  })

  const deleteCuentaMutation = useMutation({
    mutationFn: finanzasService.deleteCuenta,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cuentas'] })
      toast({ title: 'Cuenta eliminada' })
    },
  })

  const createClienteProveedorMutation = useMutation({
    mutationFn: finanzasService.createClienteProveedor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientes-proveedores'] })
      toast({ title: 'Cliente/Proveedor creado correctamente' })
      setIsCreateClienteProveedorOpen(false)
      clienteProveedorForm.reset()
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al crear cliente/proveedor' })
    },
  })

  const deleteClienteProveedorMutation = useMutation({
    mutationFn: finanzasService.deleteClienteProveedor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientes-proveedores'] })
      toast({ title: 'Cliente/Proveedor eliminado' })
    },
  })

  // Forms
  const transaccionForm = useForm<TransaccionForm>({
    resolver: zodResolver(transaccionSchema),
    defaultValues: {
      tipo: 'ingreso',
      fecha: new Date().toISOString().split('T')[0],
      metodo_pago: 'efectivo',
    },
  })

  const cuentaForm = useForm<CuentaForm>({
    resolver: zodResolver(cuentaSchema),
    defaultValues: {
      tipo: 'caja',
      saldo_inicial: 0,
    },
  })

  const clienteProveedorForm = useForm<ClienteProveedorForm>({
    resolver: zodResolver(clienteProveedorSchema),
    defaultValues: {
      tipo: 'cliente',
    },
  })

  const onSubmitTransaccion = (data: TransaccionForm) => {
    createTransaccionMutation.mutate({
      ...data,
      proyecto_id: data.proyecto_id || undefined,
      categoria_id: data.categoria_id || undefined,
      cuenta_id: data.cuenta_id || undefined,
      cliente_proveedor_id: data.cliente_proveedor_id || undefined,
    } as TransaccionCreate)
  }

  const onSubmitCuenta = (data: CuentaForm) => {
    createCuentaMutation.mutate(data as CuentaCreate)
  }

  const onSubmitClienteProveedor = (data: ClienteProveedorForm) => {
    createClienteProveedorMutation.mutate({
      ...data,
      email: data.email || undefined,
    } as ClienteProveedorCreate)
  }

  const filteredTransacciones = transacciones?.filter((t) =>
    t.concepto.toLowerCase().includes(search.toLowerCase())
  )

  const openCreateTransaccion = (tipo: TipoTransaccion) => {
    setTransaccionTipo(tipo)
    transaccionForm.setValue('tipo', tipo)
    setIsCreateTransaccionOpen(true)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Finanzas</h1>
          <p className="text-muted-foreground">
            Gestión completa de ingresos, egresos y balances
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => openCreateTransaccion('egreso')}>
            <ArrowDownRight className="h-4 w-4 mr-2 text-red-500" />
            Registrar Egreso
          </Button>
          <Button onClick={() => openCreateTransaccion('ingreso')}>
            <ArrowUpRight className="h-4 w-4 mr-2" />
            Registrar Ingreso
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-8">
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="transacciones" className="flex items-center gap-2">
            <Receipt className="h-4 w-4" />
            <span className="hidden sm:inline">Transacciones</span>
          </TabsTrigger>
          <TabsTrigger value="cuentas" className="flex items-center gap-2">
            <Wallet className="h-4 w-4" />
            <span className="hidden sm:inline">Cuentas</span>
          </TabsTrigger>
          <TabsTrigger value="clientes" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">Clientes/Prov.</span>
          </TabsTrigger>
          <TabsTrigger value="reportes" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            <span className="hidden sm:inline">Reportes</span>
          </TabsTrigger>
          <TabsTrigger value="listas-precio" className="flex items-center gap-2">
            <ListOrdered className="h-4 w-4" />
            <span className="hidden sm:inline">Listas precio</span>
          </TabsTrigger>
          <TabsTrigger value="presupuestos" className="flex items-center gap-2">
            <PiggyBank className="h-4 w-4" />
            <span className="hidden sm:inline">Presupuestos</span>
          </TabsTrigger>
          <TabsTrigger value="facturacion" className="flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4" />
            <span className="hidden sm:inline">Facturación</span>
          </TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          {/* Stats cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Ingresos del Mes</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(dashboard?.total_ingresos_mes || 0)}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Egresos del Mes</CardTitle>
                <TrendingDown className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {formatCurrency(dashboard?.total_egresos_mes || 0)}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Balance del Mes</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${(dashboard?.balance_mes || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(dashboard?.balance_mes || 0)}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Saldo en Cuentas</CardTitle>
                <Wallet className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(dashboard?.saldo_total_cuentas || 0)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {dashboard?.transacciones_pendientes || 0} transacciones pendientes
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Flujo de caja */}
            <Card>
              <CardHeader>
                <CardTitle>Flujo de Caja</CardTitle>
                <CardDescription>Evolución diaria del mes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  {resumenMensual?.flujo_caja_diario && resumenMensual.flujo_caja_diario.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={resumenMensual.flujo_caja_diario}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                          dataKey="fecha"
                          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                          tickFormatter={(v) => new Date(v).getDate().toString()}
                        />
                        <YAxis
                          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                        />
                        <Tooltip
                          formatter={(value) => [formatCurrency(Number(value)), '']}
                          labelFormatter={(label) => formatDate(label)}
                        />
                        <Legend />
                        <Line type="monotone" dataKey="ingresos" name="Ingresos" stroke="#10b981" strokeWidth={2} />
                        <Line type="monotone" dataKey="egresos" name="Egresos" stroke="#ef4444" strokeWidth={2} />
                        <Line type="monotone" dataKey="saldo_final" name="Saldo" stroke="#3b82f6" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                      No hay datos de flujo de caja
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Egresos por categoría */}
            <Card>
              <CardHeader>
                <CardTitle>Egresos por Categoría</CardTitle>
                <CardDescription>Distribución del mes actual</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  {dashboard?.top_categorias_egreso && dashboard.top_categorias_egreso.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={dashboard.top_categorias_egreso}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="total"
                          nameKey="nombre"
                          label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                          labelLine={false}
                        >
                          {dashboard.top_categorias_egreso.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value) => [formatCurrency(Number(value)), 'Total']}
                        />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                      No hay datos de egresos
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Cuentas y últimas transacciones */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Saldo por cuentas */}
            <Card>
              <CardHeader>
                <CardTitle>Saldo por Cuenta</CardTitle>
                <CardDescription>Estado actual de las cuentas</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[250px]">
                  <div className="space-y-4">
                    {dashboard?.cuentas?.map((cuenta) => (
                      <div key={cuenta.id} className="flex items-center justify-between p-3 rounded-lg border">
                        <div className="flex items-center gap-3">
                          {cuenta.tipo === 'banco' ? (
                            <Building2 className="h-5 w-5 text-blue-500" />
                          ) : cuenta.tipo === 'mercado_pago' ? (
                            <CreditCard className="h-5 w-5 text-sky-500" />
                          ) : (
                            <PiggyBank className="h-5 w-5 text-green-500" />
                          )}
                          <div>
                            <p className="font-medium">{cuenta.nombre}</p>
                            <p className="text-xs text-muted-foreground">
                              {finanzasService.getTipoCuentaLabel(cuenta.tipo)}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-bold ${cuenta.saldo_actual >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(cuenta.saldo_actual)}
                          </p>
                        </div>
                      </div>
                    ))}
                    {(!dashboard?.cuentas || dashboard.cuentas.length === 0) && (
                      <p className="text-center text-muted-foreground py-4">
                        No hay cuentas registradas
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Últimas transacciones */}
            <Card>
              <CardHeader>
                <CardTitle>Últimas Transacciones</CardTitle>
                <CardDescription>Movimientos recientes</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[250px]">
                  <div className="space-y-3">
                    {dashboard?.ultimas_transacciones?.map((t) => (
                      <div key={t.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-full ${t.tipo === 'ingreso' ? 'bg-green-100' : 'bg-red-100'}`}>
                            {t.tipo === 'ingreso' ? (
                              <ArrowUpRight className="h-4 w-4 text-green-600" />
                            ) : (
                              <ArrowDownRight className="h-4 w-4 text-red-600" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{t.concepto}</p>
                            <p className="text-xs text-muted-foreground">
                              {formatDate(t.fecha)} • {t.cuenta_nombre || 'Sin cuenta'}
                            </p>
                          </div>
                        </div>
                        <p className={`font-bold ${t.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'}`}>
                          {t.tipo === 'ingreso' ? '+' : '-'}{formatCurrency(t.monto)}
                        </p>
                      </div>
                    ))}
                    {(!dashboard?.ultimas_transacciones || dashboard.ultimas_transacciones.length === 0) && (
                      <p className="text-center text-muted-foreground py-4">
                        No hay transacciones recientes
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Transacciones Tab */}
        <TabsContent value="transacciones" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar transacciones..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={tipoFilter} onValueChange={setTipoFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos</SelectItem>
                <SelectItem value="ingreso">Ingresos</SelectItem>
                <SelectItem value="egreso">Egresos</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Concepto</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead>Cuenta</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Monto</TableHead>
                  <TableHead className="w-[80px]">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadingTransacciones ? (
                  [...Array(5)].map((_, i) => (
                    <TableRow key={i}>
                      {[...Array(8)].map((_, j) => (
                        <TableCell key={j}>
                          <div className="h-4 bg-muted rounded animate-pulse" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : filteredTransacciones?.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      No se encontraron transacciones
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredTransacciones?.map((transaccion) => (
                    <TableRow key={transaccion.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          {formatDate(transaccion.fecha)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={transaccion.tipo === 'ingreso' ? 'default' : 'destructive'}>
                          {transaccion.tipo === 'ingreso' ? 'Ingreso' : 'Egreso'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{transaccion.concepto}</p>
                          {transaccion.numero_comprobante && (
                            <p className="text-xs text-muted-foreground">
                              {transaccion.numero_comprobante}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {transaccion.categoria_nombre || <span className="text-muted-foreground">-</span>}
                      </TableCell>
                      <TableCell>
                        {transaccion.cuenta_nombre || <span className="text-muted-foreground">-</span>}
                      </TableCell>
                      <TableCell>
                        <Badge className={finanzasService.getEstadoTransaccionColor(transaccion.estado)}>
                          {finanzasService.getEstadoTransaccionLabel(transaccion.estado)}
                        </Badge>
                      </TableCell>
                      <TableCell className={`text-right font-bold ${transaccion.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'}`}>
                        {transaccion.tipo === 'ingreso' ? '+' : '-'}{formatCurrency(transaccion.monto)}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {transaccion.comprobante_url && (
                              <DropdownMenuItem asChild>
                                <a href={transaccion.comprobante_url} target="_blank" rel="noopener">
                                  <FileText className="h-4 w-4 mr-2" />
                                  Ver comprobante
                                </a>
                              </DropdownMenuItem>
                            )}
                            {isAdmin && transaccion.estado === 'confirmada' && (
                              <DropdownMenuItem
                                onClick={() => anularTransaccionMutation.mutate(transaccion.id)}
                              >
                                <Ban className="h-4 w-4 mr-2" />
                                Anular
                              </DropdownMenuItem>
                            )}
                            {isAdmin && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={() => deleteTransaccionMutation.mutate(transaccion.id)}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Eliminar
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        {/* Cuentas Tab */}
        <TabsContent value="cuentas" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setIsCreateCuentaOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Nueva Cuenta
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {cuentas?.map((cuenta) => (
              <Card key={cuenta.id}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <div className="flex items-center gap-3">
                    {cuenta.tipo === 'banco' ? (
                      <Building2 className="h-6 w-6 text-blue-500" />
                    ) : cuenta.tipo === 'mercado_pago' ? (
                      <CreditCard className="h-6 w-6 text-sky-500" />
                    ) : (
                      <PiggyBank className="h-6 w-6 text-green-500" />
                    )}
                    <div>
                      <CardTitle className="text-lg">{cuenta.nombre}</CardTitle>
                      <CardDescription>
                        {finanzasService.getTipoCuentaLabel(cuenta.tipo)}
                        {cuenta.banco && ` • ${cuenta.banco}`}
                      </CardDescription>
                    </div>
                  </div>
                  {isAdmin && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Edit className="h-4 w-4 mr-2" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => deleteCuentaMutation.mutate(cuenta.id)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Eliminar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </CardHeader>
                <CardContent>
                  <div className={`text-3xl font-bold ${cuenta.saldo_actual >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(cuenta.saldo_actual)}
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Ingresos</p>
                      <p className="font-medium text-green-600">+{formatCurrency(cuenta.total_ingresos)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Egresos</p>
                      <p className="font-medium text-red-600">-{formatCurrency(cuenta.total_egresos)}</p>
                    </div>
                  </div>
                  {cuenta.alias && (
                    <p className="mt-3 text-xs text-muted-foreground">
                      Alias: {cuenta.alias}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
            {(!cuentas || cuentas.length === 0) && (
              <Card className="col-span-full">
                <CardContent className="py-8 text-center text-muted-foreground">
                  No hay cuentas registradas. Crea una para empezar.
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Clientes/Proveedores Tab */}
        <TabsContent value="clientes" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setIsCreateClienteProveedorOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Nuevo Cliente/Proveedor
            </Button>
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Razón Social</TableHead>
                  <TableHead>CUIT</TableHead>
                  <TableHead>Contacto</TableHead>
                  <TableHead>Cond. IVA</TableHead>
                  <TableHead className="text-right">Saldo Cta. Cte.</TableHead>
                  <TableHead className="w-[80px]">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {clientesProveedores?.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No hay clientes/proveedores registrados
                    </TableCell>
                  </TableRow>
                ) : (
                  clientesProveedores?.map((cp) => (
                    <TableRow key={cp.id}>
                      <TableCell>
                        <Badge variant={cp.tipo === 'cliente' ? 'default' : cp.tipo === 'proveedor' ? 'secondary' : 'outline'}>
                          {finanzasService.getTipoClienteProveedorLabel(cp.tipo)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{cp.razon_social}</p>
                          {cp.nombre_fantasia && (
                            <p className="text-xs text-muted-foreground">{cp.nombre_fantasia}</p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{cp.cuit || '-'}</TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {cp.email && <p>{cp.email}</p>}
                          {cp.telefono && <p className="text-muted-foreground">{cp.telefono}</p>}
                        </div>
                      </TableCell>
                      <TableCell>{cp.condicion_iva || '-'}</TableCell>
                      <TableCell className={`text-right font-bold ${cp.saldo_cuenta_corriente >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(cp.saldo_cuenta_corriente)}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <FileText className="h-4 w-4 mr-2" />
                              Ver cuenta corriente
                            </DropdownMenuItem>
                            {isAdmin && (
                              <>
                                <DropdownMenuItem>
                                  <Edit className="h-4 w-4 mr-2" />
                                  Editar
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={() => deleteClienteProveedorMutation.mutate(cp.id)}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Eliminar
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        {/* Reportes Tab */}
        <TabsContent value="reportes" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Ingresos Totales</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(resumenMensual?.ingresos_totales || 0)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {resumenMensual?.periodo}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Egresos Totales</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {formatCurrency(resumenMensual?.egresos_totales || 0)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {resumenMensual?.periodo}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Balance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${(resumenMensual?.balance || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(resumenMensual?.balance || 0)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {resumenMensual?.periodo}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Variación vs Anterior</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold flex items-center gap-2 ${(resumenMensual?.variacion_vs_anterior || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {(resumenMensual?.variacion_vs_anterior || 0) >= 0 ? (
                    <TrendingUp className="h-5 w-5" />
                  ) : (
                    <TrendingDown className="h-5 w-5" />
                  )}
                  {Math.abs(resumenMensual?.variacion_vs_anterior || 0).toFixed(1)}%
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Top categorías ingreso */}
            <Card>
              <CardHeader>
                <CardTitle>Top Categorías de Ingreso</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {resumenMensual?.top_categorias_ingreso?.map((cat, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[i % COLORS.length] }}
                        />
                        <span>{cat.nombre}</span>
                      </div>
                      <span className="font-medium text-green-600">
                        {formatCurrency(cat.total)}
                      </span>
                    </div>
                  ))}
                  {(!resumenMensual?.top_categorias_ingreso || resumenMensual.top_categorias_ingreso.length === 0) && (
                    <p className="text-center text-muted-foreground py-4">
                      No hay datos
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Top categorías egreso */}
            <Card>
              <CardHeader>
                <CardTitle>Top Categorías de Egreso</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {resumenMensual?.top_categorias_egreso?.map((cat, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[i % COLORS.length] }}
                        />
                        <span>{cat.nombre}</span>
                      </div>
                      <span className="font-medium text-red-600">
                        {formatCurrency(cat.total)}
                      </span>
                    </div>
                  ))}
                  {(!resumenMensual?.top_categorias_egreso || resumenMensual.top_categorias_egreso.length === 0) && (
                    <p className="text-center text-muted-foreground py-4">
                      No hay datos
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="listas-precio" className="space-y-4">
          <ListasPrecioTab />
        </TabsContent>

        <TabsContent value="presupuestos" className="space-y-4">
          <PresupuestosTab />
        </TabsContent>

        <TabsContent value="facturacion" className="space-y-4">
          <FacturacionTab />
        </TabsContent>
      </Tabs>

      {/* Dialog: Nueva Transacción */}
      <Dialog open={isCreateTransaccionOpen} onOpenChange={setIsCreateTransaccionOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {transaccionTipo === 'ingreso' ? 'Registrar Ingreso' : 'Registrar Egreso'}
            </DialogTitle>
            <DialogDescription>
              Ingresa los detalles de la transacción
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={transaccionForm.handleSubmit(onSubmitTransaccion)} className="space-y-4">
            <div className="space-y-2">
              <Label>Concepto *</Label>
              <Input
                {...transaccionForm.register('concepto')}
                placeholder="Ej: Pago de factura #123"
              />
              {transaccionForm.formState.errors.concepto && (
                <p className="text-sm text-destructive">{transaccionForm.formState.errors.concepto.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Monto *</Label>
                <Input
                  type="number"
                  step="0.01"
                  {...transaccionForm.register('monto', { valueAsNumber: true })}
                  placeholder="0.00"
                />
                {transaccionForm.formState.errors.monto && (
                  <p className="text-sm text-destructive">{transaccionForm.formState.errors.monto.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label>Fecha *</Label>
                <Input type="date" {...transaccionForm.register('fecha')} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Método de Pago</Label>
                <Select
                  defaultValue="efectivo"
                  onValueChange={(v) => transaccionForm.setValue('metodo_pago', v as MetodoPago)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="efectivo">Efectivo</SelectItem>
                    <SelectItem value="transferencia">Transferencia</SelectItem>
                    <SelectItem value="tarjeta_debito">Tarjeta Débito</SelectItem>
                    <SelectItem value="tarjeta_credito">Tarjeta Crédito</SelectItem>
                    <SelectItem value="cheque">Cheque</SelectItem>
                    <SelectItem value="mercado_pago">Mercado Pago</SelectItem>
                    <SelectItem value="otro">Otro</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Cuenta</Label>
                <Select onValueChange={(v) => transaccionForm.setValue('cuenta_id', v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar cuenta" />
                  </SelectTrigger>
                  <SelectContent>
                    {cuentas?.map((cuenta) => (
                      <SelectItem key={cuenta.id} value={cuenta.id}>
                        {cuenta.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Categoría</Label>
                <Select onValueChange={(v) => transaccionForm.setValue('categoria_id', v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar categoría" />
                  </SelectTrigger>
                  <SelectContent>
                    {categorias?.map((cat) => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {cat.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Proyecto</Label>
                <Select onValueChange={(v) => transaccionForm.setValue('proyecto_id', v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar proyecto" />
                  </SelectTrigger>
                  <SelectContent>
                    {proyectos?.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Cliente/Proveedor</Label>
              <Select onValueChange={(v) => transaccionForm.setValue('cliente_proveedor_id', v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar cliente/proveedor" />
                </SelectTrigger>
                <SelectContent>
                  {clientesProveedores?.map((cp) => (
                    <SelectItem key={cp.id} value={cp.id}>
                      {cp.razon_social}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Número de Comprobante</Label>
              <Input
                {...transaccionForm.register('numero_comprobante')}
                placeholder="Ej: FAC-A-0001-00001234"
              />
            </div>

            <div className="space-y-2">
              <Label>Descripción</Label>
              <Textarea
                {...transaccionForm.register('descripcion')}
                placeholder="Detalles adicionales..."
                rows={2}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreateTransaccionOpen(false)}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={createTransaccionMutation.isPending}>
                Registrar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Nueva Cuenta */}
      <Dialog open={isCreateCuentaOpen} onOpenChange={setIsCreateCuentaOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Nueva Cuenta</DialogTitle>
            <DialogDescription>
              Crea una nueva cuenta para gestionar tus finanzas
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={cuentaForm.handleSubmit(onSubmitCuenta)} className="space-y-4">
            <div className="space-y-2">
              <Label>Nombre *</Label>
              <Input
                {...cuentaForm.register('nombre')}
                placeholder="Ej: Caja Principal"
              />
              {cuentaForm.formState.errors.nombre && (
                <p className="text-sm text-destructive">{cuentaForm.formState.errors.nombre.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tipo *</Label>
                <Select
                  defaultValue="caja"
                  onValueChange={(v) => cuentaForm.setValue('tipo', v as TipoCuenta)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="caja">Caja</SelectItem>
                    <SelectItem value="banco">Banco</SelectItem>
                    <SelectItem value="mercado_pago">Mercado Pago</SelectItem>
                    <SelectItem value="otro">Otro</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Saldo Inicial</Label>
                <Input
                  type="number"
                  step="0.01"
                  {...cuentaForm.register('saldo_inicial', { valueAsNumber: true })}
                  placeholder="0.00"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Banco</Label>
              <Input
                {...cuentaForm.register('banco')}
                placeholder="Ej: Banco Nación"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>N° de Cuenta</Label>
                <Input
                  {...cuentaForm.register('numero_cuenta')}
                  placeholder="Ej: 1234567890"
                />
              </div>

              <div className="space-y-2">
                <Label>Alias</Label>
                <Input
                  {...cuentaForm.register('alias')}
                  placeholder="Ej: mi.alias.mp"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>CBU</Label>
              <Input
                {...cuentaForm.register('cbu')}
                placeholder="22 dígitos"
              />
            </div>

            <div className="space-y-2">
              <Label>Descripción</Label>
              <Input
                {...cuentaForm.register('descripcion')}
                placeholder="Descripción opcional"
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreateCuentaOpen(false)}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={createCuentaMutation.isPending}>
                Crear Cuenta
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Nuevo Cliente/Proveedor */}
      <Dialog open={isCreateClienteProveedorOpen} onOpenChange={setIsCreateClienteProveedorOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Nuevo Cliente/Proveedor</DialogTitle>
            <DialogDescription>
              Registra un nuevo cliente o proveedor
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={clienteProveedorForm.handleSubmit(onSubmitClienteProveedor)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tipo *</Label>
                <Select
                  defaultValue="cliente"
                  onValueChange={(v) => clienteProveedorForm.setValue('tipo', v as TipoClienteProveedor)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cliente">Cliente</SelectItem>
                    <SelectItem value="proveedor">Proveedor</SelectItem>
                    <SelectItem value="ambos">Ambos</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Condición IVA</Label>
                <Select onValueChange={(v) => clienteProveedorForm.setValue('condicion_iva', v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Responsable Inscripto">Responsable Inscripto</SelectItem>
                    <SelectItem value="Monotributo">Monotributo</SelectItem>
                    <SelectItem value="Exento">Exento</SelectItem>
                    <SelectItem value="Consumidor Final">Consumidor Final</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Razón Social *</Label>
              <Input
                {...clienteProveedorForm.register('razon_social')}
                placeholder="Nombre o razón social"
              />
              {clienteProveedorForm.formState.errors.razon_social && (
                <p className="text-sm text-destructive">{clienteProveedorForm.formState.errors.razon_social.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nombre Fantasía</Label>
                <Input
                  {...clienteProveedorForm.register('nombre_fantasia')}
                  placeholder="Nombre comercial"
                />
              </div>

              <div className="space-y-2">
                <Label>CUIT</Label>
                <Input
                  {...clienteProveedorForm.register('cuit')}
                  placeholder="XX-XXXXXXXX-X"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Dirección</Label>
              <Input
                {...clienteProveedorForm.register('direccion')}
                placeholder="Dirección fiscal"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  {...clienteProveedorForm.register('email')}
                  placeholder="email@ejemplo.com"
                />
              </div>

              <div className="space-y-2">
                <Label>Teléfono</Label>
                <Input
                  {...clienteProveedorForm.register('telefono')}
                  placeholder="+54 11 1234-5678"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Notas</Label>
              <Textarea
                {...clienteProveedorForm.register('notas')}
                placeholder="Notas adicionales..."
                rows={2}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreateClienteProveedorOpen(false)}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={createClienteProveedorMutation.isPending}>
                Crear
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
