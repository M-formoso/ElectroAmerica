import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Search,
  Filter,
  Wrench,
  Truck,
  Hammer,
  MoreVertical,
  Edit,
  Trash2,
  ArrowRight,
  ArrowLeft,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
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
import { equiposService } from '@/services/equipos'
import { proyectosService } from '@/services/proyectos'
import { formatCurrency, formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin } from '@/store/auth'
import type { Equipo, EstadoEquipo, TipoEquipo } from '@/types'

const tipoIcons: Record<TipoEquipo, any> = {
  herramienta: Hammer,
  vehiculo: Truck,
  maquinaria: Wrench,
  otro: Wrench,
}

const estadoColors: Record<EstadoEquipo, string> = {
  disponible: 'success',
  asignado: 'default',
  mantenimiento: 'warning',
  fuera_servicio: 'destructive',
}

const estadoLabels: Record<EstadoEquipo, string> = {
  disponible: 'Disponible',
  asignado: 'Asignado',
  mantenimiento: 'Mantenimiento',
  fuera_servicio: 'Fuera de Servicio',
}

export function EquiposPage() {
  const [search, setSearch] = useState('')
  const [estadoFilter, setEstadoFilter] = useState<string>('todos')
  const [tipoFilter, setTipoFilter] = useState<string>('todos')
  const [isAsignarOpen, setIsAsignarOpen] = useState(false)
  const [selectedEquipo, setSelectedEquipo] = useState<Equipo | null>(null)
  const [selectedProyecto, setSelectedProyecto] = useState<string>('')

  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  const { data: equipos, isLoading } = useQuery({
    queryKey: ['equipos', estadoFilter, tipoFilter],
    queryFn: () => equiposService.getEquipos({
      estado: estadoFilter !== 'todos' ? estadoFilter : undefined,
      tipo: tipoFilter !== 'todos' ? tipoFilter : undefined,
    }),
  })

  const { data: proyectos } = useQuery({
    queryKey: ['proyectos-activos'],
    queryFn: () => proyectosService.getProyectos({ estado: 'en_ejecucion' }),
  })

  const asignarMutation = useMutation({
    mutationFn: ({ equipoId, proyectoId }: { equipoId: string; proyectoId: string }) =>
      equiposService.asignarEquipo(equipoId, proyectoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
      toast({ title: 'Equipo asignado correctamente' })
      setIsAsignarOpen(false)
      setSelectedEquipo(null)
      setSelectedProyecto('')
    },
    onError: (error: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al asignar equipo',
        description: error.response?.data?.detail,
      })
    },
  })

  const devolverMutation = useMutation({
    mutationFn: equiposService.devolverEquipo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
      toast({ title: 'Equipo devuelto correctamente' })
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al devolver equipo' })
    },
  })

  const cambiarEstadoMutation = useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: string }) =>
      equiposService.cambiarEstado(id, estado),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
      toast({ title: 'Estado actualizado' })
    },
  })

  const filteredEquipos = equipos?.filter((e) =>
    e.nombre.toLowerCase().includes(search.toLowerCase()) ||
    e.codigo.toLowerCase().includes(search.toLowerCase())
  )

  const stats = {
    total: equipos?.length || 0,
    disponibles: equipos?.filter((e) => e.estado === 'disponible').length || 0,
    asignados: equipos?.filter((e) => e.estado === 'asignado').length || 0,
    mantenimiento: equipos?.filter((e) => e.estado === 'mantenimiento').length || 0,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Equipos</h1>
          <p className="text-muted-foreground">
            Gestiona los equipos y maquinaria
          </p>
        </div>
        {isAdmin && (
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Equipo
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-green-600">
              Disponibles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.disponibles}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-600">
              Asignados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {stats.asignados}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-yellow-600">
              Mantenimiento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {stats.mantenimiento}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar equipos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={estadoFilter} onValueChange={setEstadoFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos los estados</SelectItem>
            <SelectItem value="disponible">Disponible</SelectItem>
            <SelectItem value="asignado">Asignado</SelectItem>
            <SelectItem value="mantenimiento">Mantenimiento</SelectItem>
            <SelectItem value="fuera_servicio">Fuera de servicio</SelectItem>
          </SelectContent>
        </Select>
        <Select value={tipoFilter} onValueChange={setTipoFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Tipo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos los tipos</SelectItem>
            <SelectItem value="herramienta">Herramienta</SelectItem>
            <SelectItem value="vehiculo">Vehículo</SelectItem>
            <SelectItem value="maquinaria">Maquinaria</SelectItem>
            <SelectItem value="otro">Otro</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Equipo</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Marca/Modelo</TableHead>
              <TableHead className="w-[100px]">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <TableRow key={i}>
                  {[...Array(6)].map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 bg-muted rounded animate-pulse" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : filteredEquipos?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  No se encontraron equipos
                </TableCell>
              </TableRow>
            ) : (
              filteredEquipos?.map((equipo) => {
                const TipoIcon = tipoIcons[equipo.tipo]
                return (
                  <TableRow key={equipo.id}>
                    <TableCell className="font-mono text-sm">
                      {equipo.codigo}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <TipoIcon className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{equipo.nombre}</span>
                      </div>
                    </TableCell>
                    <TableCell className="capitalize">{equipo.tipo}</TableCell>
                    <TableCell>
                      <Badge variant={estadoColors[equipo.estado] as any}>
                        {estadoLabels[equipo.estado]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {equipo.marca && equipo.modelo
                        ? `${equipo.marca} ${equipo.modelo}`
                        : equipo.marca || equipo.modelo || '-'}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          {equipo.estado === 'disponible' && (
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedEquipo(equipo)
                                setIsAsignarOpen(true)
                              }}
                            >
                              <ArrowRight className="h-4 w-4 mr-2" />
                              Asignar a proyecto
                            </DropdownMenuItem>
                          )}
                          {equipo.estado === 'asignado' && (
                            <DropdownMenuItem
                              onClick={() => devolverMutation.mutate(equipo.id)}
                            >
                              <ArrowLeft className="h-4 w-4 mr-2" />
                              Devolver
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() =>
                              cambiarEstadoMutation.mutate({
                                id: equipo.id,
                                estado: 'mantenimiento',
                              })
                            }
                          >
                            <Wrench className="h-4 w-4 mr-2" />
                            Enviar a mantenimiento
                          </DropdownMenuItem>
                          {isAdmin && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem>
                                <Edit className="h-4 w-4 mr-2" />
                                Editar
                              </DropdownMenuItem>
                              <DropdownMenuItem className="text-destructive">
                                <Trash2 className="h-4 w-4 mr-2" />
                                Eliminar
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Asignar dialog */}
      <Dialog open={isAsignarOpen} onOpenChange={setIsAsignarOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Asignar Equipo</DialogTitle>
            <DialogDescription>
              Asignar "{selectedEquipo?.nombre}" a un proyecto
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Proyecto</Label>
              <Select value={selectedProyecto} onValueChange={setSelectedProyecto}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecciona un proyecto" />
                </SelectTrigger>
                <SelectContent>
                  {proyectos?.map((proyecto) => (
                    <SelectItem key={proyecto.id} value={proyecto.id}>
                      {proyecto.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAsignarOpen(false)}>
              Cancelar
            </Button>
            <Button
              onClick={() =>
                selectedEquipo &&
                asignarMutation.mutate({
                  equipoId: selectedEquipo.id,
                  proyectoId: selectedProyecto,
                })
              }
              disabled={!selectedProyecto || asignarMutation.isPending}
            >
              Asignar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
