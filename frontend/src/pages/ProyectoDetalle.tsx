import { useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Plus,
  Edit,
  Trash2,
  Upload,
  Image as ImageIcon,
  Calendar,
  MapPin,
  User,
  DollarSign,
  Clock,
  CheckCircle2,
  Pause,
  Play,
  MoreVertical,
  Loader2,
  GripVertical,
  Eye,
  EyeOff,
  X,
  Package,
  Wrench,
  AlertTriangle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Slider } from '@/components/ui/slider'
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
import { Checkbox } from '@/components/ui/checkbox'
import { proyectosService } from '@/services/proyectos'
import { etapasService, type EtapaCreate, type EtapaUpdate } from '@/services/etapas'
import { fotosService } from '@/services/fotos'
import { materialesService } from '@/services/materiales'
import { gastosService } from '@/services/gastos'
import { proyectoActividadesService } from '@/services/proyectoActividades'
import { herramientasService, type Herramienta } from '@/services/herramientas'
import { formatDate, formatCurrency } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin, useIsSupervisor } from '@/store/auth'
import { ActividadesTab } from '@/components/proyecto/ActividadesTab'
import type { Etapa, EstadoEtapa, Foto, EstadoProyecto, Material, Equipo, Gasto } from '@/types'

const estadoProyectoColors: Record<EstadoProyecto, string> = {
  planificacion: 'secondary',
  en_ejecucion: 'default',
  pausado: 'warning',
  finalizado: 'success',
}

const estadoProyectoLabels: Record<EstadoProyecto, string> = {
  planificacion: 'Planificacion',
  en_ejecucion: 'En Ejecucion',
  pausado: 'Pausado',
  finalizado: 'Finalizado',
}

const estadoEtapaColors: Record<EstadoEtapa, string> = {
  pendiente: 'secondary',
  en_progreso: 'default',
  completada: 'success',
  pausada: 'warning',
}

const estadoEtapaLabels: Record<EstadoEtapa, string> = {
  pendiente: 'Pendiente',
  en_progreso: 'En Progreso',
  completada: 'Completada',
  pausada: 'Pausada',
}

const estadoEtapaIcons: Record<EstadoEtapa, React.ReactNode> = {
  pendiente: <Clock className="h-4 w-4" />,
  en_progreso: <Play className="h-4 w-4" />,
  completada: <CheckCircle2 className="h-4 w-4" />,
  pausada: <Pause className="h-4 w-4" />,
}

interface EtapaForm {
  nombre: string
  descripcion: string
  fecha_inicio_est: string
  fecha_fin_est: string
  estado: EstadoEtapa
}

const initialEtapaForm: EtapaForm = {
  nombre: '',
  descripcion: '',
  fecha_inicio_est: '',
  fecha_fin_est: '',
  estado: 'pendiente',
}

