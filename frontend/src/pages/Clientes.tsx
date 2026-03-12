import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Plus,
  Search,
  Users,
  Building2,
  Landmark,
  HardHat,
  Home,
  MoreVertical,
  Edit,
  Trash2,
  Eye,
  Phone,
  Mail,
  MapPin,
  CreditCard,
  AlertTriangle,
  UserPlus,
  Key,
  Copy,
  Check,
  Wallet,
  FileText,
  FolderKanban,
} from 'lucide-react'
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
import { Separator } from '@/components/ui/separator'
import { ViewToggle, type ViewMode } from '@/components/ui/view-toggle'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin } from '@/store/auth'
import { formatCurrency, formatDate } from '@/lib/utils'
import * as clientesService from '@/services/clientes'
import type {
  Cliente,
  ClienteCreate,
  ClienteUpdate,
  ClienteListItem,
  TipoCliente,
  CondicionIVA,
  EstadoCuentaCliente,
  UsuarioClienteResponse,
  ProyectoClienteResumen,
} from '@/services/clientes'

// Schema de validación
const clienteSchema = z.object({
  tipo: z.enum(['particular', 'empresa', 'gobierno', 'constructora', 'consorcio', 'otro']),
  razon_social: z.string().min(2, 'Razón social requerida'),
  nombre_fantasia: z.string().optional(),
  cuit: z.string().optional(),
  condicion_iva: z.enum(['responsable_inscripto', 'monotributo', 'exento', 'consumidor_final', 'no_responsable']),
  email: z.string().email().optional().or(z.literal('')),
  telefono: z.string().optional(),
  celular: z.string().optional(),
  contacto_nombre: z.string().optional(),
  contacto_cargo: z.string().optional(),
  direccion: z.string().optional(),
  ciudad: z.string().optional(),
  provincia: z.string().optional(),
  codigo_postal: z.string().optional(),
  descuento_general: z.number().min(0).max(100).optional(),
  limite_credito: z.number().min(0).optional(),
  dias_credito: z.number().min(0).optional(),
  enviar_notificaciones: z.boolean().optional(),
  notas: z.string().optional(),
  notas_internas: z.string().optional(),
})

const usuarioClienteSchema = z.object({
  email: z.string().email('Email inválido'),
  nombre: z.string().min(2, 'Nombre requerido'),
  apellido: z.string().optional(),
  telefono: z.string().optional(),
  password: z.string().optional(),
})

type ClienteForm = z.infer<typeof clienteSchema>
type UsuarioClienteForm = z.infer<typeof usuarioClienteSchema>

const TIPO_ICONS: Record<TipoCliente, React.ReactNode> = {
  particular: <Home className="h-4 w-4" />,
  empresa: <Building2 className="h-4 w-4" />,
  gobierno: <Landmark className="h-4 w-4" />,
  constructora: <HardHat className="h-4 w-4" />,
  consorcio: <Users className="h-4 w-4" />,
  otro: <Building2 className="h-4 w-4" />,
}

