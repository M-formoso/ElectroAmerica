import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, ArrowLeft, Eye, ImageIcon, Upload, X, Loader2 } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  herramientasService,
  type Herramienta,
  type EstadoHerramienta,
  type HerramientaCreate,
  type HerramientaUpdate,
} from '@/services/herramientas'

const estadoLabels: Record<EstadoHerramienta, string> = {
  buen_estado: 'Buen Estado',
  en_reparacion: 'En Reparación',
  rota: 'Rota',
}

const estadoColors: Record<EstadoHerramienta, string> = {
  buen_estado: 'bg-green-500 hover:bg-green-600',
  en_reparacion: 'bg-yellow-500 hover:bg-yellow-600',
  rota: 'bg-red-500 hover:bg-red-600',
}

export default function InventarioHerramientas() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState('todas')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedHerramienta, setSelectedHerramienta] = useState<Herramienta | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [verFotoUrl, setVerFotoUrl] = useState<string | null>(null)
  const [verFotoNombre, setVerFotoNombre] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  // Form states
  const [formNombre, setFormNombre] = useState('')
  const [formDescripcion, setFormDescripcion] = useState('')
  const [formEstado, setFormEstado] = useState<EstadoHerramienta>('buen_estado')
  const [formFotoPreview, setFormFotoPreview] = useState<string | null>(null)
  const [formFotoFile, setFormFotoFile] = useState<File | null>(null)

  // Queries
  const { data: herramientas, isLoading } = useQuery({
    queryKey: ['herramientas-inventario'],
    queryFn: () => herramientasService.getHerramientas(),
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: async (data: HerramientaCreate) => {
      const creada = await herramientasService.createHerramienta(data)
      if (formFotoFile) {
        return herramientasService.subirFotoHerramienta(creada.id, formFotoFile)
      }
      return creada
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['herramientas-inventario'] })
      closeDialog()
    },
    onError: (e: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al crear herramienta',
        description: e?.response?.data?.detail,
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: HerramientaUpdate }) => {
      const actualizada = await herramientasService.updateHerramienta(id, data)
      if (formFotoFile) {
        return herramientasService.subirFotoHerramienta(actualizada.id, formFotoFile)
      }
      return actualizada
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['herramientas-inventario'] })
      closeDialog()
    },
    onError: (e: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al actualizar herramienta',
        description: e?.response?.data?.detail,
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => herramientasService.deleteHerramienta(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['herramientas-inventario'] })
      setDeleteDialogOpen(false)
      setSelectedHerramienta(null)
    },
  })

  const quitarFotoMutation = useMutation({
    mutationFn: (id: string) => herramientasService.quitarFotoHerramienta(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['herramientas-inventario'] })
      setFormFotoPreview(null)
      setFormFotoFile(null)
    },
  })

  const closeDialog = () => {
    setDialogOpen(false)
    setSelectedHerramienta(null)
    setIsEditing(false)
    setFormNombre('')
    setFormDescripcion('')
    setFormEstado('buen_estado')
    setFormFotoPreview(null)
    setFormFotoFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const openCreateDialog = () => {
    setIsEditing(false)
    setFormFotoPreview(null)
    setFormFotoFile(null)
    setDialogOpen(true)
  }

  const openEditDialog = (herramienta: Herramienta) => {
    setSelectedHerramienta(herramienta)
    setFormNombre(herramienta.nombre)
    setFormDescripcion(herramienta.descripcion || '')
    setFormEstado(herramienta.estado)
    setFormFotoPreview(herramienta.foto_url || null)
    setFormFotoFile(null)
    setIsEditing(true)
    setDialogOpen(true)
  }

  const onSelectFoto = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast({ variant: 'destructive', title: 'El archivo debe ser una imagen' })
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      toast({ variant: 'destructive', title: 'Imagen demasiado grande (máx 10 MB)' })
      return
    }
    setFormFotoFile(file)
    setFormFotoPreview(URL.createObjectURL(file))
  }

  const handleQuitarFoto = () => {
    if (isEditing && selectedHerramienta?.foto_url && !formFotoFile) {
      quitarFotoMutation.mutate(selectedHerramienta.id)
    } else {
      setFormFotoFile(null)
      setFormFotoPreview(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const abrirVisorFoto = (herramienta: Herramienta) => {
    if (!herramienta.foto_url) return
    setVerFotoUrl(herramienta.foto_url)
    setVerFotoNombre(herramienta.nombre)
  }

  const openDeleteDialog = (herramienta: Herramienta) => {
    setSelectedHerramienta(herramienta)
    setDeleteDialogOpen(true)
  }

  const handleSubmit = () => {
    if (isEditing && selectedHerramienta) {
      updateMutation.mutate({
        id: selectedHerramienta.id,
        data: {
          nombre: formNombre,
          descripcion: formDescripcion || undefined,
          estado: formEstado,
        },
      })
    } else {
      createMutation.mutate({
        nombre: formNombre,
        descripcion: formDescripcion || undefined,
        estado: formEstado,
      })
    }
  }

  const handleDelete = () => {
    if (selectedHerramienta) {
      deleteMutation.mutate(selectedHerramienta.id)
    }
  }

  // Filter herramientas by tab
  const filteredHerramientas = herramientas?.filter(h => {
    if (activeTab === 'todas') return true
    if (activeTab === 'en_reparacion') return h.estado === 'en_reparacion'
    if (activeTab === 'rotas') return h.estado === 'rota'
    return true
  })

  if (isLoading) {
    return <div className="flex justify-center p-8">Cargando...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header con navegación */}
      <div className="flex items-center gap-4 mb-4">
        <Link to="/herramientas/prestamos">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Volver a Administración
          </Button>
        </Link>
      </div>

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-red-600">Inventario de Herramientas</h1>
        <Button onClick={openCreateDialog} className="bg-red-600 hover:bg-red-700">
          <Plus className="h-4 w-4 mr-2" />
          Añadir Herramienta
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="todas">Todas</TabsTrigger>
          <TabsTrigger value="en_reparacion">En Reparación</TabsTrigger>
          <TabsTrigger value="rotas">Rotas</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">Foto</TableHead>
                  <TableHead className="w-[35%]">Herramienta</TableHead>
                  <TableHead className="w-[30%]">Descripción</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredHerramientas?.map(herramienta => (
                  <TableRow key={herramienta.id}>
                    <TableCell>
                      {herramienta.foto_url ? (
                        <button
                          type="button"
                          onClick={() => abrirVisorFoto(herramienta)}
                          className="block h-12 w-12 overflow-hidden rounded-md border bg-muted hover:ring-2 hover:ring-red-500"
                          title="Ver foto"
                        >
                          <img
                            src={herramienta.foto_url}
                            alt={herramienta.nombre}
                            className="h-full w-full object-cover"
                          />
                        </button>
                      ) : (
                        <div className="flex h-12 w-12 items-center justify-center rounded-md border bg-muted text-muted-foreground">
                          <ImageIcon className="h-5 w-5" />
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="font-medium">{herramienta.nombre}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {herramienta.descripcion || '-'}
                    </TableCell>
                    <TableCell>
                      <Badge className={estadoColors[herramienta.estado]}>
                        {estadoLabels[herramienta.estado]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {herramienta.foto_url && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => abrirVisorFoto(herramienta)}
                            title="Ver foto"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(herramienta)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-red-600 hover:text-red-700"
                          onClick={() => openDeleteDialog(herramienta)}
                          disabled={herramienta.estado_prestamo === 'en_uso'}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {filteredHerramientas?.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                      No hay herramientas en esta categoría
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </TabsContent>
      </Tabs>

      {/* Dialog para crear/editar */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {isEditing ? 'Editar Herramienta' : 'Añadir Herramienta'}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? 'Modifica los datos de la herramienta.'
                : 'Registra una nueva herramienta en el inventario.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="nombre">Nombre *</Label>
              <Input
                id="nombre"
                value={formNombre}
                onChange={e => setFormNombre(e.target.value)}
                placeholder="Ej: Amoladora Bosch 900w"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="descripcion">Descripción</Label>
              <Input
                id="descripcion"
                value={formDescripcion}
                onChange={e => setFormDescripcion(e.target.value)}
                placeholder="Modelo, características, etc."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="estado">Estado</Label>
              <Select value={formEstado} onValueChange={(v: EstadoHerramienta) => setFormEstado(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="buen_estado">Buen Estado</SelectItem>
                  <SelectItem value="en_reparacion">En Reparación</SelectItem>
                  <SelectItem value="rota">Rota</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Foto</Label>
              <div className="flex items-start gap-3">
                <div className="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-md border bg-muted">
                  {formFotoPreview ? (
                    <img
                      src={formFotoPreview}
                      alt="Vista previa"
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <ImageIcon className="h-8 w-8 text-muted-foreground" />
                  )}
                </div>
                <div className="flex flex-col gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={onSelectFoto}
                    className="hidden"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    {formFotoPreview ? 'Cambiar foto' : 'Subir foto'}
                  </Button>
                  {formFotoPreview && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={handleQuitarFoto}
                      disabled={quitarFotoMutation.isPending}
                    >
                      {quitarFotoMutation.isPending ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <X className="h-4 w-4 mr-2" />
                      )}
                      Quitar foto
                    </Button>
                  )}
                  <p className="text-xs text-muted-foreground">JPG / PNG · máx 10 MB</p>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeDialog}>
              Cancelar
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!formNombre || createMutation.isPending || updateMutation.isPending}
              className="bg-red-600 hover:bg-red-700"
            >
              {createMutation.isPending || updateMutation.isPending
                ? 'Guardando...'
                : isEditing
                  ? 'Guardar Cambios'
                  : 'Añadir'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Visor de foto */}
      <Dialog open={!!verFotoUrl} onOpenChange={(o) => !o && setVerFotoUrl(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{verFotoNombre}</DialogTitle>
          </DialogHeader>
          {verFotoUrl && (
            <div className="flex justify-center">
              <img
                src={verFotoUrl}
                alt={verFotoNombre}
                className="max-h-[70vh] w-auto rounded-md"
              />
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Confirm delete dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar herramienta?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción no se puede deshacer. ¿Estás seguro de que deseas eliminar "
              {selectedHerramienta?.nombre}"?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
