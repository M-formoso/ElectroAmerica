import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Loader2, Truck, MapPin, Package, Play, AlertCircle } from 'lucide-react'
import { jornadasOperarioService, asignacionesDiariasService, type IniciarJornadaRequest, type MaterialCargar } from '@/services/jornadasOperario'
import { equiposService } from '@/services/equipos'
import { proyectosService } from '@/services/proyectos'
import { materialesService } from '@/services/materiales'
import { useAuthStore } from '@/store/auth'

export default function IniciarJornada() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()

  // Estados del formulario
  const [vehiculoId, setVehiculoId] = useState('')
  const [proyectoId, setProyectoId] = useState('')
  const [etapaId, setEtapaId] = useState('')
  const [kmInicial, setKmInicial] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [materialesSeleccionados, setMaterialesSeleccionados] = useState<MaterialCargar[]>([])
  const [asignacionSeleccionada, setAsignacionSeleccionada] = useState<string | null>(null)

  // Verificar si ya tiene jornada activa
  const { data: jornadaActiva, isLoading: loadingJornada } = useQuery({
    queryKey: ['mi-jornada-activa'],
    queryFn: jornadasOperarioService.getMiJornadaActiva,
  })

  // Cargar asignaciones del día
  const { data: asignacionesHoy } = useQuery({
    queryKey: ['mis-asignaciones-hoy'],
    queryFn: asignacionesDiariasService.getMisAsignacionesHoy,
  })

  // Cargar vehículos disponibles
  const { data: vehiculos } = useQuery({
    queryKey: ['vehiculos-disponibles'],
    queryFn: async () => {
      const equipos = await equiposService.getEquipos({ tipo: 'vehiculo' })
      return equipos.filter(e => e.estado === 'disponible')
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
    queryKey: ['etapas-proyecto', proyectoId],
    queryFn: () => proyectosService.getEtapas(proyectoId),
    enabled: !!proyectoId,
  })

  // Cargar materiales disponibles
  const { data: materiales } = useQuery({
    queryKey: ['materiales-disponibles'],
    queryFn: () => materialesService.getMateriales(),
  })

  // Mutation para iniciar jornada
  const iniciarJornadaMutation = useMutation({
    mutationFn: (data: { request: IniciarJornadaRequest; asignacionId?: string }) =>
      jornadasOperarioService.iniciarJornada(data.request, data.asignacionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mi-jornada-activa'] })
      navigate('/operario/jornada-activa')
    },
  })

  // Si tiene jornada activa, redirigir
  useEffect(() => {
    if (jornadaActiva && !loadingJornada) {
      navigate('/operario/jornada-activa')
    }
  }, [jornadaActiva, loadingJornada, navigate])

  // Cargar datos de asignación seleccionada
  useEffect(() => {
    if (asignacionSeleccionada && asignacionesHoy) {
      const asignacion = asignacionesHoy.find(a => a.id === asignacionSeleccionada)
      if (asignacion) {
        setProyectoId(asignacion.proyecto_id)
        setEtapaId(asignacion.etapa_id || '')
        if (asignacion.vehiculo_id) {
          setVehiculoId(asignacion.vehiculo_id)
        }
        // Cargar materiales planificados
        if (asignacion.materiales_planificados) {
          setMaterialesSeleccionados(
            asignacion.materiales_planificados.map((m: any) => ({
              material_id: m.material_id,
              cantidad_cargada: m.cantidad,
              notas: m.notas,
            }))
          )
        }
      }
    }
  }, [asignacionSeleccionada, asignacionesHoy])

  const handleToggleMaterial = (materialId: string, checked: boolean) => {
    if (checked) {
      setMaterialesSeleccionados(prev => [...prev, { material_id: materialId, cantidad_cargada: 0 }])
    } else {
      setMaterialesSeleccionados(prev => prev.filter(m => m.material_id !== materialId))
    }
  }

  const handleCantidadMaterial = (materialId: string, cantidad: number) => {
    setMaterialesSeleccionados(prev =>
      prev.map(m => (m.material_id === materialId ? { ...m, cantidad_cargada: cantidad } : m))
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!vehiculoId || !proyectoId) {
      return
    }

    const request: IniciarJornadaRequest = {
      vehiculo_id: vehiculoId,
      proyecto_id: proyectoId,
      etapa_id: etapaId || undefined,
      km_inicial: kmInicial ? parseInt(kmInicial) : undefined,
      observaciones: observaciones || undefined,
      materiales: materialesSeleccionados.filter(m => m.cantidad_cargada > 0),
    }

    iniciarJornadaMutation.mutate({
      request,
      asignacionId: asignacionSeleccionada || undefined,
    })
  }

  if (loadingJornada) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-red-600" />
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Iniciar Jornada</h1>
        <p className="text-gray-500">
          Registra tu vehículo, destino y materiales para comenzar el día
        </p>
      </div>

      {/* Asignaciones del día */}
      {asignacionesHoy && asignacionesHoy.length > 0 && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              Asignaciones para hoy
            </CardTitle>
            <CardDescription>
              Tenés {asignacionesHoy.length} asignación(es) planificada(s)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {asignacionesHoy.map(asig => (
              <div
                key={asig.id}
                onClick={() => setAsignacionSeleccionada(asig.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  asignacionSeleccionada === asig.id
                    ? 'border-red-500 bg-white'
                    : 'border-gray-200 bg-white hover:border-red-300'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{asig.proyecto_nombre}</p>
                    {asig.etapa_nombre && (
                      <p className="text-sm text-gray-500">{asig.etapa_nombre}</p>
                    )}
                  </div>
                  <Badge
                    variant={asig.prioridad === 'urgente' ? 'destructive' : 'secondary'}
                  >
                    {asig.prioridad}
                  </Badge>
                </div>
                {asig.vehiculo_patente && (
                  <p className="text-sm text-gray-500 mt-1">
                    Vehículo: {asig.vehiculo_patente}
                  </p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <form onSubmit={handleSubmit}>
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Truck className="h-5 w-5" />
              Vehículo
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="vehiculo">Seleccionar vehículo *</Label>
              <Select value={vehiculoId} onValueChange={setVehiculoId}>
                <SelectTrigger>
                  <SelectValue placeholder="Elegí un vehículo" />
                </SelectTrigger>
                <SelectContent>
                  {vehiculos?.map(v => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.patente || v.codigo} - {v.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="km">Kilometraje inicial</Label>
              <Input
                id="km"
                type="number"
                placeholder="Ej: 125430"
                value={kmInicial}
                onChange={e => setKmInicial(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              Destino
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="proyecto">Proyecto / Obra *</Label>
              <Select value={proyectoId} onValueChange={setProyectoId}>
                <SelectTrigger>
                  <SelectValue placeholder="Elegí el proyecto" />
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
                <Label htmlFor="etapa">Etapa / Zona (opcional)</Label>
                <Select value={etapaId} onValueChange={setEtapaId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Elegí la etapa" />
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
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Package className="h-5 w-5" />
              Materiales a cargar
            </CardTitle>
            <CardDescription>
              Marcá los materiales que llevás y la cantidad
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-[300px] overflow-y-auto">
              {materiales?.map(mat => {
                const seleccionado = materialesSeleccionados.find(m => m.material_id === mat.id)
                return (
                  <div
                    key={mat.id}
                    className={`flex items-center gap-4 p-3 rounded-lg border ${
                      seleccionado ? 'border-red-300 bg-red-50' : 'border-gray-200'
                    }`}
                  >
                    <Checkbox
                      checked={!!seleccionado}
                      onCheckedChange={checked => handleToggleMaterial(mat.id, checked as boolean)}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{mat.nombre}</p>
                      <p className="text-sm text-gray-500">
                        Stock: {mat.stock_actual} {mat.unidad}
                      </p>
                    </div>
                    {seleccionado && (
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          className="w-24"
                          placeholder="Cant."
                          value={seleccionado.cantidad_cargada || ''}
                          onChange={e =>
                            handleCantidadMaterial(mat.id, parseFloat(e.target.value) || 0)
                          }
                        />
                        <span className="text-sm text-gray-500">{mat.unidad}</span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Observaciones</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="Notas adicionales para el inicio de jornada..."
              value={observaciones}
              onChange={e => setObservaciones(e.target.value)}
              rows={3}
            />
          </CardContent>
        </Card>

        <Button
          type="submit"
          size="lg"
          className="w-full bg-red-600 hover:bg-red-700"
          disabled={!vehiculoId || !proyectoId || iniciarJornadaMutation.isPending}
        >
          {iniciarJornadaMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Iniciando...
            </>
          ) : (
            <>
              <Play className="mr-2 h-5 w-5" />
              Iniciar Jornada
            </>
          )}
        </Button>

        {iniciarJornadaMutation.isError && (
          <p className="mt-4 text-center text-red-600">
            Error al iniciar la jornada. Por favor, intentá de nuevo.
          </p>
        )}
      </form>
    </div>
  )
}
