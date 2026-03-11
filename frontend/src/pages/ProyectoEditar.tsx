import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Save,
  Loader2,
  Building2,
  Calendar,
  MapPin,
  DollarSign,
  User,
  Users,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { proyectosService } from '@/services/proyectos'
import { usuariosService } from '@/services/usuarios'
import { useToast } from '@/hooks/use-toast'
import type { EstadoProyecto } from '@/types'

interface ProyectoForm {
  nombre: string
  descripcion: string
  ubicacion: string
  fecha_inicio: string
  fecha_fin_estimada: string
  fecha_fin_real: string
  estado: EstadoProyecto
  monto_contratado: string
  cliente_id: string
  supervisor_id: string
}

export function ProyectoEditarPage() {
  const { proyectoId } = useParams<{ proyectoId: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState<ProyectoForm>({
    nombre: '',
    descripcion: '',
    ubicacion: '',
    fecha_inicio: '',
    fecha_fin_estimada: '',
    fecha_fin_real: '',
    estado: 'planificacion',
    monto_contratado: '',
    cliente_id: '',
    supervisor_id: '',
  })

  const { data: proyecto, isLoading: loadingProyecto } = useQuery({
    queryKey: ['proyecto', proyectoId],
    queryFn: () => proyectosService.getProyecto(proyectoId!),
    enabled: !!proyectoId,
  })

  const { data: usuarios } = useQuery({
    queryKey: ['usuarios'],
    queryFn: () => usuariosService.getUsuarios(),
  })

  const clientes = usuarios?.filter((u) => u.rol === 'cliente') || []
  const supervisores = usuarios?.filter((u) => u.rol === 'supervisor' || u.rol === 'administrador') || []

  useEffect(() => {
    if (proyecto) {
      setFormData({
        nombre: proyecto.nombre,
        descripcion: proyecto.descripcion || '',
        ubicacion: proyecto.ubicacion || '',
        fecha_inicio: proyecto.fecha_inicio || '',
        fecha_fin_estimada: proyecto.fecha_fin_estimada || '',
        fecha_fin_real: proyecto.fecha_fin_real || '',
        estado: proyecto.estado,
        monto_contratado: proyecto.monto_contratado?.toString() || '',
        cliente_id: proyecto.cliente_id || '',
        supervisor_id: proyecto.supervisor_id || '',
      })
    }
  }, [proyecto])

  const updateMutation = useMutation({
    mutationFn: (data: Partial<typeof formData>) =>
      proyectosService.updateProyecto(proyectoId!, {
        ...data,
        monto_contratado: data.monto_contratado ? parseFloat(data.monto_contratado as string) : undefined,
        cliente_id: data.cliente_id || undefined,
        supervisor_id: data.supervisor_id || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyectos'] })
      toast({ title: 'Proyecto actualizado exitosamente' })
      navigate(`/proyectos/${proyectoId}`)
    },
    onError: () => {
      toast({ variant: 'destructive', title: 'Error al actualizar proyecto' })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate(formData)
  }

  if (loadingProyecto) {
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

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Editar Proyecto</h1>
          <p className="text-muted-foreground">{proyecto.nombre}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Información básica */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Información Básica
            </CardTitle>
            <CardDescription>Datos principales del proyecto</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="nombre">Nombre del proyecto *</Label>
                <Input
                  id="nombre"
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  placeholder="Ej: Instalación eléctrica edificio central"
                  required
                />
              </div>

              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="descripcion">Descripción</Label>
                <Textarea
                  id="descripcion"
                  value={formData.descripcion}
                  onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                  placeholder="Descripción detallada del proyecto..."
                  rows={4}
                />
              </div>

              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="ubicacion" className="flex items-center gap-1">
                  <MapPin className="h-4 w-4" />
                  Ubicación
                </Label>
                <Input
                  id="ubicacion"
                  value={formData.ubicacion}
                  onChange={(e) => setFormData({ ...formData, ubicacion: e.target.value })}
                  placeholder="Dirección del proyecto"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="estado">Estado</Label>
                <Select
                  value={formData.estado}
                  onValueChange={(v) => setFormData({ ...formData, estado: v as EstadoProyecto })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="planificacion">Planificación</SelectItem>
                    <SelectItem value="en_ejecucion">En Ejecución</SelectItem>
                    <SelectItem value="pausado">Pausado</SelectItem>
                    <SelectItem value="finalizado">Finalizado</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="monto_contratado" className="flex items-center gap-1">
                  <DollarSign className="h-4 w-4" />
                  Monto Contratado
                </Label>
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
            </div>
          </CardContent>
        </Card>

        {/* Fechas */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Fechas
            </CardTitle>
            <CardDescription>Cronograma del proyecto</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="fecha_inicio">Fecha de Inicio</Label>
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

              <div className="space-y-2">
                <Label htmlFor="fecha_fin_real">Fecha Fin Real</Label>
                <Input
                  id="fecha_fin_real"
                  type="date"
                  value={formData.fecha_fin_real}
                  onChange={(e) => setFormData({ ...formData, fecha_fin_real: e.target.value })}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Asignaciones */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Asignaciones
            </CardTitle>
            <CardDescription>Cliente y supervisor del proyecto</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="cliente_id" className="flex items-center gap-1">
                  <User className="h-4 w-4" />
                  Cliente
                </Label>
                <Select
                  value={formData.cliente_id || 'none'}
                  onValueChange={(v) => setFormData({ ...formData, cliente_id: v === 'none' ? '' : v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar cliente" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sin cliente asignado</SelectItem>
                    {clientes.map((cliente) => (
                      <SelectItem key={cliente.id} value={cliente.id}>
                        {cliente.nombre} {cliente.apellido}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="supervisor_id" className="flex items-center gap-1">
                  <User className="h-4 w-4" />
                  Supervisor
                </Label>
                <Select
                  value={formData.supervisor_id || 'none'}
                  onValueChange={(v) => setFormData({ ...formData, supervisor_id: v === 'none' ? '' : v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar supervisor" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sin supervisor asignado</SelectItem>
                    {supervisores.map((sup) => (
                      <SelectItem key={sup.id} value={sup.id}>
                        {sup.nombre} {sup.apellido}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Separator />

        {/* Botones */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>
            Cancelar
          </Button>
          <Button type="submit" disabled={updateMutation.isPending || !formData.nombre}>
            {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            Guardar Cambios
          </Button>
        </div>
      </form>
    </div>
  )
}
