import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Loader2,
  Truck,
  MapPin,
  Package,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Navigation,
  Flag,
  MessageSquare,
} from 'lucide-react'
import {
  jornadasOperarioService,
  type JornadaOperario,
  type CerrarJornadaRequest,
  type MaterialRendir,
  type DestinoDevolucion,
} from '@/services/jornadasOperario'

export default function JornadaActiva() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Estados
  const [showNovedadDialog, setShowNovedadDialog] = useState(false)
  const [showCerrarDialog, setShowCerrarDialog] = useState(false)
  const [novedad, setNovedad] = useState('')
  const [novedadUrgente, setNovedadUrgente] = useState(false)
  const [kmFinal, setKmFinal] = useState('')
  const [observacionesCierre, setObservacionesCierre] = useState('')
  const [materialesRendicion, setMaterialesRendicion] = useState<MaterialRendir[]>([])

  // Cargar jornada activa
  const { data: jornada, isLoading, refetch } = useQuery({
    queryKey: ['mi-jornada-activa'],
    queryFn: jornadasOperarioService.getMiJornadaActiva,
    refetchInterval: 30000, // Refrescar cada 30 segundos
  })

  // Mutations
  const marcarEnCaminoMutation = useMutation({
    mutationFn: (jornadaId: string) => jornadasOperarioService.marcarEnCamino(jornadaId),
    onSuccess: () => refetch(),
  })

  const marcarLlegadaMutation = useMutation({
    mutationFn: (jornadaId: string) => jornadasOperarioService.marcarLlegada(jornadaId),
    onSuccess: () => refetch(),
  })

  const reportarNovedadMutation = useMutation({
    mutationFn: ({ jornadaId, novedad, urgente }: { jornadaId: string; novedad: string; urgente: boolean }) =>
      jornadasOperarioService.reportarNovedad(jornadaId, novedad, urgente),
    onSuccess: () => {
      setShowNovedadDialog(false)
      setNovedad('')
      setNovedadUrgente(false)
      refetch()
    },
  })

  const cerrarJornadaMutation = useMutation({
    mutationFn: ({ jornadaId, data }: { jornadaId: string; data: CerrarJornadaRequest }) =>
      jornadasOperarioService.cerrarJornada(jornadaId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mi-jornada-activa'] })
      navigate('/operario/historial')
    },
  })

  // Inicializar rendición de materiales cuando se abre el dialog
  const handleOpenCerrarDialog = () => {
    if (jornada?.materiales) {
      setMaterialesRendicion(
        jornada.materiales.map(m => ({
          material_id: m.material_id,
          cantidad_consumida: m.cantidad_cargada || 0,
          cantidad_devuelta: 0,
          destino_devolucion: undefined,
        }))
      )
    }
    setShowCerrarDialog(true)
  }

  const handleCerrarJornada = () => {
    if (!jornada) return

    const data: CerrarJornadaRequest = {
      km_final: kmFinal ? parseInt(kmFinal) : undefined,
      observaciones: observacionesCierre || undefined,
      materiales: materialesRendicion,
    }

    cerrarJornadaMutation.mutate({ jornadaId: jornada.id, data })
  }

  const updateMaterialRendicion = (materialId: string, field: keyof MaterialRendir, value: any) => {
    setMaterialesRendicion(prev =>
      prev.map(m => (m.material_id === materialId ? { ...m, [field]: value } : m))
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-red-600" />
      </div>
    )
  }

  if (!jornada) {
    return (
      <div className="container mx-auto py-6 max-w-3xl">
        <Card className="text-center py-12">
          <CardContent>
            <Clock className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <h2 className="text-xl font-semibold mb-2">No tenés jornada activa</h2>
            <p className="text-gray-500 mb-6">Iniciá una nueva jornada para comenzar a trabajar</p>
            <Button onClick={() => navigate('/operario/iniciar-jornada')} className="bg-red-600 hover:bg-red-700">
              Iniciar Jornada
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const estadoConfig = {
    iniciada: { label: 'Iniciada', color: 'bg-yellow-100 text-yellow-800', progress: 25 },
    en_camino: { label: 'En camino', color: 'bg-blue-100 text-blue-800', progress: 50 },
    en_obra: { label: 'En obra', color: 'bg-green-100 text-green-800', progress: 75 },
    finalizada: { label: 'Finalizada', color: 'bg-gray-100 text-gray-800', progress: 100 },
  }

  const config = estadoConfig[jornada.estado as keyof typeof estadoConfig] || estadoConfig.iniciada

  return (
    <div className="container mx-auto py-6 max-w-3xl">
      {/* Header con estado */}
      <Card className="mb-6 border-red-200">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-xl">{jornada.proyecto_nombre}</CardTitle>
              {jornada.etapa_nombre && (
                <CardDescription className="text-base">{jornada.etapa_nombre}</CardDescription>
              )}
            </div>
            <Badge className={config.color}>{config.label}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={config.progress} className="h-2 mb-4" />
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Truck className="h-4 w-4 text-gray-500" />
              <span>{jornada.vehiculo_patente || 'Sin vehículo'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-gray-500" />
              <span>
                Inicio:{' '}
                {jornada.hora_inicio
                  ? new Date(jornada.hora_inicio).toLocaleTimeString('es-AR', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  : '-'}
              </span>
            </div>
            {jornada.km_inicial && (
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-gray-500" />
                <span>Km inicial: {jornada.km_inicial}</span>
              </div>
            )}
            {jornada.duracion_total && (
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-gray-500" />
                <span>Duración: {jornada.duracion_total.toFixed(1)} hs</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Acciones según estado */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Acciones</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {jornada.estado === 'iniciada' && (
            <Button
              className="w-full"
              variant="outline"
              onClick={() => marcarEnCaminoMutation.mutate(jornada.id)}
              disabled={marcarEnCaminoMutation.isPending}
            >
              <Navigation className="mr-2 h-5 w-5" />
              {marcarEnCaminoMutation.isPending ? 'Marcando...' : 'Marcar En Camino'}
            </Button>
          )}

          {jornada.estado === 'en_camino' && (
            <Button
              className="w-full bg-green-600 hover:bg-green-700"
              onClick={() => marcarLlegadaMutation.mutate(jornada.id)}
              disabled={marcarLlegadaMutation.isPending}
            >
              <Flag className="mr-2 h-5 w-5" />
              {marcarLlegadaMutation.isPending ? 'Marcando...' : 'Llegué a la Obra'}
            </Button>
          )}

          <Dialog open={showNovedadDialog} onOpenChange={setShowNovedadDialog}>
            <DialogTrigger asChild>
              <Button className="w-full" variant="outline">
                <MessageSquare className="mr-2 h-5 w-5" />
                Reportar Novedad
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Reportar Novedad</DialogTitle>
                <DialogDescription>
                  Registrá cualquier novedad o situación que ocurra durante la jornada
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Descripción</Label>
                  <Textarea
                    value={novedad}
                    onChange={e => setNovedad(e.target.value)}
                    placeholder="Describí la novedad..."
                    rows={4}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="urgente"
                    checked={novedadUrgente}
                    onChange={e => setNovedadUrgente(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <Label htmlFor="urgente" className="text-red-600 font-medium">
                    Es urgente (notificar al supervisor)
                  </Label>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowNovedadDialog(false)}>
                  Cancelar
                </Button>
                <Button
                  onClick={() =>
                    reportarNovedadMutation.mutate({
                      jornadaId: jornada.id,
                      novedad,
                      urgente: novedadUrgente,
                    })
                  }
                  disabled={!novedad || reportarNovedadMutation.isPending}
                >
                  {reportarNovedadMutation.isPending ? 'Enviando...' : 'Enviar'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {jornada.estado === 'en_obra' && (
            <Button className="w-full bg-red-600 hover:bg-red-700" onClick={handleOpenCerrarDialog}>
              <CheckCircle2 className="mr-2 h-5 w-5" />
              Cerrar Jornada
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Materiales cargados */}
      {jornada.materiales && jornada.materiales.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Package className="h-5 w-5" />
              Materiales Cargados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {jornada.materiales.map(mat => (
                <div key={mat.id} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">{mat.material_nombre}</p>
                    <p className="text-sm text-gray-500">{mat.material_codigo}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">
                      {mat.cantidad_cargada} {mat.material_unidad}
                    </p>
                    <Badge variant="outline" className="text-xs">
                      {mat.estado}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Novedades registradas */}
      {jornada.novedades && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Novedades
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded-lg">
              {jornada.novedades}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Dialog de cierre de jornada */}
      <Dialog open={showCerrarDialog} onOpenChange={setShowCerrarDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Cerrar Jornada</DialogTitle>
            <DialogDescription>
              Completá la rendición de materiales y los datos de cierre
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Km final */}
            <div className="space-y-2">
              <Label>Kilometraje final del vehículo</Label>
              <Input
                type="number"
                value={kmFinal}
                onChange={e => setKmFinal(e.target.value)}
                placeholder="Ej: 125480"
              />
              {jornada.km_inicial && kmFinal && (
                <p className="text-sm text-gray-500">
                  Recorrido: {parseInt(kmFinal) - jornada.km_inicial} km
                </p>
              )}
            </div>

            {/* Rendición de materiales */}
            {jornada.materiales && jornada.materiales.length > 0 && (
              <div className="space-y-4">
                <Label className="text-base font-semibold">Rendición de Materiales</Label>
                {jornada.materiales.map(mat => {
                  const rendicion = materialesRendicion.find(m => m.material_id === mat.material_id)
                  return (
                    <div key={mat.id} className="border rounded-lg p-4 space-y-3">
                      <div className="flex justify-between">
                        <div>
                          <p className="font-medium">{mat.material_nombre}</p>
                          <p className="text-sm text-gray-500">
                            Cargado: {mat.cantidad_cargada} {mat.material_unidad}
                          </p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <Label className="text-sm">Consumido</Label>
                          <Input
                            type="number"
                            value={rendicion?.cantidad_consumida || 0}
                            onChange={e =>
                              updateMaterialRendicion(
                                mat.material_id,
                                'cantidad_consumida',
                                parseFloat(e.target.value) || 0
                              )
                            }
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-sm">Sobrante</Label>
                          <Input
                            type="number"
                            value={rendicion?.cantidad_devuelta || 0}
                            onChange={e =>
                              updateMaterialRendicion(
                                mat.material_id,
                                'cantidad_devuelta',
                                parseFloat(e.target.value) || 0
                              )
                            }
                          />
                        </div>
                      </div>
                      {(rendicion?.cantidad_devuelta || 0) > 0 && (
                        <div className="space-y-1">
                          <Label className="text-sm">Destino del sobrante</Label>
                          <Select
                            value={rendicion?.destino_devolucion || ''}
                            onValueChange={v =>
                              updateMaterialRendicion(
                                mat.material_id,
                                'destino_devolucion',
                                v as DestinoDevolucion
                              )
                            }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Seleccionar destino" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="deposito">Devolver al depósito</SelectItem>
                              <SelectItem value="obra">Dejar en la obra</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}

            {/* Observaciones */}
            <div className="space-y-2">
              <Label>Observaciones de cierre</Label>
              <Textarea
                value={observacionesCierre}
                onChange={e => setObservacionesCierre(e.target.value)}
                placeholder="Notas adicionales sobre la jornada..."
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCerrarDialog(false)}>
              Cancelar
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={handleCerrarJornada}
              disabled={cerrarJornadaMutation.isPending}
            >
              {cerrarJornadaMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Cerrando...
                </>
              ) : (
                'Confirmar Cierre'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