export function ProyectoDetallePage() {
  const { proyectoId } = useParams<{ proyectoId: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const isSupervisor = useIsSupervisor()
  const canEdit = isAdmin || isSupervisor
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Estados para dialogos
  const [isEtapaDialogOpen, setIsEtapaDialogOpen] = useState(false)
  const [isDeleteEtapaOpen, setIsDeleteEtapaOpen] = useState(false)
  const [selectedEtapa, setSelectedEtapa] = useState<Etapa | null>(null)
  const [etapaForm, setEtapaForm] = useState<EtapaForm>(initialEtapaForm)
  const [isEditing, setIsEditing] = useState(false)

  // Estados para fotos
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false)
  const [uploadEtapaId, setUploadEtapaId] = useState<string | undefined>()
  const [uploadDescripcion, setUploadDescripcion] = useState('')
  const [uploadVisibleCliente, setUploadVisibleCliente] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)

  // Estado para galeria
  const [selectedFoto, setSelectedFoto] = useState<Foto | null>(null)

  // Estados para asignar materiales
  const [isAsignarMaterialOpen, setIsAsignarMaterialOpen] = useState(false)
  const [selectedMaterialId, setSelectedMaterialId] = useState('')
  const [cantidadMaterial, setCantidadMaterial] = useState('')
  const [notasMaterial, setNotasMaterial] = useState('')
  const [etapaMaterialId, setEtapaMaterialId] = useState('')

  // Estados para asignar herramientas
  const [isAsignarHerramientaOpen, setIsAsignarHerramientaOpen] = useState(false)
  const [selectedHerramientas, setSelectedHerramientas] = useState<string[]>([])

  // Estados para registrar avance
  const [isRegistrarAvanceOpen, setIsRegistrarAvanceOpen] = useState(false)
  const [selectedActividadAvance, setSelectedActividadAvance] = useState<any>(null)
  const [avanceForm, setAvanceForm] = useState({
    fecha: new Date().toISOString().split('T')[0],
    cantidad: '',
    observaciones: '',
  })

  // Estados para agregar gasto
  const [isAgregarGastoOpen, setIsAgregarGastoOpen] = useState(false)
  const [gastoForm, setGastoForm] = useState({
    descripcion: '',
    monto: '',
    categoria_id: '',
    fecha: new Date().toISOString().split('T')[0],
  })

  // Queries
  const { data: proyecto, isLoading: isLoadingProyecto } = useQuery({
    queryKey: ['proyecto', proyectoId],
    queryFn: () => proyectosService.getProyecto(proyectoId!),
    enabled: !!proyectoId,
  })

  const { data: etapas, isLoading: isLoadingEtapas } = useQuery({
    queryKey: ['etapas', proyectoId],
    queryFn: () => etapasService.getEtapas(proyectoId!),
    enabled: !!proyectoId,
  })

  const { data: fotos, isLoading: isLoadingFotos } = useQuery({
    queryKey: ['fotos', proyectoId],
    queryFn: () => fotosService.getFotos(proyectoId!),
    enabled: !!proyectoId,
  })

  // Queries para materiales, equipos y gastos
  const { data: materialesAsignados } = useQuery({
    queryKey: ['proyecto-materiales', proyectoId],
    queryFn: () => materialesService.getAsignacionesProyecto(proyectoId!),
    enabled: !!proyectoId,
  })

  const { data: herramientasProyecto } = useQuery({
    queryKey: ['proyecto-herramientas', proyectoId],
    queryFn: () => proyectoActividadesService.getHerramientas(proyectoId!),
    enabled: !!proyectoId,
  })

  const { data: gastosProyecto } = useQuery({
    queryKey: ['proyecto-gastos', proyectoId],
    queryFn: () => gastosService.getGastosPorProyecto(proyectoId!),
    enabled: !!proyectoId,
  })

  const { data: actividadesProyecto } = useQuery({
    queryKey: ['proyecto-actividades', proyectoId],
    queryFn: () => proyectoActividadesService.getActividades(proyectoId!),
    enabled: !!proyectoId,
  })

  const { data: resumenActividades } = useQuery({
    queryKey: ['proyecto-actividades-resumen', proyectoId],
    queryFn: () => proyectoActividadesService.getResumen(proyectoId!),
    enabled: !!proyectoId,
  })

  // Queries para listas de seleccion
  const { data: materialesDisponibles } = useQuery({
    queryKey: ['materiales'],
    queryFn: () => materialesService.getMateriales(),
  })

  const { data: herramientasDisponibles } = useQuery({
    queryKey: ['herramientas'],
    queryFn: () => herramientasService.getHerramientas(),
  })

  const { data: categorias } = useQuery({
    queryKey: ['gastos-categorias'],
    queryFn: () => gastosService.getCategorias(),
  })

  // Mutations para etapas
  const createEtapaMutation = useMutation({
    mutationFn: (data: EtapaCreate) => etapasService.createEtapa(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etapas', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
      toast({ title: 'Etapa creada exitosamente' })
      closeEtapaDialog()
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al crear etapa' })
    },
  })

  const updateEtapaMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: EtapaUpdate }) =>
      etapasService.updateEtapa(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etapas', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
      toast({ title: 'Etapa actualizada' })
      closeEtapaDialog()
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al actualizar etapa' })
    },
  })

  const deleteEtapaMutation = useMutation({
    mutationFn: etapasService.deleteEtapa,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etapas', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
      toast({ title: 'Etapa eliminada' })
      setIsDeleteEtapaOpen(false)
      setSelectedEtapa(null)
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al eliminar etapa' })
    },
  })

  const updateAvanceMutation = useMutation({
    mutationFn: ({ id, porcentaje }: { id: string; porcentaje: number }) =>
      etapasService.updateAvance(id, porcentaje),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etapas', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
    },
  })

  // Mutations para fotos
  const deleteFotoMutation = useMutation({
    mutationFn: fotosService.deleteFoto,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fotos', proyectoId] })
      toast({ title: 'Foto eliminada' })
      setSelectedFoto(null)
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al eliminar foto' })
    },
  })

  const toggleVisibilidadMutation = useMutation({
    mutationFn: ({ id, visible }: { id: string; visible: boolean }) =>
      fotosService.updateFoto(id, { visible_cliente: visible }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fotos', proyectoId] })
      toast({ title: 'Visibilidad actualizada' })
    },
  })

  // Mutation para asignar material
  const asignarMaterialMutation = useMutation({
    mutationFn: (data: { material_id: string; proyecto_id: string; etapa_id?: string; cantidad: number; notas?: string }) =>
      materialesService.asignarMaterial(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto-materiales', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['materiales'] })
      toast({ title: 'Material asignado exitosamente' })
      setIsAsignarMaterialOpen(false)
      setSelectedMaterialId('')
      setCantidadMaterial('')
      setNotasMaterial('')
      setEtapaMaterialId('')
    },
    onError: (error: any) => {
      toast({ variant: 'destructive', title: error.response?.data?.detail || 'Error al asignar material' })
    },
  })

  // Mutation para asignar herramientas
  const asignarHerramientasMutation = useMutation({
    mutationFn: (herramientasIds: string[]) =>
      proyectoActividadesService.asignarHerramientas(proyectoId!, herramientasIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto-herramientas', proyectoId] })
      toast({ title: 'Herramientas asignadas exitosamente' })
      setIsAsignarHerramientaOpen(false)
      setSelectedHerramientas([])
    },
    onError: (error: any) => {
      toast({ variant: 'destructive', title: error.response?.data?.detail || 'Error al asignar herramientas' })
    },
  })

  // Mutation para desasignar herramienta
  const desasignarHerramientaMutation = useMutation({
    mutationFn: (herramientaId: string) =>
      proyectoActividadesService.desasignarHerramienta(proyectoId!, herramientaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto-herramientas', proyectoId] })
      toast({ title: 'Herramienta desasignada' })
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al desasignar herramienta' })
    },
  })

  // Mutation para registrar avance
  const registrarAvanceMutation = useMutation({
    mutationFn: (data: { actividadId: string; fecha: string; cantidad: number; observaciones?: string }) =>
      proyectoActividadesService.createAvance(proyectoId!, data.actividadId, {
        fecha: data.fecha,
        cantidad: data.cantidad,
        observaciones: data.observaciones,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto-actividades-resumen', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
      toast({ title: 'Avance registrado exitosamente' })
      setIsRegistrarAvanceOpen(false)
      setSelectedActividadAvance(null)
      setAvanceForm({
        fecha: new Date().toISOString().split('T')[0],
        cantidad: '',
        observaciones: '',
      })
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al registrar avance' })
    },
  })

  // Mutation para crear gasto
  const crearGastoMutation = useMutation({
    mutationFn: (data: Partial<Gasto>) => gastosService.createGasto(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto-gastos', proyectoId] })
      toast({ title: 'Gasto registrado exitosamente' })
      setIsAgregarGastoOpen(false)
      setGastoForm({
        descripcion: '',
        monto: '',
        categoria_id: '',
        fecha: new Date().toISOString().split('T')[0],
      })
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al registrar gasto' })
    },
  })

  // Handlers
  const closeEtapaDialog = () => {
    setIsEtapaDialogOpen(false)
    setSelectedEtapa(null)
    setEtapaForm(initialEtapaForm)
    setIsEditing(false)
  }

  const openCreateEtapa = () => {
    setIsEditing(false)
    setEtapaForm(initialEtapaForm)
    setIsEtapaDialogOpen(true)
  }

  const openEditEtapa = (etapa: Etapa) => {
    setIsEditing(true)
    setSelectedEtapa(etapa)
    setEtapaForm({
      nombre: etapa.nombre,
      descripcion: etapa.descripcion || '',
      fecha_inicio_est: etapa.fecha_inicio_est || '',
      fecha_fin_est: etapa.fecha_fin_est || '',
      estado: etapa.estado,
    })
    setIsEtapaDialogOpen(true)
  }

  const handleEtapaSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isEditing && selectedEtapa) {
      updateEtapaMutation.mutate({
        id: selectedEtapa.id,
        data: {
          nombre: etapaForm.nombre,
          descripcion: etapaForm.descripcion || undefined,
          fecha_inicio_est: etapaForm.fecha_inicio_est || undefined,
          fecha_fin_est: etapaForm.fecha_fin_est || undefined,
          estado: etapaForm.estado,
        },
      })
    } else {
      createEtapaMutation.mutate({
        proyecto_id: proyectoId!,
        nombre: etapaForm.nombre,
        descripcion: etapaForm.descripcion || undefined,
        fecha_inicio_est: etapaForm.fecha_inicio_est || undefined,
        fecha_fin_est: etapaForm.fecha_fin_est || undefined,
        estado: etapaForm.estado,
      })
    }
  }

  const handleAvanceChange = (etapaId: string, value: number[]) => {
    updateAvanceMutation.mutate({ id: etapaId, porcentaje: value[0] })
  }

  const openUploadDialog = (etapaId?: string) => {
    setUploadEtapaId(etapaId)
    setUploadDescripcion('')
    setUploadVisibleCliente(false)
    setSelectedFiles([])
    setIsUploadDialogOpen(true)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return

    setIsUploading(true)
    try {
      for (const file of selectedFiles) {
        await fotosService.uploadFotoProyecto(
          file,
          proyectoId!,
          uploadEtapaId,
          uploadDescripcion,
          uploadVisibleCliente
        )
      }
      queryClient.invalidateQueries({ queryKey: ['fotos', proyectoId] })
      toast({ title: `${selectedFiles.length} foto(s) subida(s) exitosamente` })
      setIsUploadDialogOpen(false)
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error al subir fotos' })
    } finally {
      setIsUploading(false)
    }
  }

  const handleAsignarMaterial = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedMaterialId || !cantidadMaterial) return
    asignarMaterialMutation.mutate({
      material_id: selectedMaterialId,
      proyecto_id: proyectoId!,
      etapa_id: etapaMaterialId || undefined,
      cantidad: parseFloat(cantidadMaterial),
      notas: notasMaterial || undefined,
    })
  }

  const handleCrearGasto = (e: React.FormEvent) => {
    e.preventDefault()
    if (!gastoForm.descripcion || !gastoForm.monto) return
    crearGastoMutation.mutate({
      proyecto_id: proyectoId!,
      descripcion: gastoForm.descripcion,
      monto: parseFloat(gastoForm.monto),
      categoria_id: gastoForm.categoria_id || undefined,
      fecha: gastoForm.fecha,
    })
  }

  const openAvanceDialog = (actividad: any) => {
    setSelectedActividadAvance(actividad)
    setAvanceForm({
      fecha: new Date().toISOString().split('T')[0],
      cantidad: '',
      observaciones: '',
    })
    setIsRegistrarAvanceOpen(true)
  }

  const handleRegistrarAvance = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedActividadAvance || !avanceForm.cantidad) return

    registrarAvanceMutation.mutate({
      actividadId: selectedActividadAvance.id,
      fecha: avanceForm.fecha,
      cantidad: parseFloat(avanceForm.cantidad),
      observaciones: avanceForm.observaciones || undefined,
    })
  }

  if (isLoadingProyecto) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!proyecto) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Proyecto no encontrado</p>
        <Button variant="link" onClick={() => navigate('/proyectos')}>
          Volver a proyectos
        </Button>
      </div>
    )
  }

  const fotosGenerales = fotos?.filter((f) => !f.etapa_id) || []
  const totalGastos = gastosProyecto?.reduce((sum, g) => sum + Number(g.monto), 0) || 0
  const totalMateriales = materialesAsignados?.reduce((sum, m) => sum + (m.cantidad * (m.material?.precio_unitario || 0)), 0) || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/proyectos')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{proyecto.nombre}</h1>
            <Badge variant={estadoProyectoColors[proyecto.estado] as any}>
              {estadoProyectoLabels[proyecto.estado]}
            </Badge>
          </div>
          {proyecto.ubicacion && (
            <p className="text-muted-foreground flex items-center gap-1 mt-1">
              <MapPin className="h-4 w-4" />
              {proyecto.ubicacion}
            </p>
          )}
        </div>
        {isAdmin && (
          <Button variant="outline" asChild>
            <Link to={`/proyectos/${proyectoId}/editar`}>
              <Edit className="h-4 w-4 mr-2" />
              Editar
            </Link>
          </Button>
        )}
      </div>

      {/* Info Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avance General
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Number(proyecto.porcentaje_avance).toFixed(0)}%
            </div>
            <Progress value={Number(proyecto.porcentaje_avance)} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              Fechas
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1">
            <p>Inicio: {proyecto.fecha_inicio ? formatDate(proyecto.fecha_inicio) : '-'}</p>
            <p>Fin Est.: {proyecto.fecha_fin_estimada ? formatDate(proyecto.fecha_fin_estimada) : '-'}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <DollarSign className="h-4 w-4" />
              Monto Contratado
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {proyecto.monto_contratado ? formatCurrency(proyecto.monto_contratado) : '-'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <User className="h-4 w-4" />
              Cliente
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-medium">
              {proyecto.cliente
                ? `${proyecto.cliente.nombre} ${proyecto.cliente.apellido}`
                : 'Sin asignar'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="tareas">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="tareas" className="flex items-center gap-2">
            <Play className="h-4 w-4" />
            <span className="hidden sm:inline">Tareas</span>
            <Badge variant="secondary" className="ml-1">{actividadesProyecto?.length || 0}</Badge>
          </TabsTrigger>
          <TabsTrigger value="materiales" className="flex items-center gap-2">
            <Package className="h-4 w-4" />
            <span className="hidden sm:inline">Materiales</span>
            <Badge variant="secondary" className="ml-1">{resumenActividades?.materiales_totales?.length || 0}</Badge>
          </TabsTrigger>
          <TabsTrigger value="herramientas" className="flex items-center gap-2">
            <Wrench className="h-4 w-4" />
            <span className="hidden sm:inline">Inventario</span>
            <Badge variant="secondary" className="ml-1">{herramientasProyecto?.length || 0}</Badge>
          </TabsTrigger>
          <TabsTrigger value="avances" className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span className="hidden sm:inline">Avances</span>
          </TabsTrigger>
          <TabsTrigger value="fotos" className="flex items-center gap-2">
            <ImageIcon className="h-4 w-4" />
            <span className="hidden sm:inline">Fotos</span>
            <Badge variant="secondary" className="ml-1">{fotos?.length || 0}</Badge>
          </TabsTrigger>
        </TabsList>

        {/* Tareas Tab */}
        <TabsContent value="tareas" className="space-y-4">
          <ActividadesTab proyectoId={proyectoId!} proyectoNombre={proyecto.nombre} canEdit={canEdit} />
        </TabsContent>

        {/* Etapas Tab - OCULTO */}
        <TabsContent value="etapas-hidden" className="space-y-4 hidden">
          <div className="flex justify-between items-center">
            <p className="text-muted-foreground">
              Gestiona las etapas del proyecto y actualiza su avance
            </p>
            {canEdit && (
              <Button onClick={openCreateEtapa}>
                <Plus className="h-4 w-4 mr-2" />
                Nueva Etapa
              </Button>
            )}
          </div>

          {isLoadingEtapas ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="py-4">
                    <div className="h-6 bg-muted rounded w-1/3 mb-2" />
                    <div className="h-4 bg-muted rounded w-1/2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : etapas?.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-muted-foreground mb-4">
                  No hay etapas definidas para este proyecto
                </p>
                {canEdit && (
                  <Button onClick={openCreateEtapa}>
                    <Plus className="h-4 w-4 mr-2" />
                    Crear primera etapa
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {etapas?.sort((a, b) => a.orden - b.orden).map((etapa) => {
                const etapaFotos = fotos?.filter((f) => f.etapa_id === etapa.id) || []
                return (
                  <Card key={etapa.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="text-muted-foreground cursor-grab">
                            <GripVertical className="h-5 w-5" />
                          </div>
                          <div>
                            <CardTitle className="text-lg flex items-center gap-2">
                              {etapa.nombre}
                              <Badge variant={estadoEtapaColors[etapa.estado] as any} className="gap-1">
                                {estadoEtapaIcons[etapa.estado]}
                                {estadoEtapaLabels[etapa.estado]}
                              </Badge>
                            </CardTitle>
                            {etapa.descripcion && (
                              <CardDescription>{etapa.descripcion}</CardDescription>
                            )}
                          </div>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openUploadDialog(etapa.id)}>
                              <Upload className="h-4 w-4 mr-2" />
                              Subir fotos
                            </DropdownMenuItem>
                            {canEdit && (
                              <>
                                <DropdownMenuItem onClick={() => openEditEtapa(etapa)}>
                                  <Edit className="h-4 w-4 mr-2" />
                                  Editar
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={() => {
                                    setSelectedEtapa(etapa)
                                    setIsDeleteEtapaOpen(true)
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
                      {/* Fechas */}
                      <div className="flex gap-4 text-sm text-muted-foreground">
                        {etapa.fecha_inicio_est && (
                          <span>Inicio Est.: {formatDate(etapa.fecha_inicio_est)}</span>
                        )}
                        {etapa.fecha_fin_est && (
                          <span>Fin Est.: {formatDate(etapa.fecha_fin_est)}</span>
                        )}
                      </div>

                      {/* Avance slider */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Avance</span>
                          <span className="text-sm font-bold">
                            {Number(etapa.porcentaje_avance).toFixed(0)}%
                          </span>
                        </div>
                        <Slider
                          value={[Number(etapa.porcentaje_avance)]}
                          max={100}
                          step={5}
                          onValueCommit={(value) => handleAvanceChange(etapa.id, value)}
                          disabled={!canEdit && etapa.estado === 'completada'}
                        />
                      </div>

                      {/* Fotos de la etapa */}
                      {etapaFotos.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-sm font-medium flex items-center gap-1">
                            <ImageIcon className="h-4 w-4" />
                            Fotos ({etapaFotos.length})
                          </p>
                          <div className="flex gap-2 flex-wrap">
                            {etapaFotos.slice(0, 4).map((foto) => (
                              <button
                                key={foto.id}
                                onClick={() => setSelectedFoto(foto)}
                                className="relative w-20 h-20 rounded-md overflow-hidden border hover:opacity-80 transition-opacity"
                              >
                                <img
                                  src={foto.thumbnail_url || foto.url}
                                  alt={foto.descripcion || 'Foto'}
                                  className="w-full h-full object-cover"
                                />
                                {foto.visible_cliente && (
                                  <div className="absolute top-1 right-1 bg-green-500 rounded-full p-0.5">
                                    <Eye className="h-3 w-3 text-white" />
                                  </div>
                                )}
                              </button>
                            ))}
                            {etapaFotos.length > 4 && (
                              <div className="w-20 h-20 rounded-md bg-muted flex items-center justify-center text-sm font-medium">
                                +{etapaFotos.length - 4}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </TabsContent>

        {/* Materiales Tab */}
        <TabsContent value="materiales" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-muted-foreground">
                Materiales necesarios según las tareas del proyecto
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Calculados automáticamente en base a las tareas asignadas
              </p>
            </div>
          </div>

          {!resumenActividades?.materiales_totales || resumenActividades.materiales_totales.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">
                  No hay materiales calculados
                </p>
                <p className="text-sm text-muted-foreground">
                  Los materiales se calculan automáticamente al asignar tareas al proyecto
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Material</TableHead>
                    <TableHead className="text-right">Cantidad Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {resumenActividades.materiales_totales.map((mat) => (
                    <TableRow key={mat.material_id}>
                      <TableCell className="font-medium">
                        {mat.material_nombre}
                      </TableCell>
                      <TableCell className="text-right">
                        {Number(mat.cantidad_total).toFixed(2)} {mat.unidad}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>

        {/* Inventario Tab */}
        <TabsContent value="herramientas" className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-muted-foreground">
              Herramientas del inventario asignadas a este proyecto
            </p>
            {canEdit && (
              <Button onClick={() => setIsAsignarHerramientaOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Asignar del Inventario
              </Button>
            )}
          </div>

          {!herramientasProyecto || herramientasProyecto.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <Wrench className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">
                  No hay herramientas del inventario asignadas a este proyecto
                </p>
                {canEdit && (
                  <Button onClick={() => setIsAsignarHerramientaOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Asignar del inventario
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {herramientasProyecto.map((asignacion: any) => (
                <Card key={asignacion.id}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base">
                          {asignacion.herramienta_nombre || 'Herramienta'}
                        </CardTitle>
                        {asignacion.herramienta_codigo && (
                          <CardDescription>
                            {asignacion.herramienta_codigo}
                          </CardDescription>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Asignado:</span>
                      <span>{asignacion.fecha_asignacion ? formatDate(asignacion.fecha_asignacion) : '-'}</span>
                    </div>
                    {asignacion.observaciones && (
                      <div className="text-muted-foreground text-xs">
                        {asignacion.observaciones}
                      </div>
                    )}
                    {canEdit && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full mt-2"
                        onClick={() => desasignarHerramientaMutation.mutate(asignacion.herramienta_id)}
                        disabled={desasignarHerramientaMutation.isPending}
                      >
                        <X className="h-4 w-4 mr-2" />
                        Desasignar
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Avances Tab */}
        <TabsContent value="avances" className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-muted-foreground">
              Historial de avances registrados en las tareas del proyecto
            </p>
          </div>

          {resumenActividades && (
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Total Tareas
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{resumenActividades.total_actividades}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    Completadas
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">
                    {resumenActividades.actividades_completadas}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                    <Play className="h-4 w-4 text-blue-600" />
                    En Progreso
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">
                    {resumenActividades.actividades_en_progreso}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                    <Clock className="h-4 w-4 text-gray-600" />
                    Pendientes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-gray-600">
                    {resumenActividades.actividades_pendientes}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Avance Global */}
          {resumenActividades && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Avance Global del Proyecto</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  <Progress value={Number(resumenActividades.porcentaje_avance_global)} className="flex-1" />
                  <span className="text-lg font-bold">
                    {Number(resumenActividades.porcentaje_avance_global).toFixed(1)}%
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Lista de tareas con su avance */}
          {actividadesProyecto?.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <CheckCircle2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  No hay tareas asignadas a este proyecto
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Detalle de Avance por Tarea</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tarea</TableHead>
                      <TableHead>Categoría</TableHead>
                      <TableHead>Ejecutado / Planificado</TableHead>
                      <TableHead>Avance</TableHead>
                      <TableHead>Estado</TableHead>
                      {canEdit && <TableHead className="text-right">Acciones</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {actividadesProyecto?.map((actividad) => (
                      <TableRow key={actividad.id}>
                        <TableCell className="font-medium">
                          <div>
                            <span className="font-mono text-xs text-muted-foreground mr-2">
                              {actividad.actividad_codigo}
                            </span>
                            {actividad.actividad_nombre}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{actividad.actividad_categoria}</Badge>
                        </TableCell>
                        <TableCell>
                          {actividad.cantidad_ejecutada} / {actividad.cantidad_planificada} {actividad.unidad_trabajo}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2 w-24">
                            <Progress value={Number(actividad.porcentaje_avance)} className="flex-1 h-2" />
                            <span className="text-sm font-medium">
                              {Number(actividad.porcentaje_avance).toFixed(0)}%
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={
                            Number(actividad.porcentaje_avance) >= 100 ? 'default' :
                            Number(actividad.porcentaje_avance) > 0 ? 'secondary' : 'outline'
                          }>
                            {Number(actividad.porcentaje_avance) >= 100 ? 'Completada' :
                             Number(actividad.porcentaje_avance) > 0 ? 'En Progreso' : 'Pendiente'}
                          </Badge>
                        </TableCell>
                        {canEdit && (
                          <TableCell className="text-right">
                            {Number(actividad.porcentaje_avance) < 100 && (
                              <Button
                                size="sm"
                                onClick={() => openAvanceDialog(actividad)}
                              >
                                <Plus className="h-4 w-4 mr-1" />
                                Registrar Avance
                              </Button>
                            )}
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Fotos Tab */}
        <TabsContent value="fotos" className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-muted-foreground">
              Galeria de fotos del proyecto
            </p>
            <Button onClick={() => openUploadDialog()}>
              <Upload className="h-4 w-4 mr-2" />
              Subir Fotos
            </Button>
          </div>

          {isLoadingFotos ? (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="aspect-square bg-muted rounded-lg animate-pulse" />
              ))}
            </div>
          ) : fotos?.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <ImageIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">
                  No hay fotos en este proyecto
                </p>
                <Button onClick={() => openUploadDialog()}>
                  <Upload className="h-4 w-4 mr-2" />
                  Subir primera foto
                </Button>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Fotos generales */}
              {fotosGenerales.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-medium">Fotos Generales</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {fotosGenerales.map((foto) => (
                      <button
                        key={foto.id}
                        onClick={() => setSelectedFoto(foto)}
                        className="relative aspect-square rounded-lg overflow-hidden border hover:opacity-80 transition-opacity"
                      >
                        <img
                          src={foto.thumbnail_url || foto.url}
                          alt={foto.descripcion || 'Foto'}
                          className="w-full h-full object-cover"
                        />
                        {foto.visible_cliente && (
                          <div className="absolute top-2 right-2 bg-green-500 rounded-full p-1">
                            <Eye className="h-4 w-4 text-white" />
                          </div>
                        )}
                        <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1 truncate">
                          {formatDate(foto.fecha)}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Fotos por etapa */}
              {etapas?.map((etapa) => {
                const etapaFotos = fotos?.filter((f) => f.etapa_id === etapa.id) || []
                if (etapaFotos.length === 0) return null
                return (
                  <div key={etapa.id} className="space-y-2">
                    <h3 className="font-medium">{etapa.nombre}</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                      {etapaFotos.map((foto) => (
                        <button
                          key={foto.id}
                          onClick={() => setSelectedFoto(foto)}
                          className="relative aspect-square rounded-lg overflow-hidden border hover:opacity-80 transition-opacity"
                        >
                          <img
                            src={foto.thumbnail_url || foto.url}
                            alt={foto.descripcion || 'Foto'}
                            className="w-full h-full object-cover"
                          />
                          {foto.visible_cliente && (
                            <div className="absolute top-2 right-2 bg-green-500 rounded-full p-1">
                              <Eye className="h-4 w-4 text-white" />
                            </div>
                          )}
                          <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1 truncate">
                            {formatDate(foto.fecha)}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )
              })}
            </>
          )}
        </TabsContent>
      </Tabs>

      {/* Etapa Dialog */}
      <Dialog open={isEtapaDialogOpen} onOpenChange={setIsEtapaDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {isEditing ? 'Editar Etapa' : 'Nueva Etapa'}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? 'Modifica los datos de la etapa'
                : 'Ingresa los datos de la nueva etapa'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEtapaSubmit}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre *</Label>
                <Input
                  id="nombre"
                  value={etapaForm.nombre}
                  onChange={(e) => setEtapaForm({ ...etapaForm, nombre: e.target.value })}
                  placeholder="Ej: Demolicion, Cimentacion, Estructura..."
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="descripcion">Descripcion</Label>
                <Textarea
                  id="descripcion"
                  value={etapaForm.descripcion}
                  onChange={(e) => setEtapaForm({ ...etapaForm, descripcion: e.target.value })}
                  placeholder="Descripcion de las tareas de esta etapa"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="fecha_inicio_est">Fecha Inicio Est.</Label>
                  <Input
                    id="fecha_inicio_est"
                    type="date"
                    value={etapaForm.fecha_inicio_est}
                    onChange={(e) =>
                      setEtapaForm({ ...etapaForm, fecha_inicio_est: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fecha_fin_est">Fecha Fin Est.</Label>
                  <Input
                    id="fecha_fin_est"
                    type="date"
                    value={etapaForm.fecha_fin_est}
                    onChange={(e) =>
                      setEtapaForm({ ...etapaForm, fecha_fin_est: e.target.value })
                    }
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="estado">Estado</Label>
                <Select
                  value={etapaForm.estado}
                  onValueChange={(v) => setEtapaForm({ ...etapaForm, estado: v as EstadoEtapa })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pendiente">Pendiente</SelectItem>
                    <SelectItem value="en_progreso">En Progreso</SelectItem>
                    <SelectItem value="completada">Completada</SelectItem>
                    <SelectItem value="pausada">Pausada</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeEtapaDialog}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={
                  createEtapaMutation.isPending ||
                  updateEtapaMutation.isPending ||
                  !etapaForm.nombre
                }
              >
                {(createEtapaMutation.isPending || updateEtapaMutation.isPending) && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {isEditing ? 'Guardar' : 'Crear'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Etapa Dialog */}
      <Dialog open={isDeleteEtapaOpen} onOpenChange={setIsDeleteEtapaOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar etapa</DialogTitle>
            <DialogDescription>
              Estas seguro de eliminar "{selectedEtapa?.nombre}"? Esta accion no se puede
              deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteEtapaOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => selectedEtapa && deleteEtapaMutation.mutate(selectedEtapa.id)}
              disabled={deleteEtapaMutation.isPending}
            >
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Dialog */}
      <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Subir Fotos</DialogTitle>
            <DialogDescription>
              Selecciona las fotos que deseas subir
              {uploadEtapaId && etapas && (
                <> a la etapa "{etapas.find((e) => e.id === uploadEtapaId)?.nombre}"</>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Archivos</Label>
              <Input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileSelect}
              />
              {selectedFiles.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  {selectedFiles.length} archivo(s) seleccionado(s)
                </p>
              )}
            </div>

            {!uploadEtapaId && (
              <div className="space-y-2">
                <Label>Etapa (opcional)</Label>
                <Select
                  value={uploadEtapaId || 'none'}
                  onValueChange={(v) => setUploadEtapaId(v === 'none' ? undefined : v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sin etapa especifica" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sin etapa especifica</SelectItem>
                    {etapas?.map((etapa) => (
                      <SelectItem key={etapa.id} value={etapa.id}>
                        {etapa.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="descripcion">Descripcion</Label>
              <Textarea
                id="descripcion"
                value={uploadDescripcion}
                onChange={(e) => setUploadDescripcion(e.target.value)}
                placeholder="Descripcion de las fotos"
                rows={2}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="visible_cliente"
                checked={uploadVisibleCliente}
                onCheckedChange={(checked) => setUploadVisibleCliente(checked as boolean)}
              />
              <Label htmlFor="visible_cliente" className="text-sm font-normal">
                Visible para el cliente
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsUploadDialogOpen(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleUpload}
              disabled={isUploading || selectedFiles.length === 0}
            >
              {isUploading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Subir {selectedFiles.length > 0 && `(${selectedFiles.length})`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Photo Preview Dialog */}
      <Dialog open={!!selectedFoto} onOpenChange={() => setSelectedFoto(null)}>
        <DialogContent className="sm:max-w-[800px] p-0">
          {selectedFoto && (
            <div>
              <div className="relative">
                <img
                  src={selectedFoto.url}
                  alt={selectedFoto.descripcion || 'Foto'}
                  className="w-full max-h-[70vh] object-contain"
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 text-white"
                  onClick={() => setSelectedFoto(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <div className="p-4 space-y-3">
                {selectedFoto.descripcion && (
                  <p className="text-sm">{selectedFoto.descripcion}</p>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    {formatDate(selectedFoto.fecha)}
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        toggleVisibilidadMutation.mutate({
                          id: selectedFoto.id,
                          visible: !selectedFoto.visible_cliente,
                        })
                      }
                    >
                      {selectedFoto.visible_cliente ? (
                        <>
                          <EyeOff className="h-4 w-4 mr-1" />
                          Ocultar al cliente
                        </>
                      ) : (
                        <>
                          <Eye className="h-4 w-4 mr-1" />
                          Mostrar al cliente
                        </>
                      )}
                    </Button>
                    {isAdmin && (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => deleteFotoMutation.mutate(selectedFoto.id)}
                        disabled={deleteFotoMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Eliminar
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Asignar Material Dialog */}
      <Dialog open={isAsignarMaterialOpen} onOpenChange={setIsAsignarMaterialOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Asignar Material</DialogTitle>
            <DialogDescription>
              Selecciona un material del inventario para asignar a este proyecto
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAsignarMaterial}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Material *</Label>
                <Select value={selectedMaterialId} onValueChange={setSelectedMaterialId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar material" />
                  </SelectTrigger>
                  <SelectContent>
                    {materialesDisponibles?.map((material) => (
                      <SelectItem key={material.id} value={material.id}>
                        <div className="flex items-center justify-between w-full">
                          <span>{material.nombre}</span>
                          <span className="text-muted-foreground ml-2">
                            (Stock: {material.stock_actual} {material.unidad})
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Cantidad *</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={cantidadMaterial}
                  onChange={(e) => setCantidadMaterial(e.target.value)}
                  placeholder="Cantidad a asignar"
                  required
                />
                {selectedMaterialId && materialesDisponibles && (
                  <p className="text-xs text-muted-foreground">
                    Stock disponible: {materialesDisponibles.find(m => m.id === selectedMaterialId)?.stock_actual || 0}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>Etapa (opcional)</Label>
                <Select value={etapaMaterialId} onValueChange={setEtapaMaterialId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Sin etapa especifica" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Sin etapa especifica</SelectItem>
                    {etapas?.map((etapa) => (
                      <SelectItem key={etapa.id} value={etapa.id}>
                        {etapa.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Notas</Label>
                <Textarea
                  value={notasMaterial}
                  onChange={(e) => setNotasMaterial(e.target.value)}
                  placeholder="Observaciones adicionales"
                  rows={2}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsAsignarMaterialOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={asignarMaterialMutation.isPending || !selectedMaterialId || !cantidadMaterial}
              >
                {asignarMaterialMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Asignar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Asignar del Inventario Dialog */}
      <Dialog open={isAsignarHerramientaOpen} onOpenChange={setIsAsignarHerramientaOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Asignar del Inventario</DialogTitle>
            <DialogDescription>
              Selecciona las herramientas del inventario que deseas asignar a este proyecto
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="space-y-4 max-h-[400px] overflow-y-auto">
              {!herramientasDisponibles || herramientasDisponibles.length === 0 ? (
                <div className="flex items-center gap-2 text-amber-600 bg-amber-50 p-3 rounded-md">
                  <AlertTriangle className="h-4 w-4" />
                  <p className="text-sm">No hay herramientas en el inventario</p>
                </div>
              ) : (
                herramientasDisponibles
                  ?.filter(h => !herramientasProyecto?.some((hp: any) => hp.herramienta_id === h.id))
                  ?.map((herramienta) => {
                    const isSelected = selectedHerramientas.includes(herramienta.id)
                    const estadoLabel = herramienta.estado_prestamo === 'disponible' ? 'Disponible' : 'En uso'
                    const estadoColor = herramienta.estado_prestamo === 'disponible' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    return (
                      <div
                        key={herramienta.id}
                        className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                          isSelected ? 'bg-primary/10 border-primary' : 'hover:bg-muted'
                        }`}
                        onClick={() => {
                          if (isSelected) {
                            setSelectedHerramientas(selectedHerramientas.filter(id => id !== herramienta.id))
                          } else {
                            setSelectedHerramientas([...selectedHerramientas, herramienta.id])
                          }
                        }}
                      >
                        <Checkbox checked={isSelected} />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{herramienta.nombre}</span>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${estadoColor}`}>
                              {estadoLabel}
                            </span>
                          </div>
                          {herramienta.descripcion && (
                            <div className="text-sm text-muted-foreground">
                              {herramienta.descripcion}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })
              )}
            </div>
            {selectedHerramientas.length > 0 && (
              <div className="mt-4 p-2 bg-muted rounded-md">
                <p className="text-sm font-medium">{selectedHerramientas.length} herramienta(s) seleccionada(s)</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => {
              setIsAsignarHerramientaOpen(false)
              setSelectedHerramientas([])
            }}>
              Cancelar
            </Button>
            <Button
              onClick={() => asignarHerramientasMutation.mutate(selectedHerramientas)}
              disabled={asignarHerramientasMutation.isPending || selectedHerramientas.length === 0}
            >
              {asignarHerramientasMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Asignar ({selectedHerramientas.length})
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Agregar Gasto Dialog */}
      <Dialog open={isAgregarGastoOpen} onOpenChange={setIsAgregarGastoOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Registrar Gasto</DialogTitle>
            <DialogDescription>
              Registra un nuevo gasto asociado a este proyecto
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCrearGasto}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Descripcion *</Label>
                <Input
                  value={gastoForm.descripcion}
                  onChange={(e) => setGastoForm({ ...gastoForm, descripcion: e.target.value })}
                  placeholder="Ej: Combustible, Transporte, Herramientas..."
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Monto *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={gastoForm.monto}
                    onChange={(e) => setGastoForm({ ...gastoForm, monto: e.target.value })}
                    placeholder="0.00"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label>Fecha</Label>
                  <Input
                    type="date"
                    value={gastoForm.fecha}
                    onChange={(e) => setGastoForm({ ...gastoForm, fecha: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Categoria</Label>
                <Select
                  value={gastoForm.categoria_id}
                  onValueChange={(v) => setGastoForm({ ...gastoForm, categoria_id: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar categoria" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Sin categoria</SelectItem>
                    {categorias?.map((cat) => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {cat.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsAgregarGastoOpen(false)}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={crearGastoMutation.isPending || !gastoForm.descripcion || !gastoForm.monto}
              >
                {crearGastoMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Registrar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Registrar Avance Dialog */}
      <Dialog open={isRegistrarAvanceOpen} onOpenChange={setIsRegistrarAvanceOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Registrar Avance</DialogTitle>
            <DialogDescription>
              {selectedActividadAvance && (
                <span>
                  {selectedActividadAvance.actividad_nombre} - Pendiente:{' '}
                  {(Number(selectedActividadAvance.cantidad_planificada) - Number(selectedActividadAvance.cantidad_ejecutada)).toFixed(2)}{' '}
                  {selectedActividadAvance.unidad_trabajo}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleRegistrarAvance} className="space-y-4">
            <div className="space-y-2">
              <Label>Fecha</Label>
              <Input
                type="date"
                value={avanceForm.fecha}
                onChange={(e) => setAvanceForm({ ...avanceForm, fecha: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label>
                Cantidad ({selectedActividadAvance?.unidad_trabajo})
              </Label>
              <Input
                type="number"
                value={avanceForm.cantidad}
                onChange={(e) => setAvanceForm({ ...avanceForm, cantidad: e.target.value })}
                min={0.01}
                step={0.01}
                max={
                  selectedActividadAvance
                    ? selectedActividadAvance.cantidad_planificada - selectedActividadAvance.cantidad_ejecutada
                    : undefined
                }
                required
              />
              {selectedActividadAvance && (
                <p className="text-xs text-muted-foreground">
                  Máximo: {(Number(selectedActividadAvance.cantidad_planificada) - Number(selectedActividadAvance.cantidad_ejecutada)).toFixed(2)}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Observaciones (opcional)</Label>
              <Textarea
                value={avanceForm.observaciones}
                onChange={(e) => setAvanceForm({ ...avanceForm, observaciones: e.target.value })}
                placeholder="Notas sobre el trabajo realizado..."
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsRegistrarAvanceOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={registrarAvanceMutation.isPending}>
                {registrarAvanceMutation.isPending && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                Registrar Avance
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
