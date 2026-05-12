import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Loader2,
  Plus,
  ClipboardList,
  Package,
  Edit,
  Trash2,
  Search,
  LayoutGrid,
  List,
} from 'lucide-react'
import { actividadesTipoService, type ActividadTipoCreate, type ActividadTipo } from '@/services/jornadasOperario'
import { materialesService } from '@/services/materiales'

interface MaterialSeleccionado {
  material_id: string
  cantidad_por_unidad: number
}

export default function ActividadesTipo() {
  const queryClient = useQueryClient()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [actividadEditar, setActividadEditar] = useState<ActividadTipo | null>(null)
  const [actividadEliminar, setActividadEliminar] = useState<string | null>(null)
  const [busqueda, setBusqueda] = useState('')
  const [viewMode, setViewMode] = useState<'cards' | 'list'>('cards')

  // Form state
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    categoria: '',
  })
  const [materialesSeleccionados, setMaterialesSeleccionados] = useState<MaterialSeleccionado[]>([])

  // Cargar actividades tipo
  const { data: actividades, isLoading } = useQuery({
    queryKey: ['actividades-tipo'],
    queryFn: () => actividadesTipoService.getActividadesTipo(),
  })

  // Cargar materiales para selector
  const { data: materiales } = useQuery({
    queryKey: ['materiales-lista'],
    queryFn: () => materialesService.getMateriales(),
  })

  // Cargar actividad completa con materiales cuando se esta editando
  const { data: actividadCompleta } = useQuery({
    queryKey: ['actividad-tipo', actividadEditar?.id],
    queryFn: () => actividadesTipoService.getActividadTipo(actividadEditar!.id),
    enabled: !!actividadEditar?.id && dialogOpen,
  })

  // Cuando llega la actividad completa, pre-cargar sus materiales
  useEffect(() => {
    if (actividadCompleta?.materiales) {
      setMaterialesSeleccionados(
        actividadCompleta.materiales.map((m) => ({
          material_id: m.material_id,
          cantidad_por_unidad: m.cantidad_por_unidad,
        }))
      )
    }
  }, [actividadCompleta])

  // Mutation crear
  const crearMutation = useMutation({
    mutationFn: (data: ActividadTipoCreate) => actividadesTipoService.createActividadTipo(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actividades-tipo'] })
      handleCloseDialog()
    },
  })

  // Mutation actualizar
  const actualizarMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ActividadTipoCreate }) =>
      actividadesTipoService.updateActividadTipo(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actividades-tipo'] })
      // Refrescar materiales calculados de cualquier proyecto que use esta actividad
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades'] })
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades-resumen'] })
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividad-detalle'] })
      handleCloseDialog()
    },
  })

  // Mutation eliminar
  const eliminarMutation = useMutation({
    mutationFn: (id: string) => actividadesTipoService.deleteActividadTipo(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actividades-tipo'] })
      setDeleteDialogOpen(false)
      setActividadEliminar(null)
    },
  })

  const handleOpenDialog = (actividad?: ActividadTipo) => {
    if (actividad) {
      setFormData({
        nombre: actividad.nombre,
        descripcion: actividad.descripcion || '',
        categoria: actividad.categoria || '',
      })
      setMaterialesSeleccionados(
        actividad.materiales?.map(m => ({
          material_id: m.material_id,
          cantidad_por_unidad: m.cantidad_por_unidad,
        })) || []
      )
      setActividadEditar(actividad)
    } else {
      setFormData({ nombre: '', descripcion: '', categoria: '' })
      setMaterialesSeleccionados([])
      setActividadEditar(null)
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setActividadEditar(null)
    setFormData({ nombre: '', descripcion: '', categoria: '' })
    setMaterialesSeleccionados([])
  }

  const handleToggleMaterial = (materialId: string, checked: boolean) => {
    if (checked) {
      setMaterialesSeleccionados(prev => [...prev, { material_id: materialId, cantidad_por_unidad: 1 }])
    } else {
      setMaterialesSeleccionados(prev => prev.filter(m => m.material_id !== materialId))
    }
  }

  const handleCantidadMaterial = (materialId: string, cantidad: number) => {
    setMaterialesSeleccionados(prev =>
      prev.map(m => (m.material_id === materialId ? { ...m, cantidad_por_unidad: cantidad } : m))
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.nombre.trim()) return

    const data: ActividadTipoCreate = {
      nombre: formData.nombre.trim(),
      descripcion: formData.descripcion.trim() || undefined,
      categoria: formData.categoria.trim() || undefined,
      materiales: materialesSeleccionados.filter(m => m.cantidad_por_unidad > 0),
    }

    if (actividadEditar) {
      actualizarMutation.mutate({ id: actividadEditar.id, data })
    } else {
      crearMutation.mutate(data)
    }
  }

  const handleConfirmDelete = () => {
    if (actividadEliminar) {
      eliminarMutation.mutate(actividadEliminar)
    }
  }

  // Filtrar actividades
  const actividadesFiltradas = actividades?.filter(
    a =>
      a.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
      a.categoria?.toLowerCase().includes(busqueda.toLowerCase())
  )

  // Agrupar por categoría
  const actividadesPorCategoria = actividadesFiltradas?.reduce(
    (acc, act) => {
      const cat = act.categoria || 'Sin categoría'
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(act)
      return acc
    },
    {} as Record<string, ActividadTipo[]>
  )

  const isPending = crearMutation.isPending || actualizarMutation.isPending

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Actividades Tipo</h1>
          <p className="text-gray-500">
            Catálogo de actividades con materiales predefinidos
          </p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="bg-red-600 hover:bg-red-700">
          <Plus className="h-4 w-4 mr-2" />
          Nueva Actividad
        </Button>
      </div>

      {/* Búsqueda y vista */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Buscar actividades..."
            value={busqueda}
            onChange={e => setBusqueda(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex items-center border rounded-md">
          <Button
            variant={viewMode === 'cards' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('cards')}
            className={viewMode === 'cards' ? 'bg-red-600 hover:bg-red-700' : ''}
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('list')}
            className={viewMode === 'list' ? 'bg-red-600 hover:bg-red-700' : ''}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Lista de actividades */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-red-600" />
        </div>
      ) : actividadesFiltradas && actividadesFiltradas.length > 0 ? (
        viewMode === 'cards' ? (
          <div className="space-y-6">
            {Object.entries(actividadesPorCategoria || {}).map(([categoria, acts]) => (
              <div key={categoria}>
                <h3 className="text-lg font-semibold mb-3 text-gray-700">{categoria}</h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {acts.map(actividad => (
                    <Card key={actividad.id} className="hover:shadow-md transition-shadow">
                      <CardHeader className="pb-2">
                        <div className="flex items-start justify-between">
                          <CardTitle className="text-base flex items-center gap-2">
                            <ClipboardList className="h-4 w-4 text-red-600" />
                            {actividad.nombre}
                          </CardTitle>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleOpenDialog(actividad)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-red-600"
                              onClick={() => {
                                setActividadEliminar(actividad.id)
                                setDeleteDialogOpen(true)
                              }}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        {actividad.descripcion && (
                          <CardDescription>{actividad.descripcion}</CardDescription>
                        )}
                      </CardHeader>
                      <CardContent>
                        {actividad.materiales && actividad.materiales.length > 0 ? (
                          <div className="space-y-2">
                            <p className="text-sm text-gray-500 flex items-center gap-1">
                              <Package className="h-3 w-3" />
                              Materiales ({actividad.materiales.length}):
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {actividad.materiales.slice(0, 3).map(mat => (
                                <Badge key={mat.material_id} variant="outline" className="text-xs">
                                  {mat.material_nombre} ({mat.cantidad_por_unidad})
                                </Badge>
                              ))}
                              {actividad.materiales.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{actividad.materiales.length - 3} más
                                </Badge>
                              )}
                            </div>
                          </div>
                        ) : (
                          <p className="text-sm text-gray-400">Sin materiales definidos</p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead>Descripción</TableHead>
                  <TableHead>Materiales</TableHead>
                  <TableHead className="w-24">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {actividadesFiltradas.map(actividad => (
                  <TableRow key={actividad.id}>
                    <TableCell className="font-medium">{actividad.nombre}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{actividad.categoria || 'Sin categoría'}</Badge>
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      {actividad.descripcion || '-'}
                    </TableCell>
                    <TableCell>
                      {actividad.materiales?.length || 0} materiales
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => handleOpenDialog(actividad)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-600"
                          onClick={() => {
                            setActividadEliminar(actividad.id)
                            setDeleteDialogOpen(true)
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        )
      ) : (
        <Card className="text-center py-12">
          <CardContent>
            <ClipboardList className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-500 mb-4">
              {busqueda ? 'No se encontraron actividades' : 'No hay actividades tipo definidas'}
            </p>
            {!busqueda && (
              <Button onClick={() => handleOpenDialog()} variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Crear primera actividad
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Dialog de crear/editar */}
      <Dialog open={dialogOpen} onOpenChange={handleCloseDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {actividadEditar ? 'Editar Actividad Tipo' : 'Nueva Actividad Tipo'}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre *</Label>
                <Input
                  id="nombre"
                  value={formData.nombre}
                  onChange={e => setFormData(prev => ({ ...prev, nombre: e.target.value }))}
                  placeholder="Ej: Instalación de tablero"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="categoria">Categoría</Label>
                <Input
                  id="categoria"
                  value={formData.categoria}
                  onChange={e => setFormData(prev => ({ ...prev, categoria: e.target.value }))}
                  placeholder="Ej: Instalación eléctrica"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="descripcion">Descripción</Label>
              <Textarea
                id="descripcion"
                value={formData.descripcion}
                onChange={e => setFormData(prev => ({ ...prev, descripcion: e.target.value }))}
                placeholder="Descripción de la actividad..."
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Package className="h-4 w-4" />
                Materiales predefinidos
              </Label>
              <p className="text-sm text-gray-500">
                Seleccioná los materiales típicos para esta actividad
              </p>
              <div className="border rounded-lg max-h-[200px] overflow-y-auto">
                {materiales?.map(mat => {
                  const seleccionado = materialesSeleccionados.find(
                    m => m.material_id === mat.id
                  )
                  return (
                    <div
                      key={mat.id}
                      className={`flex items-center gap-4 p-3 border-b last:border-b-0 ${
                        seleccionado ? 'bg-red-50' : ''
                      }`}
                    >
                      <Checkbox
                        checked={!!seleccionado}
                        onCheckedChange={checked =>
                          handleToggleMaterial(mat.id, checked as boolean)
                        }
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{mat.nombre}</p>
                        <p className="text-xs text-gray-500">{mat.unidad}</p>
                      </div>
                      {seleccionado && (
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            className="w-20 h-8"
                            value={seleccionado.cantidad_por_unidad || ''}
                            onChange={e =>
                              handleCantidadMaterial(mat.id, parseFloat(e.target.value) || 0)
                            }
                            min="0"
                            step="0.1"
                          />
                          <span className="text-xs text-gray-500">{mat.unidad}</span>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCloseDialog}>
                Cancelar
              </Button>
              <Button
                type="submit"
                className="bg-red-600 hover:bg-red-700"
                disabled={!formData.nombre.trim() || isPending}
              >
                {isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Guardando...
                  </>
                ) : actividadEditar ? (
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
            <AlertDialogTitle>¿Eliminar actividad tipo?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción no se puede deshacer. La actividad y sus materiales predefinidos serán
              eliminados del catálogo.
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
