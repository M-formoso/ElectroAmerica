import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Plus,
  Search,
  Filter,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  MapPin,
  Calendar,
  User,
  Loader2,
  Wrench,
  ClipboardList,
  Check,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { ViewToggle, type ViewMode } from '@/components/ui/view-toggle'
import { proyectosService } from '@/services/proyectos'
import { actividadesTipoService, type ActividadTipoList } from '@/services/actividadesTipo'
import { proyectoActividadesService } from '@/services/proyectoActividades'
import { herramientasService, type Herramienta } from '@/services/herramientas'
import { getClientes, type ClienteListItem } from '@/services/clientes'
import { depositosService } from '@/services/depositos'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin } from '@/store/auth'
import type { Proyecto, EstadoProyecto } from '@/types'

interface ActividadSeleccionada {
  actividad_tipo_id: string
  cantidad_planificada: string
}

interface ProyectoForm {
  nombre: string
  descripcion: string
  ubicacion: string
  fecha_inicio: string
  fecha_fin_estimada: string
  monto_contratado: string
  cliente_id: string
  fuente_materiales: 'global' | 'deposito'
  deposito_id: string
  actividades: ActividadSeleccionada[]
  herramientas_ids: string[]
}

const formInicial: ProyectoForm = {
  nombre: '',
  descripcion: '',
  ubicacion: '',
  fecha_inicio: '',
  fecha_fin_estimada: '',
  monto_contratado: '',
  cliente_id: '',
  fuente_materiales: 'global',
  deposito_id: '',
  actividades: [],
  herramientas_ids: [],
}

const estadoColors: Record<EstadoProyecto, string> = {
  planificacion: 'secondary',
  en_ejecucion: 'default',
  pausado: 'warning',
  finalizado: 'success',
}

const estadoLabels: Record<EstadoProyecto, string> = {
  planificacion: 'Planificacion',
  en_ejecucion: 'En Ejecucion',
  pausado: 'Pausado',
  finalizado: 'Finalizado',
}