export function ClientesPage() {
  const [search, setSearch] = useState('')
  const [tipoFilter, setTipoFilter] = useState<string>('todos')
  const [conDeudaFilter, setConDeudaFilter] = useState<boolean | undefined>(undefined)
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [isUsuarioOpen, setIsUsuarioOpen] = useState(false)
  const [selectedCliente, setSelectedCliente] = useState<Cliente | null>(null)
  const [copiedPassword, setCopiedPassword] = useState(false)
  const [newPassword, setNewPassword] = useState<string | null>(null)

  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  // Queries
  const { data: clientes, isLoading } = useQuery({
    queryKey: ['clientes', tipoFilter, conDeudaFilter, search],
    queryFn: () => clientesService.getClientes({
      tipo: tipoFilter !== 'todos' ? tipoFilter as TipoCliente : undefined,
      con_deuda: conDeudaFilter,
      buscar: search || undefined,
    }),
  })

  const { data: estadisticas } = useQuery({
    queryKey: ['clientes-estadisticas'],
    queryFn: clientesService.getEstadisticasClientes,
  })

  const { data: clienteDetalle } = useQuery({
    queryKey: ['cliente', selectedCliente?.id],
    queryFn: () => selectedCliente ? clientesService.getClienteCompleto(selectedCliente.id) : null,
    enabled: !!selectedCliente && isDetailOpen,
  })

  const { data: estadoCuenta } = useQuery({
    queryKey: ['cliente-cuenta', selectedCliente?.id],
    queryFn: () => selectedCliente ? clientesService.getEstadoCuenta(selectedCliente.id) : null,
    enabled: !!selectedCliente && isDetailOpen,
  })

  const { data: usuarioCliente } = useQuery({
    queryKey: ['cliente-usuario', selectedCliente?.id],
    queryFn: () => selectedCliente ? clientesService.getUsuarioCliente(selectedCliente.id) : null,
    enabled: !!selectedCliente && isDetailOpen,
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: clientesService.createCliente,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
      queryClient.invalidateQueries({ queryKey: ['clientes-estadisticas'] })
      toast({ title: 'Cliente creado correctamente' })
      setIsCreateOpen(false)
      createForm.reset()
    },
    onError: (error: any) => {
      toast({ variant: 'destructive', title: error.response?.data?.detail || 'Error al crear cliente' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ClienteUpdate }) => clientesService.updateCliente(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
      queryClient.invalidateQueries({ queryKey: ['cliente', selectedCliente?.id] })
      toast({ title: 'Cliente actualizado correctamente' })
      setIsEditOpen(false)
    },
    onError: (error: any) => {
      toast({ variant: 'destructive', title: error.response?.data?.detail || 'Error al actualizar cliente' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: clientesService.deleteCliente,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
      queryClient.invalidateQueries({ queryKey: ['clientes-estadisticas'] })
      toast({ title: 'Cliente eliminado' })
      setIsDetailOpen(false)
    },
    onError: (error: any) => {
      toast({ variant: 'destructive', title: error.response?.data?.detail || 'Error al eliminar cliente' })
    },
  })

  const crearUsuarioMutation = useMutation({
    mutationFn: ({ clienteId, data }: { clienteId: string; data: any }) =>
      clientesService.crearUsuarioCliente(clienteId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['cliente-usuario', selectedCliente?.id] })
      setNewPassword(data.password_visible || null)
      toast({ title: 'Usuario creado correctamente' })
      setIsUsuarioOpen(false)
      usuarioForm.reset()
    },
    onError: (error: any) => {
      toast({ variant: 'destructive', title: error.response?.data?.detail || 'Error al crear usuario' })
    },
  })

  const resetPasswordMutation = useMutation({
    mutationFn: (clienteId: string) => clientesService.resetPasswordUsuario(clienteId),
    onSuccess: (data) => {
      setNewPassword(data.password)
      toast({ title: 'Contraseña reseteada' })
    },
  })

  // Forms
  const createForm = useForm<ClienteForm>({
    resolver: zodResolver(clienteSchema),
    defaultValues: {
      tipo: 'particular',
      condicion_iva: 'consumidor_final',
      provincia: 'Buenos Aires',
      enviar_notificaciones: true,
      descuento_general: 0,
      dias_credito: 0,
    },
  })

  const editForm = useForm<ClienteForm>({
    resolver: zodResolver(clienteSchema),
  })

  const usuarioForm = useForm<UsuarioClienteForm>({
    resolver: zodResolver(usuarioClienteSchema),
  })

  const onSubmitCreate = (data: ClienteForm) => {
    createMutation.mutate({
      ...data,
      email: data.email || undefined,
    } as ClienteCreate)
  }

  const onSubmitEdit = (data: ClienteForm) => {
    if (!selectedCliente) return
    updateMutation.mutate({
      id: selectedCliente.id,
      data: {
        ...data,
        email: data.email || undefined,
      } as ClienteUpdate,
    })
  }

  const onSubmitUsuario = (data: UsuarioClienteForm) => {
    if (!selectedCliente) return
    crearUsuarioMutation.mutate({
      clienteId: selectedCliente.id,
      data,
    })
  }

  const openDetail = (cliente: ClienteListItem) => {
    setSelectedCliente(cliente as any)
    setIsDetailOpen(true)
    setNewPassword(null)
  }

  const openEdit = () => {
    if (!clienteDetalle) return
    editForm.reset({
      tipo: clienteDetalle.tipo,
      razon_social: clienteDetalle.razon_social,
      nombre_fantasia: clienteDetalle.nombre_fantasia || '',
      cuit: clienteDetalle.cuit || '',
      condicion_iva: clienteDetalle.condicion_iva,
      email: clienteDetalle.email || '',
      telefono: clienteDetalle.telefono || '',
      celular: clienteDetalle.celular || '',
      contacto_nombre: clienteDetalle.contacto_nombre || '',
      contacto_cargo: clienteDetalle.contacto_cargo || '',
      direccion: clienteDetalle.direccion || '',
      ciudad: clienteDetalle.ciudad || '',
      provincia: clienteDetalle.provincia || 'Buenos Aires',
      codigo_postal: clienteDetalle.codigo_postal || '',
      descuento_general: clienteDetalle.descuento_general,
      limite_credito: clienteDetalle.limite_credito || undefined,
      dias_credito: clienteDetalle.dias_credito,
      enviar_notificaciones: clienteDetalle.enviar_notificaciones,
      notas: clienteDetalle.notas || '',
      notas_internas: clienteDetalle.notas_internas || '',
    })
    setIsEditOpen(true)
  }

  const openCrearUsuario = () => {
    if (!clienteDetalle) return
    usuarioForm.reset({
      email: clienteDetalle.email || '',
      nombre: clienteDetalle.contacto_nombre || clienteDetalle.razon_social,
    })
    setIsUsuarioOpen(true)
  }

  const copyPassword = () => {
    if (newPassword) {
      navigator.clipboard.writeText(newPassword)
      setCopiedPassword(true)
      setTimeout(() => setCopiedPassword(false), 2000)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Clientes</h1>
          <p className="text-muted-foreground">
            Gestión de clientes y cuentas corrientes
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Cliente
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Clientes</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{estadisticas?.total_clientes || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Con Deuda</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {estadisticas?.clientes_con_deuda || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Deuda</CardTitle>
            <CreditCard className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(estadisticas?.total_deuda || 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Empresas</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {estadisticas?.por_tipo?.find(t => t.tipo === 'empresa')?.cantidad || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nombre, CUIT, email..."
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
            <SelectItem value="todos">Todos los tipos</SelectItem>
            <SelectItem value="particular">Particular</SelectItem>
            <SelectItem value="empresa">Empresa</SelectItem>
            <SelectItem value="gobierno">Gobierno</SelectItem>
            <SelectItem value="constructora">Constructora</SelectItem>
            <SelectItem value="consorcio">Consorcio</SelectItem>
            <SelectItem value="otro">Otro</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={conDeudaFilter === undefined ? 'todos' : conDeudaFilter ? 'con_deuda' : 'sin_deuda'}
          onValueChange={(v) => setConDeudaFilter(v === 'todos' ? undefined : v === 'con_deuda')}
        >
          <SelectTrigger className="w-full sm:w-[150px]">
            <SelectValue placeholder="Deuda" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos</SelectItem>
            <SelectItem value="con_deuda">Con deuda</SelectItem>
            <SelectItem value="sin_deuda">Sin deuda</SelectItem>
          </SelectContent>
        </Select>
        <ViewToggle viewMode={viewMode} onViewModeChange={setViewMode} />
      </div>

      {/* Cards View */}
      {viewMode === 'cards' && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {isLoading ? (
            [...Array(6)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardHeader className="space-y-2">
                  <div className="h-5 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-1/2" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 bg-muted rounded w-1/4" />
                </CardContent>
              </Card>
            ))
          ) : clientes?.length === 0 ? (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              No se encontraron clientes
            </div>
          ) : (
            clientes?.map((cliente) => (
              <Card
                key={cliente.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => openDetail(cliente)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1 min-w-0">
                      <CardTitle className="text-lg truncate">
                        {cliente.razon_social}
                      </CardTitle>
                      {cliente.nombre_fantasia && (
                        <p className="text-sm text-muted-foreground truncate">
                          {cliente.nombre_fantasia}
                        </p>
                      )}
                    </div>
                    <Badge className={clientesService.getTipoClienteColor(cliente.tipo)}>
                      {TIPO_ICONS[cliente.tipo]}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="text-sm space-y-1">
                    {cliente.email && (
                      <div className="flex items-center gap-1 text-muted-foreground truncate">
                        <Mail className="h-3 w-3 flex-shrink-0" />
                        {cliente.email}
                      </div>
                    )}
                    {cliente.telefono && (
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Phone className="h-3 w-3" />
                        {cliente.telefono}
                      </div>
                    )}
                    {cliente.ciudad && (
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        {cliente.ciudad}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t">
                    <span className="text-sm text-muted-foreground">Saldo CC</span>
                    <span className={`font-bold ${cliente.saldo_cuenta_corriente > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {formatCurrency(cliente.saldo_cuenta_corriente)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Table View */}
      {viewMode === 'list' && (
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Cliente</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Contacto</TableHead>
              <TableHead>Ciudad</TableHead>
              <TableHead className="text-right">Saldo CC</TableHead>
              <TableHead className="w-[80px]">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <TableRow key={i}>
                  {[...Array(7)].map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 bg-muted rounded animate-pulse" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : clientes?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                  No se encontraron clientes
                </TableCell>
              </TableRow>
            ) : (
              clientes?.map((cliente) => (
                <TableRow
                  key={cliente.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => openDetail(cliente)}
                >
                  <TableCell>
                    <span className="font-mono text-sm">{cliente.codigo}</span>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{cliente.razon_social}</p>
                      {cliente.nombre_fantasia && (
                        <p className="text-xs text-muted-foreground">{cliente.nombre_fantasia}</p>
                      )}
                      {cliente.cuit && (
                        <p className="text-xs text-muted-foreground">
                          CUIT: {clientesService.formatCUIT(cliente.cuit)}
                        </p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={clientesService.getTipoClienteColor(cliente.tipo)}>
                      <span className="flex items-center gap-1">
                        {TIPO_ICONS[cliente.tipo]}
                        {clientesService.getTipoClienteLabel(cliente.tipo)}
                      </span>
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm space-y-1">
                      {cliente.telefono && (
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <Phone className="h-3 w-3" />
                          {cliente.telefono}
                        </div>
                      )}
                      {cliente.email && (
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <Mail className="h-3 w-3" />
                          {cliente.email}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {cliente.ciudad || <span className="text-muted-foreground">-</span>}
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={`font-bold ${cliente.saldo_cuenta_corriente > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {formatCurrency(cliente.saldo_cuenta_corriente)}
                    </span>
                    {cliente.saldo_cuenta_corriente > 0 && (
                      <AlertTriangle className="h-4 w-4 text-yellow-500 inline ml-1" />
                    )}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openDetail(cliente); }}>
                          <Eye className="h-4 w-4 mr-2" />
                          Ver detalle
                        </DropdownMenuItem>
                        {isAdmin && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={(e) => {
                                e.stopPropagation()
                                if (confirm('¿Eliminar este cliente?')) {
                                  deleteMutation.mutate(cliente.id)
                                }
                              }}
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
      )}

      {/* Dialog: Crear Cliente */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Nuevo Cliente</DialogTitle>
            <DialogDescription>
              Registra un nuevo cliente en el sistema
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={createForm.handleSubmit(onSubmitCreate)} className="space-y-6">
            {/* Datos básicos */}
            <div className="space-y-4">
              <h4 className="font-medium">Datos Básicos</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Tipo de Cliente *</Label>
                  <Select
                    defaultValue="particular"
                    onValueChange={(v) => createForm.setValue('tipo', v as TipoCliente)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="particular">Particular</SelectItem>
                      <SelectItem value="empresa">Empresa</SelectItem>
                      <SelectItem value="gobierno">Gobierno</SelectItem>
                      <SelectItem value="constructora">Constructora</SelectItem>
                      <SelectItem value="consorcio">Consorcio</SelectItem>
                      <SelectItem value="otro">Otro</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Condición IVA *</Label>
                  <Select
                    defaultValue="consumidor_final"
                    onValueChange={(v) => createForm.setValue('condicion_iva', v as CondicionIVA)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="responsable_inscripto">Responsable Inscripto</SelectItem>
                      <SelectItem value="monotributo">Monotributo</SelectItem>
                      <SelectItem value="exento">Exento</SelectItem>
                      <SelectItem value="consumidor_final">Consumidor Final</SelectItem>
                      <SelectItem value="no_responsable">No Responsable</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Razón Social *</Label>
                <Input {...createForm.register('razon_social')} placeholder="Nombre o razón social" />
                {createForm.formState.errors.razon_social && (
                  <p className="text-sm text-destructive">{createForm.formState.errors.razon_social.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nombre Fantasía</Label>
                  <Input {...createForm.register('nombre_fantasia')} placeholder="Nombre comercial" />
                </div>
                <div className="space-y-2">
                  <Label>CUIT</Label>
                  <Input {...createForm.register('cuit')} placeholder="XX-XXXXXXXX-X" />
                </div>
              </div>
            </div>

            <Separator />

            {/* Contacto */}
            <div className="space-y-4">
              <h4 className="font-medium">Contacto</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input type="email" {...createForm.register('email')} placeholder="email@ejemplo.com" />
                </div>
                <div className="space-y-2">
                  <Label>Teléfono</Label>
                  <Input {...createForm.register('telefono')} placeholder="+54 11 1234-5678" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Celular</Label>
                  <Input {...createForm.register('celular')} placeholder="+54 9 11 1234-5678" />
                </div>
                <div className="space-y-2">
                  <Label>Persona de Contacto</Label>
                  <Input {...createForm.register('contacto_nombre')} placeholder="Nombre del contacto" />
                </div>
              </div>
            </div>

            <Separator />

            {/* Dirección */}
            <div className="space-y-4">
              <h4 className="font-medium">Dirección</h4>
              <div className="space-y-2">
                <Label>Dirección</Label>
                <Input {...createForm.register('direccion')} placeholder="Calle y número" />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Ciudad</Label>
                  <Input {...createForm.register('ciudad')} placeholder="Ciudad" />
                </div>
                <div className="space-y-2">
                  <Label>Provincia</Label>
                  <Input {...createForm.register('provincia')} defaultValue="Buenos Aires" />
                </div>
                <div className="space-y-2">
                  <Label>Código Postal</Label>
                  <Input {...createForm.register('codigo_postal')} placeholder="1234" />
                </div>
              </div>
            </div>

            <Separator />

            {/* Comercial */}
            <div className="space-y-4">
              <h4 className="font-medium">Datos Comerciales</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Descuento General (%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    {...createForm.register('descuento_general', { valueAsNumber: true })}
                    defaultValue={0}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Límite de Crédito</Label>
                  <Input
                    type="number"
                    step="0.01"
                    {...createForm.register('limite_credito', { valueAsNumber: true })}
                    placeholder="Sin límite"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Días de Crédito</Label>
                  <Input
                    type="number"
                    {...createForm.register('dias_credito', { valueAsNumber: true })}
                    defaultValue={0}
                  />
                </div>
              </div>
            </div>

            <Separator />

            {/* Notas */}
            <div className="space-y-4">
              <h4 className="font-medium">Notas</h4>
              <div className="space-y-2">
                <Label>Notas</Label>
                <Textarea {...createForm.register('notas')} placeholder="Notas generales..." rows={2} />
              </div>
              <div className="space-y-2">
                <Label>Notas Internas (no visible para el cliente)</Label>
                <Textarea {...createForm.register('notas_internas')} placeholder="Notas internas..." rows={2} />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                Crear Cliente
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Detalle Cliente */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle className="flex items-center gap-2">
                  {clienteDetalle?.nombre_display}
                  <Badge className={clientesService.getTipoClienteColor(clienteDetalle?.tipo || 'particular')}>
                    {clientesService.getTipoClienteLabel(clienteDetalle?.tipo || 'particular')}
                  </Badge>
                </DialogTitle>
                <DialogDescription>
                  {clienteDetalle?.codigo} • {clienteDetalle?.cuit ? clientesService.formatCUIT(clienteDetalle.cuit) : 'Sin CUIT'}
                </DialogDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={openEdit}>
                  <Edit className="h-4 w-4 mr-1" />
                  Editar
                </Button>
              </div>
            </div>
          </DialogHeader>

          {clienteDetalle && (
            <Tabs defaultValue="info" className="mt-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="info">Información</TabsTrigger>
                <TabsTrigger value="cuenta">Cuenta Corriente</TabsTrigger>
                <TabsTrigger value="proyectos">Proyectos</TabsTrigger>
                <TabsTrigger value="acceso">Acceso Portal</TabsTrigger>
              </TabsList>

              <TabsContent value="info" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <Label className="text-muted-foreground">Razón Social</Label>
                      <p className="font-medium">{clienteDetalle.razon_social}</p>
                    </div>
                    {clienteDetalle.nombre_fantasia && (
                      <div>
                        <Label className="text-muted-foreground">Nombre Fantasía</Label>
                        <p>{clienteDetalle.nombre_fantasia}</p>
                      </div>
                    )}
                    <div>
                      <Label className="text-muted-foreground">Condición IVA</Label>
                      <p>{clientesService.getCondicionIVALabel(clienteDetalle.condicion_iva)}</p>
                    </div>
                    {clienteDetalle.direccion && (
                      <div className="flex items-start gap-2">
                        <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                        <div>
                          <p>{clienteDetalle.direccion}</p>
                          <p className="text-sm text-muted-foreground">
                            {[clienteDetalle.ciudad, clienteDetalle.provincia, clienteDetalle.codigo_postal].filter(Boolean).join(', ')}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="space-y-4">
                    {clienteDetalle.email && (
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <p>{clienteDetalle.email}</p>
                      </div>
                    )}
                    {clienteDetalle.telefono && (
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-muted-foreground" />
                        <p>{clienteDetalle.telefono}</p>
                      </div>
                    )}
                    {clienteDetalle.contacto_nombre && (
                      <div>
                        <Label className="text-muted-foreground">Contacto</Label>
                        <p>{clienteDetalle.contacto_nombre}</p>
                        {clienteDetalle.contacto_cargo && (
                          <p className="text-sm text-muted-foreground">{clienteDetalle.contacto_cargo}</p>
                        )}
                      </div>
                    )}
                    <div>
                      <Label className="text-muted-foreground">Fecha de Alta</Label>
                      <p>{clienteDetalle.fecha_alta ? formatDate(clienteDetalle.fecha_alta) : '-'}</p>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="cuenta" className="space-y-4 mt-4">
                {estadoCuenta && (
                  <>
                    <div className="grid grid-cols-3 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Saldo Actual</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className={`text-2xl font-bold ${estadoCuenta.saldo_actual > 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {formatCurrency(estadoCuenta.saldo_actual)}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Límite de Crédito</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-2xl font-bold">
                            {estadoCuenta.limite_credito ? formatCurrency(estadoCuenta.limite_credito) : 'Sin límite'}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Proyectos Activos</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-2xl font-bold">{estadoCuenta.proyectos_activos}</p>
                        </CardContent>
                      </Card>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Facturado este mes</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-xl font-bold">{formatCurrency(estadoCuenta.total_facturado_mes)}</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Pagado este mes</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-xl font-bold text-green-600">{formatCurrency(estadoCuenta.total_pagado_mes)}</p>
                        </CardContent>
                      </Card>
                    </div>
                  </>
                )}
              </TabsContent>

              <TabsContent value="proyectos" className="mt-4">
                {clienteDetalle.proyectos && clienteDetalle.proyectos.length > 0 ? (
                  <div className="space-y-3">
                    {clienteDetalle.proyectos.map((proyecto) => (
                      <Card key={proyecto.id}>
                        <CardContent className="py-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <FolderKanban className="h-5 w-5 text-muted-foreground" />
                              <div>
                                <p className="font-medium">{proyecto.nombre}</p>
                                <p className="text-sm text-muted-foreground">
                                  {proyecto.fecha_inicio && `Inicio: ${formatDate(proyecto.fecha_inicio)}`}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <Badge>{proyecto.estado}</Badge>
                              <p className="text-sm text-muted-foreground mt-1">
                                {proyecto.porcentaje_avance.toFixed(0)}% avance
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <FolderKanban className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No hay proyectos asociados</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="acceso" className="space-y-4 mt-4">
                {usuarioCliente ? (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Usuario del Portal</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-muted-foreground">Email</Label>
                          <p className="font-medium">{usuarioCliente.email}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Nombre</Label>
                          <p>{usuarioCliente.nombre} {usuarioCliente.apellido}</p>
                        </div>
                      </div>

                      {newPassword && (
                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                          <p className="text-sm font-medium text-green-800 mb-2">Nueva contraseña:</p>
                          <div className="flex items-center gap-2">
                            <code className="bg-white px-3 py-1 rounded border">{newPassword}</code>
                            <Button variant="outline" size="sm" onClick={copyPassword}>
                              {copiedPassword ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                            </Button>
                          </div>
                        </div>
                      )}

                      <Button
                        variant="outline"
                        onClick={() => {
                          if (confirm('¿Resetear la contraseña del usuario?')) {
                            resetPasswordMutation.mutate(clienteDetalle.id)
                          }
                        }}
                      >
                        <Key className="h-4 w-4 mr-2" />
                        Resetear Contraseña
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="text-center py-8">
                    <UserPlus className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground mb-4">
                      Este cliente no tiene acceso al portal
                    </p>
                    <Button onClick={openCrearUsuario}>
                      <UserPlus className="h-4 w-4 mr-2" />
                      Crear Usuario de Acceso
                    </Button>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog: Editar Cliente */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Editar Cliente</DialogTitle>
          </DialogHeader>

          <form onSubmit={editForm.handleSubmit(onSubmitEdit)} className="space-y-6">
            {/* Mismo formulario que crear pero con editForm */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tipo de Cliente</Label>
                <Select
                  value={editForm.watch('tipo')}
                  onValueChange={(v) => editForm.setValue('tipo', v as TipoCliente)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="particular">Particular</SelectItem>
                    <SelectItem value="empresa">Empresa</SelectItem>
                    <SelectItem value="gobierno">Gobierno</SelectItem>
                    <SelectItem value="constructora">Constructora</SelectItem>
                    <SelectItem value="consorcio">Consorcio</SelectItem>
                    <SelectItem value="otro">Otro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Condición IVA</Label>
                <Select
                  value={editForm.watch('condicion_iva')}
                  onValueChange={(v) => editForm.setValue('condicion_iva', v as CondicionIVA)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="responsable_inscripto">Responsable Inscripto</SelectItem>
                    <SelectItem value="monotributo">Monotributo</SelectItem>
                    <SelectItem value="exento">Exento</SelectItem>
                    <SelectItem value="consumidor_final">Consumidor Final</SelectItem>
                    <SelectItem value="no_responsable">No Responsable</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Razón Social</Label>
              <Input {...editForm.register('razon_social')} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nombre Fantasía</Label>
                <Input {...editForm.register('nombre_fantasia')} />
              </div>
              <div className="space-y-2">
                <Label>CUIT</Label>
                <Input {...editForm.register('cuit')} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input type="email" {...editForm.register('email')} />
              </div>
              <div className="space-y-2">
                <Label>Teléfono</Label>
                <Input {...editForm.register('telefono')} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Dirección</Label>
              <Input {...editForm.register('direccion')} />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Ciudad</Label>
                <Input {...editForm.register('ciudad')} />
              </div>
              <div className="space-y-2">
                <Label>Provincia</Label>
                <Input {...editForm.register('provincia')} />
              </div>
              <div className="space-y-2">
                <Label>Código Postal</Label>
                <Input {...editForm.register('codigo_postal')} />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Descuento (%)</Label>
                <Input type="number" step="0.01" {...editForm.register('descuento_general', { valueAsNumber: true })} />
              </div>
              <div className="space-y-2">
                <Label>Límite Crédito</Label>
                <Input type="number" step="0.01" {...editForm.register('limite_credito', { valueAsNumber: true })} />
              </div>
              <div className="space-y-2">
                <Label>Días Crédito</Label>
                <Input type="number" {...editForm.register('dias_credito', { valueAsNumber: true })} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Notas</Label>
              <Textarea {...editForm.register('notas')} rows={2} />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                Guardar Cambios
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Crear Usuario Cliente */}
      <Dialog open={isUsuarioOpen} onOpenChange={setIsUsuarioOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Crear Usuario de Acceso</DialogTitle>
            <DialogDescription>
              Crea un usuario para que el cliente pueda acceder al portal
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={usuarioForm.handleSubmit(onSubmitUsuario)} className="space-y-4">
            <div className="space-y-2">
              <Label>Email *</Label>
              <Input type="email" {...usuarioForm.register('email')} />
              {usuarioForm.formState.errors.email && (
                <p className="text-sm text-destructive">{usuarioForm.formState.errors.email.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nombre *</Label>
                <Input {...usuarioForm.register('nombre')} />
              </div>
              <div className="space-y-2">
                <Label>Apellido</Label>
                <Input {...usuarioForm.register('apellido')} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Contraseña (opcional)</Label>
              <Input type="password" {...usuarioForm.register('password')} placeholder="Se genera automáticamente si no se especifica" />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsUsuarioOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={crearUsuarioMutation.isPending}>
                Crear Usuario
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
