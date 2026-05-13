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
import { getClientes, type ClienteListItem } from '@/services/clientes'
import { depositosService } from '@/services/depositos'
import { proyectoActividadesService } from '@/services/proyectoActividades'
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
  fuente_materiales: 'ninguna' | 'global' | 'deposito'
  deposito_id: string
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
    fuente_materiales: 'ninguna',
    deposito_id: '',
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

  const { data: clientes = [] } = useQuery({
    queryKey: ['clientes'],
    queryFn: () => getClientes(),
  })

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
        fuente_materiales: proyecto.deposito_id ? 'deposito' : 'ninguna',
        deposito_id: proyecto.deposito_id || '',
      })
    }
  }, [proyecto])

  // Depositos del cliente seleccionado
  const { data: depositosCliente = [] } = useQuery({
    queryKey: ['depositos', formData.cliente_id],
    queryFn: () => depositosService.list(formData.cliente_id),
    enabled: !!formData.cliente_id,
  })

  // Actividades existentes del proyecto (para validar stock al cambiar deposito)
  const { data: actividadesProyecto = [] } = useQuery({
    queryKey: ['proyecto-actividades', proyectoId],
    queryFn: () => proyectoActividadesService.getActividades(proyectoId!),
    enabled: !!proyectoId,
  })

  const updateMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      proyectosService.updateProyecto(proyectoId!, {
        nombre: data.nombre,
        descripcion: data.descripcion || undefined,
        ubicacion: data.ubicacion || undefined,
        estado: data.estado,
        fecha_inicio: data.fecha_inicio || undefined,
        fecha_fin_estimada: data.fecha_fin_estimada || undefined,
        fecha_fin_real: data.fecha_fin_real || undefined,
        monto_contratado: data.monto_contratado ? parseFloat(data.monto_contratado) : undefined,
        cliente_id: data.cliente_id || undefined,
        supervisor_id: data.supervisor_id || undefined,
        deposito_id:
          data.fuente_materiales === 'deposito' && data.deposito_id
            ? data.deposito_id
            : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proyecto', proyectoId] })
      queryClient.invalidateQueries({ queryKey: ['proyectos'] })
      toast({ title: 'Proyecto actualizado exitosamente' })
      navigate(`/proyectos/${proyectoId}`)
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join(' | ')
        : typeof detail === 'string'
          ? detail
          : 'Error al actualizar proyecto'
      toast({ variant: 'destructive', title: 'Error al actualizar proyecto', description: msg })
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const cambioDeposito =
      formData.fuente_materiales === 'deposito' &&
      formData.deposito_id &&
      formData.deposito_id !== (proyecto?.deposito_id || '')

    if (cambioDeposito && actividadesProyecto.length > 0) {
      try {
        const verif = await proyectosService.verificarStockDeposito(
          formData.deposito_id,
          actividadesProyecto.map((a) => ({
            actividad_tipo_id: a.actividad_tipo_id,
            cantidad_planificada: Number(a.cantidad_planificada) || 1,
          }))
        )
        if (!verif.ok) {
          const lista = verif.faltantes
            .map(
              (f) =>
                `${f.material_nombre}: faltan ${Number(f.faltante).toFixed(2)} ${f.unidad || ''}`
            )
            .join(' | ')
          toast({
            variant: 'destructive',
            title: 'Stock insuficiente en el deposito elegido',
            description: lista,
          })
          return
        }
      } catch (err: any) {
        toast({
          variant: 'destructive',
          title: 'No se pudo verificar el stock',
          description: err?.response?.data?.detail || '',
        })
        return
      }
    }

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
                  onValueChange={(v) =>
                    setFormData({
                      ...formData,
                      cliente_id: v === 'none' ? '' : v,
                      // Al cambiar el cliente, resetear deposito
                      deposito_id: '',
                      fuente_materiales: 'ninguna',
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar cliente" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sin cliente asignado</SelectItem>
                    {clientes.map((cliente: ClienteListItem) => (
                      <SelectItem key={cliente.id} value={cliente.id}>
                        {cliente.nombre_fantasia || cliente.razon_social}
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

        {/* Fuente de materiales */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Fuente de materiales
            </CardTitle>
            <CardDescription>
              Donde se descuenta el stock al consumir materiales en este proyecto.
              Podés dejarlo sin asignar.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-2">
              <label className="flex items-center gap-3 p-2 rounded-md border cursor-pointer hover:bg-muted/50">
                <input
                  type="radio"
                  name="fuente_materiales_edit"
                  checked={formData.fuente_materiales === 'ninguna'}
                  onChange={() =>
                    setFormData({
                      ...formData,
                      fuente_materiales: 'ninguna',
                      deposito_id: '',
                    })
                  }
                />
                <div className="flex-1">
                  <p className="text-sm font-medium">Sin asignar</p>
                  <p className="text-xs text-muted-foreground">
                    El proyecto no descuenta stock automáticamente. Podés vincular una fuente más tarde.
                  </p>
                </div>
              </label>
              <label className="flex items-center gap-3 p-2 rounded-md border cursor-pointer hover:bg-muted/50">
                <input
                  type="radio"
                  name="fuente_materiales_edit"
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
                  name="fuente_materiales_edit"
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
                        (asigna un cliente primero)
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
