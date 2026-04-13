import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, addDays } from 'date-fns'
import { es } from 'date-fns/locale'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Loader2,
  Plus,
  Calendar,
  User,
  Truck,
  MapPin,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Edit,
} from 'lucide-react'
import { asignacionesDiariasService, type AsignacionDiariaCreate, type AsignacionDiaria } from '@/services/jornadasOperario'
import { proyectosService } from '@/services/proyectos'
import { equiposService } from '@/services/equipos'
import { usuariosService } from '@/services/usuarios'

const prioridadConfig: Record<string, { label: string; color: string }> = {
  normal: { label: 'Normal', color: 'bg-gray-100 text-gray-800' },
  urgente: { label: 'Urgente', color: 'bg-red-100 text-red-800' },
  baja: { label: 'Baja', color: 'bg-blue-100 text-blue-800' },
}

export default function PlanificacionDiaria() {
  const queryClient = useQueryClient()
  const [fechaSeleccionada, setFechaSeleccionada] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [asignacionEditar, setAsignacionEditar] = useState<string | null>(null)
  const [asignacionEliminar, setAsignacionEliminar] = useState<string | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    operario_id: '',
    proyecto_id: '',
    etapa_id: '',
    vehiculo_id: '',
    prioridad: 'normal',
    notas: '',
  })

  // Cargar asignaciones del día
  const { data: asignaciones, isLoading } = useQuery({
    queryKey: ['asignaciones-diarias', fechaSeleccionada],
    queryFn: () => asignacionesDiariasService.getAsignaciones({ fecha: fechaSeleccionada }),
  })

  // Cargar operarios
  const { data: operarios } = useQuery({
    queryKey: ['operarios-lista'],
    queryFn: async () => {
      const usuarios = await usuariosService.getUsuarios()
      return usuarios.filter(u => u.rol === 'operario' && u.activo)
    },
  })

  // Cargar proyectos
  const { data: proyectos } = useQuery({
    queryKey: ['proyectos-activos'],
    queryFn: async () => {
      const proyectos = await proyectosService.getProyectos()
      return proyectos.filter(p => p.estado === 'en_ejecucion')
    },
  })

  // Cargar etapas del proyecto seleccionado
  const { data: etapas } = useQuery({
    queryKey: ['etapas-proyecto', formData.proyecto_id],
    queryFn: () => proyectosService.getEtapas(formData.proyecto_id),
    enabled: !!formData.proyecto_id,
  })

  // Cargar vehículos
  const { data: vehiculos } = useQuery({
    queryKey: ['vehiculos-disponibles'],
    queryFn: async () => {
      const equipos = await equiposService.getEquipos({ tipo: 'vehiculo' })
      return equipos.filter(e => e.estado === 'disponible')
    },
  })

  // Mutation crear asignación
  const crearMutation = useMutation({
    mutationFn: (data: AsignacionDiariaCreate) =>
      asignacionesDiariasService.crearAsignacion(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asignaciones-diarias'] })
      handleCloseDialog()
    },
  })

  // Mutation eliminar asignación
  const eliminarMutation = useMutation({
    mutationFn: (id: string) => asignacionesDiariasService.eliminarAsignacion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asignaciones-diarias'] })
      setDeleteDialogOpen(false)
      setAsignacionEliminar(null)
    },
  })

  const handleOpenDialog = (asignacionId?: string) => {
    if (asignacionId) {
      const asig = asignaciones?.find(a => a.id === asignacionId)
      if (asig) {
        setFormData({
          operario_id: asig.operario_id,
          proyecto_id: asig.proyecto_id,
          etapa_id: asig.etapa_id || '',
          vehiculo_id: asig.vehiculo_id || '',
          prioridad: asig.prioridad,
          notas: asig.notas || '',
        })
        setAsignacionEditar(asignacionId)
      }
    } else {
      setFormData({
        operario_id: '',
        proyecto_id: '',
        etapa_id: '',
        vehiculo_id: '',
        prioridad: 'normal',
        notas: '',
      })
      setAsignacionEditar(null)
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setAsignacionEditar(null)
    setFormData({
      operario_id: '',
      proyecto_id: '',
      etapa_id: '',
      vehiculo_id: '',
      prioridad: 'normal',
      notas: '',
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.operario_id || !formData.proyecto_id) return

    const data: AsignacionDiariaCreate = {
      operario_id: formData.operario_id,
      proyecto_id: formData.proyecto_id,
      etapa_id: formData.etapa_id || undefined,
      vehiculo_id: formData.vehiculo_id || undefined,
      fecha: fechaSeleccionada,
      prioridad: formData.prioridad as 'normal' | 'urgente' | 'baja',
      notas: formData.notas || undefined,
    }

    crearMutation.mutate(data)
  }

  const handleConfirmDelete = () => {
    if (asignacionEliminar) {
      eliminarMutation.mutate(asignacionEliminar)
    }
  }

  const cambiarFecha = (dias: number) => {
    const nuevaFecha = addDays(new Date(fechaSeleccionada), dias)
    setFechaSeleccionada(format(nuevaFecha, 'yyyy-MM-dd'))
  }

  // Agrupar asignaciones por proyecto
  const asignacionesPorProyecto = asignaciones?.reduce(
    (acc, asig) => {
      const key = asig.proyecto_id
      if (!acc[key]) {
        acc[key] = {
          proyecto_nombre: asig.proyecto_nombre || '',
          asignaciones: [] as AsignacionDiaria[],
        }
      }
      acc[key].asignaciones.push(asig)
      return acc
    },
    {} as Record<string, { proyecto_nombre: string; asignaciones: AsignacionDiaria[] }>
  )

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Planificación Diaria</h1>
          <p className="text-gray-500">Asigná operarios a proyectos para cada día</p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="bg-red-600 hover:bg-red-700">
          <Plus className="h-4 w-4 mr-2" />
          Nueva Asignación
        </Button>
      </div>

      {/* Selector de fecha */}
      <Card className="mb-6">
        <CardContent className="py-4">
          <div className="flex items-center justify-center gap-4">
            <Button variant="outline" size="icon" onClick={() => cambiarFecha(-1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-gray-500" />
              <Input
                type="date"
                value={fechaSeleccionada}
                onChange={e => setFechaSeleccionada(e.target.value)}
                className="w-40"
              />
              <span className="text-lg font-medium capitalize">
                {format(new Date(fechaSeleccionada), "EEEE d 'de' MMMM", { locale: es })}
              </span>
            </div>
            <Button variant="outline" size="icon" onClick={() => cambiarFecha(1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => setFechaSeleccionada(format(new Date(), 'yyyy-MM-dd'))}
            >
              Hoy
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lista de asignaciones */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-red-600" />
        </div>
      ) : asignaciones && asignaciones.length > 0 ? (
        <div className="space-y-6">
          {Object.entries(asignacionesPorProyecto || {}).map(([proyectoId, grupo]) => (
            <Card key={proyectoId}>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-red-600" />
                  {grupo.proyecto_nombre}
                </CardTitle>
                <CardDescription>
                  {grupo.asignaciones.length} operario(s) asignado(s)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {grupo.asignaciones.map(asig => {
                    const prioridadCfg = prioridadConfig[asig.prioridad]
                    return (
                      <div
                        key={asig.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <User className="h-4 w-4 text-gray-400" />
                            <span className="font-medium">{asig.operario_nombre}</span>
                          </div>
                          {asig.vehiculo_patente && (
                            <div className="flex items-center gap-1 text-sm text-gray-500">
                              <Truck className="h-4 w-4" />
                              {asig.vehiculo_patente}
                            </div>
                          )}
                          {asig.etapa_nombre && (
                            <span className="text-sm text-gray-500">→ {asig.etapa_nombre}</span>
                          )}
                          <Badge className={prioridadCfg.color}>{prioridadCfg.label}</Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleOpenDialog(asig.id)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-red-600 hover:text-red-700"
                            onClick={() => {
                              setAsignacionEliminar(asig.id)
                              setDeleteDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <CardContent>
            <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-500 mb-4">No hay asignaciones para esta fecha</p>
            <Button onClick={() => handleOpenDialog()} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Crear asignación
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Dialog de crear/editar */}
      <Dialog open={dialogOpen} onOpenChange={handleCloseDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {asignacionEditar ? 'Editar Asignación' : 'Nueva Asignación'}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="operario">Operario *</Label>
              <Select
                value={formData.operario_id}
                onValueChange={v => setFormData(prev => ({ ...prev, operario_id: v }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar operario" />
                </SelectTrigger>
                <SelectContent>
                  {operarios?.map(op => (
                    <SelectItem key={op.id} value={op.id}>
                      {op.nombre} {op.apellido}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="proyecto">Proyecto *</Label>
              <Select
                value={formData.proyecto_id}
                onValueChange={v =>
                  setFormData(prev => ({ ...prev, proyecto_id: v, etapa_id: '' }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar proyecto" />
                </SelectTrigger>
                <SelectContent>
                  {proyectos?.map(p => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {etapas && etapas.length > 0 && (
              <div className="space-y-2">
                <Label htmlFor="etapa">Etapa (opcional)</Label>
                <Select
                  value={formData.etapa_id}
                  onValueChange={v => setFormData(prev => ({ ...prev, etapa_id: v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar etapa" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Sin especificar</SelectItem>
                    {etapas.map((e: { id: string; nombre: string }) => (
                      <SelectItem key={e.id} value={e.id}>
                        {e.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="vehiculo">Vehículo (opcional)</Label>
              <Select
                value={formData.vehiculo_id}
                onValueChange={v => setFormData(prev => ({ ...prev, vehiculo_id: v }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar vehículo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Sin asignar</SelectItem>
                  {vehiculos?.map(v => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.patente || v.codigo} - {v.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="prioridad">Prioridad</Label>
              <Select
                value={formData.prioridad}
                onValueChange={v => setFormData(prev => ({ ...prev, prioridad: v }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(prioridadConfig).map(([key, cfg]) => (
                    <SelectItem key={key} value={key}>
                      {cfg.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notas">Notas</Label>
              <Textarea
                value={formData.notas}
                onChange={e => setFormData(prev => ({ ...prev, notas: e.target.value }))}
                placeholder="Instrucciones adicionales..."
                rows={3}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCloseDialog}>
                Cancelar
              </Button>
              <Button
                type="submit"
                className="bg-red-600 hover:bg-red-700"
                disabled={!formData.operario_id || !formData.proyecto_id || crearMutation.isPending}
              >
                {crearMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Guardando...
                  </>
                ) : asignacionEditar ? (
                  'Actualizar'
                ) : (
                  'Crear'
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Alert de confirmación de eliminación */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar asignación?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción no se puede deshacer. El operario dejará de estar asignado para esta
              fecha.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              {eliminarMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Eliminar'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
