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
import { Label } from '@/components/ui/label'
import { proyectosService } from '@/services/proyectos'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin } from '@/store/auth'
import type { Proyecto, EstadoProyecto } from '@/types'

const estadoColors: Record<EstadoProyecto, string> = {
  planificacion: 'secondary',
  en_ejecucion: 'default',
  pausado: 'warning',
  finalizado: 'success',
}

const estadoLabels: Record<EstadoProyecto, string> = {
  planificacion: 'Planificación',
  en_ejecucion: 'En Ejecución',
  pausado: 'Pausado',
  finalizado: 'Finalizado',
}

export function ProyectosPage() {
  const [search, setSearch] = useState('')
  const [estadoFilter, setEstadoFilter] = useState<string>('todos')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [selectedProyecto, setSelectedProyecto] = useState<Proyecto | null>(null)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)

  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  const { data: proyectos, isLoading } = useQuery({
    queryKey: ['proyectos', estadoFilter],
    queryFn: () => proyectosService.getProyectos(
      estadoFilter !== 'todos' ? { estado: estadoFilter } : undefined
    ),
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

  const filteredProyectos = proyectos?.filter((p) =>
    p.nombre.toLowerCase().includes(search.toLowerCase()) ||
    p.ubicacion?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Proyectos</h1>
          <p className="text-muted-foreground">
            Gestiona los proyectos de construcción
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
        <Select value={estadoFilter} onValueChange={setEstadoFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos</SelectItem>
            <SelectItem value="planificacion">Planificación</SelectItem>
            <SelectItem value="en_ejecucion">En Ejecución</SelectItem>
            <SelectItem value="pausado">Pausado</SelectItem>
            <SelectItem value="finalizado">Finalizado</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Projects grid */}
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
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredProyectos?.map((proyecto) => (
            <Card key={proyecto.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="space-y-1 flex-1 min-w-0">
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
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Avance</span>
                    <span className="font-medium">
                      {proyecto.porcentaje_avance.toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={proyecto.porcentaje_avance} className="h-2" />
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

                {proyecto.cliente && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground pt-2 border-t">
                    <User className="h-3 w-3" />
                    <span className="truncate">
                      {proyecto.cliente.nombre} {proyecto.cliente.apellido}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {filteredProyectos?.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No se encontraron proyectos</p>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar proyecto</DialogTitle>
            <DialogDescription>
              ¿Estás seguro de eliminar "{selectedProyecto?.nombre}"? Esta acción no se puede deshacer.
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