export function ProyectosPage() {
  const [search, setSearch] = useState('')
  const [estadoFilter, setEstadoFilter] = useState<string>('todos')
  const [viewMode, setViewMode] = useState<ViewMode>('cards')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [selectedProyecto, setSelectedProyecto] = useState<Proyecto | null>(null)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [formData, setFormData] = useState<ProyectoForm>(formInicial)
  const [clienteFilter, setClienteFilter] = useState<string>('todos')

  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  const { data: proyectos, isLoading } = useQuery({
    queryKey: ['proyectos', estadoFilter],
    queryFn: () => proyectosService.getProyectos(
      estadoFilter !== 'todos' ? { estado: estadoFilter } : undefined
    ),
  })

  // Queries para el formulario de nuevo proyecto
  const { data: actividadesTipo = [] } = useQuery({
    queryKey: ['actividades-tipo'],
    queryFn: () => actividadesTipoService.getActividadesTipo(),
    enabled: isCreateOpen,
  })

  const { data: herramientas = [] } = useQuery({
    queryKey: ['herramientas'],
    queryFn: () => herramientasService.getHerramientas({ estado: 'buen_estado' }),
    enabled: isCreateOpen,
  })

  const { data: clientes = [] } = useQuery({
    queryKey: ['clientes'],
    queryFn: () => getClientes(),
  })

  // Depositos del cliente seleccionado (para elegir fuente de materiales)
  const { data: depositosCliente = [] } = useQuery({
    queryKey: ['depositos', formData.cliente_id],
    queryFn: () => depositosService.list(formData.cliente_id),
    enabled: isCreateOpen && !!formData.cliente_id,
  })

  const createMutation = useMutation({
    mutationFn: async (payload: {
      proyecto: Parameters<typeof proyectosService.createProyecto>[0]
      actividades: ActividadSeleccionada[]
    }) => {
      const proyecto = await proyectosService.createProyecto(payload.proyecto)
      if (payload.actividades.length > 0) {
        await proyectoActividadesService.createActividadesBulk(
          proyecto.id,
          payload.actividades.map((a) => ({
            actividad_tipo_id: a.actividad_tipo_id,
            cantidad_planificada: parseFloat(a.cantidad_planificada) || 1,
          }))
        )
      }
      return proyecto
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyectos'] })
      toast({ title: 'Proyecto creado exitosamente' })
      setIsCreateOpen(false)
      setFormData(formInicial)
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al crear proyecto' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: proyectosService.deleteProyecto,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyectos'] })
      toast({ title: 'Proyecto eliminado' })
      setIsDeleteOpen(false)
      setSelectedProyecto(null)
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al eliminar' })
    },
  })

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      proyecto: {
        nombre: formData.nombre,
        descripcion: formData.descripcion || undefined,
        ubicacion: formData.ubicacion || undefined,
        fecha_inicio: formData.fecha_inicio || undefined,
        fecha_fin_estimada: formData.fecha_fin_estimada || undefined,
        monto_contratado: formData.monto_contratado ? parseFloat(formData.monto_contratado) : undefined,
        cliente_id: formData.cliente_id || undefined,
        deposito_id:
          formData.fuente_materiales === 'deposito' && formData.deposito_id
            ? formData.deposito_id
            : undefined,
      },
      actividades: formData.actividades,
    })
  }

  // Funciones para manejar seleccion de actividades y herramientas
  const toggleActividadTipo = (id: string) => {
    setFormData(prev => {
      const yaSeleccionada = prev.actividades.some(a => a.actividad_tipo_id === id)
      return {
        ...prev,
        actividades: yaSeleccionada
          ? prev.actividades.filter(a => a.actividad_tipo_id !== id)
          : [...prev.actividades, { actividad_tipo_id: id, cantidad_planificada: '1' }],
      }
    })
  }

  const setCantidadActividad = (id: string, cantidad: string) => {
    setFormData(prev => ({
      ...prev,
      actividades: prev.actividades.map(a =>
        a.actividad_tipo_id === id ? { ...a, cantidad_planificada: cantidad } : a
      ),
    }))
  }

  const toggleHerramienta = (id: string) => {
    setFormData(prev => ({
      ...prev,
      herramientas_ids: prev.herramientas_ids.includes(id)
        ? prev.herramientas_ids.filter(h => h !== id)
        : [...prev.herramientas_ids, id]
    }))
  }

  const filteredProyectos = proyectos?.filter((p) => {
    const matchesSearch = p.nombre.toLowerCase().includes(search.toLowerCase()) ||
      p.ubicacion?.toLowerCase().includes(search.toLowerCase())
    const matchesCliente = clienteFilter === 'todos' ||
      (clienteFilter === 'sin_cliente' && !p.cliente_id) ||
      p.cliente_id === clienteFilter
    return matchesSearch && matchesCliente
  })

  const renderCardView = () => (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {filteredProyectos?.map((proyecto) => (
        <Card key={proyecto.id} className="hover:shadow-md transition-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between">
              <div className="space-y-1 flex-1 min-w-0">
                {proyecto.cliente_nombre ? (
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                      <User className="h-3 w-3 mr-1" />
                      {proyecto.cliente_nombre}
                    </Badge>
                  </div>
                ) : (
                  <Badge variant="outline" className="text-xs mb-1">Sin cliente</Badge>
                )}
                <CardTitle className="text-lg truncate">
                  {proyecto.nombre}
                </CardTitle>
                {proyecto.ubicacion && (
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    {proyecto.ubicacion}
                  </p>
                )}
              </div>
              {isAdmin && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem asChild>
                      <Link to={`/proyectos/${proyecto.id}/editar`}>
                        <Edit className="h-4 w-4 mr-2" />
                        Editar
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={() => {
                        setSelectedProyecto(proyecto)
                        setIsDeleteOpen(true)
                      }}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Eliminar
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Avance</span>
                <span className="font-medium">
                  {Number(proyecto.porcentaje_avance).toFixed(0)}%
                </span>
              </div>
              <Progress value={Number(proyecto.porcentaje_avance)} className="h-2" />
            </div>

            <div className="flex items-center justify-between">
              <Badge variant={estadoColors[proyecto.estado] as any}>
                {estadoLabels[proyecto.estado]}
              </Badge>
              {proyecto.fecha_fin_estimada && (
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {formatDate(proyecto.fecha_fin_estimada)}
                </span>
              )}
            </div>

            <Button asChild className="w-full" variant="default">
              <Link to={`/proyectos/${proyecto.id}`}>
                <Eye className="h-4 w-4 mr-2" />
                Ver Detalle
              </Link>
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  )

  const renderListView = () => (
    <Card>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Proyecto</TableHead>
            <TableHead>Ubicacion</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Avance</TableHead>
            <TableHead>Fecha Fin</TableHead>
            <TableHead>Cliente</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredProyectos?.map((proyecto) => (
            <TableRow key={proyecto.id}>
              <TableCell>
                <Link
                  to={`/proyectos/${proyecto.id}`}
                  className="font-medium hover:underline"
                >
                  {proyecto.nombre}
                </Link>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {proyecto.ubicacion || '-'}
              </TableCell>
              <TableCell>
                <Badge variant={estadoColors[proyecto.estado] as any}>
                  {estadoLabels[proyecto.estado]}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress value={Number(proyecto.porcentaje_avance)} className="h-2 w-16" />
                  <span className="text-sm">{Number(proyecto.porcentaje_avance).toFixed(0)}%</span>
                </div>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {proyecto.fecha_fin_estimada ? formatDate(proyecto.fecha_fin_estimada) : '-'}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {proyecto.cliente_nombre || '-'}
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem asChild>
                      <Link to={`/proyectos/${proyecto.id}`}>
                        <Eye className="h-4 w-4 mr-2" />
                        Ver detalles
                      </Link>
                    </DropdownMenuItem>
                    {isAdmin && (
                      <>
                        <DropdownMenuItem asChild>
                          <Link to={`/proyectos/${proyecto.id}/editar`}>
                            <Edit className="h-4 w-4 mr-2" />
                            Editar
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => {
                            setSelectedProyecto(proyecto)
                            setIsDeleteOpen(true)
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
          ))}
        </TableBody>
      </Table>
    </Card>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Proyectos</h1>
          <p className="text-muted-foreground">
            Gestiona los proyectos de construccion
          </p>
        </div>
        {isAdmin && (
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Proyecto
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar proyectos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <Select value={clienteFilter} onValueChange={setClienteFilter}>
            <SelectTrigger className="w-full sm:w-[200px]">
              <User className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Cliente" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Todos los clientes</SelectItem>
              <SelectItem value="sin_cliente">Sin cliente</SelectItem>
              {clientes.map((cliente: ClienteListItem) => (
                <SelectItem key={cliente.id} value={cliente.id}>
                  {cliente.nombre_fantasia || cliente.razon_social}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={estadoFilter} onValueChange={setEstadoFilter}>
            <SelectTrigger className="w-full sm:w-[180px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Todos</SelectItem>
              <SelectItem value="planificacion">Planificacion</SelectItem>
              <SelectItem value="en_ejecucion">En Ejecucion</SelectItem>
              <SelectItem value="pausado">Pausado</SelectItem>
              <SelectItem value="finalizado">Finalizado</SelectItem>
            </SelectContent>
          </Select>
          <ViewToggle viewMode={viewMode} onViewModeChange={setViewMode} />
        </div>
      </div>

      {/* Projects grid/list */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="space-y-2">
                <div className="h-5 bg-muted rounded w-3/4" />
                <div className="h-4 bg-muted rounded w-1/2" />
              </CardHeader>
              <CardContent>
                <div className="h-2 bg-muted rounded mb-4" />
                <div className="h-4 bg-muted rounded w-1/4" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : viewMode === 'cards' ? (
        renderCardView()
      ) : (
        renderListView()
      )}

      {filteredProyectos?.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No se encontraron proyectos</p>
        </div>
      )}

      {/* Create project dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Nuevo Proyecto</DialogTitle>
            <DialogDescription>
              Ingresa los datos del nuevo proyecto
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateSubmit}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre *</Label>
                <Input
                  id="nombre"
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  placeholder="Nombre del proyecto"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="descripcion">Descripcion</Label>
                <Textarea
                  id="descripcion"
                  value={formData.descripcion}
                  onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                  placeholder="Descripcion del proyecto"
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ubicacion">Ubicacion</Label>
                <Input
                  id="ubicacion"
                  value={formData.ubicacion}
                  onChange={(e) => setFormData({ ...formData, ubicacion: e.target.value })}
                  placeholder="Direccion o ubicacion"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="fecha_inicio">Fecha Inicio</Label>
                  <Input
                    id="fecha_inicio"
                    type="date"
                    value={formData.fecha_inicio}
                    onChange={(e) => setFormData({ ...formData, fecha_inicio: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fecha_fin_estimada">Fecha Fin Estimada</Label>
                  <Input
                    id="fecha_fin_estimada"
                    type="date"
                    value={formData.fecha_fin_estimada}
                    onChange={(e) => setFormData({ ...formData, fecha_fin_estimada: e.target.value })}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="monto_contratado">Monto Contratado ($)</Label>
                  <Input
                    id="monto_contratado"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.monto_contratado}
                    onChange={(e) => setFormData({ ...formData, monto_contratado: e.target.value })}
                    placeholder="0.00"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Cliente</Label>
                  <Select
                    value={formData.cliente_id}
                    onValueChange={(v) =>
                      setFormData({
                        ...formData,
                        cliente_id: v,
                        // Al cambiar de cliente, resetear el deposito seleccionado
                        deposito_id: '',
                        fuente_materiales: 'global',
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar cliente" />
                    </SelectTrigger>
                    <SelectContent>
                      {clientes.map((cliente: ClienteListItem) => (
                        <SelectItem key={cliente.id} value={cliente.id}>
                          {cliente.nombre_fantasia || cliente.razon_social}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Fuente de materiales */}
              <div className="space-y-3 pt-4 border-t">
                <div className="flex items-center gap-2">
                  <Wrench className="h-4 w-4 text-primary" />
                  <Label className="text-base font-semibold">Fuente de materiales</Label>
                </div>
                <p className="text-sm text-muted-foreground">
                  Donde se descuenta el stock al consumir materiales en este proyecto.
                </p>
                <div className="grid gap-2">
                  <label className="flex items-center gap-3 p-2 rounded-md border cursor-pointer hover:bg-muted/50">
                    <input
                      type="radio"
                      name="fuente_materiales"
                      checked={formData.fuente_materiales === 'global'}
                      onChange={() =>
                        setFormData({
                          ...formData,
                          fuente_materiales: 'global',
                          deposito_id: '',
                        })
                      }
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium">Stock global</p>
                      <p className="text-xs text-muted-foreground">
                        Usa el inventario general de la seccion Materiales.
                      </p>
                    </div>
                  </label>
                  <label
                    className={`flex items-center gap-3 p-2 rounded-md border ${
                      formData.cliente_id
                        ? 'cursor-pointer hover:bg-muted/50'
                        : 'opacity-50 cursor-not-allowed'
                    }`}
                  >
                    <input
                      type="radio"
                      name="fuente_materiales"
                      disabled={!formData.cliente_id}
                      checked={formData.fuente_materiales === 'deposito'}
                      onChange={() =>
                        setFormData({ ...formData, fuente_materiales: 'deposito' })
                      }
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium">
                        Deposito del cliente
                        {!formData.cliente_id && (
                          <span className="text-xs text-muted-foreground ml-2">
                            (selecciona un cliente primero)
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Usa el stock de un deposito especifico del cliente.
                      </p>
                    </div>
                  </label>
                </div>
                {formData.fuente_materiales === 'deposito' && (
                  <div className="space-y-2 pl-4">
                    <Label>Deposito *</Label>
                    <Select
                      value={formData.deposito_id}
                      onValueChange={(v) =>
                        setFormData({ ...formData, deposito_id: v })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccionar deposito del cliente" />
                      </SelectTrigger>
                      <SelectContent>
                        {depositosCliente.length === 0 ? (
                          <div className="p-2 text-sm text-muted-foreground text-center">
                            El cliente no tiene depositos. Crealos en Recursos &gt; Depositos.
                          </div>
                        ) : (
                          depositosCliente.map((d) => (
                            <SelectItem key={d.id} value={d.id}>
                              {d.nombre}
                              {d.cantidad_materiales > 0 && (
                                <span className="text-xs text-muted-foreground ml-2">
                                  ({d.cantidad_materiales} materiales)
                                </span>
                              )}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>

              {/* Seccion de Actividades Tipo */}
              <div className="space-y-3 pt-4 border-t">
                <div className="flex items-center gap-2">
                  <ClipboardList className="h-4 w-4 text-primary" />
                  <Label className="text-base font-semibold">Actividades del Proyecto</Label>
                  {formData.actividades.length > 0 && (
                    <Badge variant="secondary">{formData.actividades.length} seleccionadas</Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  Selecciona las actividades y la cantidad planificada para cada una
                </p>
                <div className="max-h-[260px] overflow-y-auto border rounded-md p-3">
                  <div className="space-y-2">
                    {actividadesTipo.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        No hay actividades tipo disponibles
                      </p>
                    ) : (
                      actividadesTipo.map((actividad) => {
                        const seleccionada = formData.actividades.find(
                          (a) => a.actividad_tipo_id === actividad.id
                        )
                        const checked = !!seleccionada
                        return (
                          <div
                            key={actividad.id}
                            className={`w-full rounded-md transition-colors ${
                              checked ? 'bg-primary/10' : 'hover:bg-muted/50'
                            }`}
                          >
                            <div
                              role="button"
                              tabIndex={0}
                              className="flex items-center gap-3 p-2 cursor-pointer text-left"
                              onClick={() => toggleActividadTipo(actividad.id)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                  e.preventDefault()
                                  toggleActividadTipo(actividad.id)
                                }
                              }}
                            >
                              <span
                                aria-hidden
                                className={`h-4 w-4 shrink-0 rounded-sm border flex items-center justify-center ${
                                  checked ? 'bg-primary border-primary' : 'border-primary'
                                }`}
                              >
                                {checked && <Check className="h-3 w-3 text-primary-foreground" />}
                              </span>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">{actividad.nombre}</p>
                                <p className="text-xs text-muted-foreground">
                                  {actividad.categoria} • {actividad.cantidad_materiales} materiales
                                </p>
                              </div>
                            </div>
                            {checked && (
                              <div
                                className="flex items-center gap-2 px-2 pb-2 pl-9"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <Label className="text-xs text-muted-foreground shrink-0">
                                  Cantidad planificada:
                                </Label>
                                <Input
                                  type="number"
                                  min="0"
                                  step="0.01"
                                  value={seleccionada.cantidad_planificada}
                                  onChange={(e) =>
                                    setCantidadActividad(actividad.id, e.target.value)
                                  }
                                  className="h-8 w-28"
                                  placeholder="1"
                                />
                                <span className="text-xs text-muted-foreground">
                                  {actividad.unidad_trabajo}
                                </span>
                              </div>
                            )}
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
              </div>

              {/* Seccion de Herramientas */}
              <div className="space-y-3 pt-4 border-t">
                <div className="flex items-center gap-2">
                  <Wrench className="h-4 w-4 text-primary" />
                  <Label className="text-base font-semibold">Herramientas</Label>
                  {formData.herramientas_ids.length > 0 && (
                    <Badge variant="secondary">{formData.herramientas_ids.length} seleccionadas</Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  Selecciona las herramientas necesarias para este proyecto
                </p>
                <div className="h-[150px] overflow-y-auto border rounded-md p-3">
                  <div className="space-y-2">
                    {herramientas.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        No hay herramientas disponibles
                      </p>
                    ) : (
                      herramientas.map((herramienta) => {
                        const checked = formData.herramientas_ids.includes(herramienta.id)
                        return (
                          <div
                            key={herramienta.id}
                            role="button"
                            tabIndex={0}
                            className={`w-full flex items-center gap-3 p-2 rounded-md cursor-pointer hover:bg-muted/50 transition-colors text-left ${
                              checked ? 'bg-primary/10' : ''
                            }`}
                            onClick={() => toggleHerramienta(herramienta.id)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault()
                                toggleHerramienta(herramienta.id)
                              }
                            }}
                          >
                            <span
                              aria-hidden
                              className={`h-4 w-4 shrink-0 rounded-sm border flex items-center justify-center ${
                                checked ? 'bg-primary border-primary' : 'border-primary'
                              }`}
                            >
                              {checked && <Check className="h-3 w-3 text-primary-foreground" />}
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">{herramienta.nombre}</p>
                              {herramienta.descripcion && (
                                <p className="text-xs text-muted-foreground truncate">
                                  {herramienta.descripcion}
                                </p>
                              )}
                            </div>
                            <Badge
                              variant={herramienta.estado_prestamo === 'disponible' ? 'secondary' : 'outline'}
                              className="text-xs"
                            >
                              {herramienta.estado_prestamo === 'disponible' ? 'Disponible' : 'En uso'}
                            </Badge>
                            {checked && <Check className="h-4 w-4 text-primary" />}
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={
                  createMutation.isPending ||
                  !formData.nombre ||
                  (formData.fuente_materiales === 'deposito' && !formData.deposito_id)
                }
              >
                {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Crear Proyecto
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar proyecto</DialogTitle>
            <DialogDescription>
              Estas seguro de eliminar "{selectedProyecto?.nombre}"? Esta accion no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => selectedProyecto && deleteMutation.mutate(selectedProyecto.id)}
              disabled={deleteMutation.isPending}
            >
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
