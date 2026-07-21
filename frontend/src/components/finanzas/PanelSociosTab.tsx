import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Loader2,
  Plus,
  ArrowUpRight,
  ArrowDownRight,
  Users,
  DollarSign,
  Wallet,
  ChevronDown,
  ChevronUp,
  Trash2,
  Pencil,
  TrendingUp,
  TrendingDown,
  Settings2,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import { useIsAdmin } from '@/store/auth'
import { formatCurrency, formatDate } from '@/lib/utils'
import * as panelSocios from '@/services/panelSocios'
import * as finanzasService from '@/services/finanzas'
import type {
  AporteSocio,
  RetiroSocio,
  TipoIngresoConfig,
} from '@/services/panelSocios'

// ============ helpers ============

const primerDiaMes = () => {
  const d = new Date()
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split('T')[0]
}

const ultimoDiaMes = () => {
  const d = new Date()
  return new Date(d.getFullYear(), d.getMonth() + 1, 0).toISOString().split('T')[0]
}

// ============ schemas ============

const aporteSchema = z.object({
  socio_id: z.string().min(1, 'Requerido'),
  monto: z.number().min(0.01, 'Monto debe ser > 0'),
  fecha: z.string().min(1, 'Requerido'),
  concepto: z.string().optional(),
  observaciones: z.string().optional(),
  cuenta_id: z.string().optional(),
})

const retiroSchema = z.object({
  socio_id: z.string().min(1, 'Requerido'),
  monto: z.number().min(0.01, 'Monto debe ser > 0'),
  fecha: z.string().min(1, 'Requerido'),
  concepto: z.string().optional(),
  observaciones: z.string().optional(),
  cuenta_id: z.string().optional(),
})

const socioSchema = z.object({
  nombre: z.string().min(1, 'Nombre requerido'),
  apellido: z.string().optional(),
  porcentaje_participacion: z.number().min(0).max(100),
  email: z.string().email().optional().or(z.literal('')),
  telefono: z.string().optional(),
  notas: z.string().optional(),
})

const tipoIngresoSchema = z.object({
  nombre: z.string().min(1, 'Nombre requerido').max(100),
  color: z.string().optional(),
  orden: z.number().optional(),
  es_aporte_socio: z.boolean().optional(),
})

type AporteForm = z.infer<typeof aporteSchema>
type RetiroForm = z.infer<typeof retiroSchema>
type SocioForm = z.infer<typeof socioSchema>
type TipoIngresoForm = z.infer<typeof tipoIngresoSchema>

// ============ componente ============

export function PanelSociosTab() {
  const [fechaDesde, setFechaDesde] = useState(primerDiaMes())
  const [fechaHasta, setFechaHasta] = useState(ultimoDiaMes())
  const [openPlanilla, setOpenPlanilla] = useState<string | null>(null)
  const [openGasto, setOpenGasto] = useState<string | null>(null)
  const [openSocio, setOpenSocio] = useState<string | null>(null)
  const [isAporteOpen, setIsAporteOpen] = useState(false)
  const [isRetiroOpen, setIsRetiroOpen] = useState(false)
  const [isSocioOpen, setIsSocioOpen] = useState(false)
  const [isPlanillasOpen, setIsPlanillasOpen] = useState(false)
  const [aporteEdit, setAporteEdit] = useState<AporteSocio | null>(null)
  const [retiroEdit, setRetiroEdit] = useState<RetiroSocio | null>(null)
  const [tipoEdit, setTipoEdit] = useState<TipoIngresoConfig | null>(null)
  const [socioSeleccionado, setSocioSeleccionado] = useState<string | undefined>()

  const { toast } = useToast()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  const { data: resumen, isLoading } = useQuery({
    queryKey: ['panel-socios-resumen', fechaDesde, fechaHasta],
    queryFn: () => panelSocios.getResumenPanel({
      fecha_desde: fechaDesde,
      fecha_hasta: fechaHasta,
    }),
  })

  const { data: cuentas } = useQuery({
    queryKey: ['cuentas'],
    queryFn: () => finanzasService.getCuentas(),
  })

  const { data: socios } = useQuery({
    queryKey: ['socios'],
    queryFn: () => panelSocios.getSocios(),
  })

  const { data: tiposIngreso } = useQuery({
    queryKey: ['tipos-ingreso'],
    queryFn: panelSocios.getTiposIngreso,
  })

  // Aportes y retiros completos para modo edicion
  const { data: aportesFull } = useQuery({
    queryKey: ['aportes-periodo', fechaDesde, fechaHasta],
    queryFn: () => panelSocios.getAportes({
      fecha_desde: fechaDesde,
      fecha_hasta: fechaHasta,
    }),
  })

  const { data: retirosFull } = useQuery({
    queryKey: ['retiros-periodo', fechaDesde, fechaHasta],
    queryFn: () => panelSocios.getRetiros({
      fecha_desde: fechaDesde,
      fecha_hasta: fechaHasta,
    }),
  })

  const invalidar = () => {
    queryClient.invalidateQueries({ queryKey: ['panel-socios-resumen'] })
    queryClient.invalidateQueries({ queryKey: ['socios'] })
    queryClient.invalidateQueries({ queryKey: ['tipos-ingreso'] })
    queryClient.invalidateQueries({ queryKey: ['aportes-periodo'] })
    queryClient.invalidateQueries({ queryKey: ['retiros-periodo'] })
    queryClient.invalidateQueries({ queryKey: ['transacciones'] })
    queryClient.invalidateQueries({ queryKey: ['finanzas-dashboard'] })
  }

  // Mutations aportes
  const createAporteMutation = useMutation({
    mutationFn: panelSocios.createAporte,
    onSuccess: () => {
      invalidar()
      toast({ title: 'Aporte registrado' })
      setIsAporteOpen(false)
      aporteForm.reset()
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al registrar aporte' }),
  })

  const updateAporteMutation = useMutation({
    mutationFn: (payload: { id: string; data: panelSocios.AporteSocioUpdate }) =>
      panelSocios.updateAporte(payload.id, payload.data),
    onSuccess: () => {
      invalidar()
      toast({ title: 'Aporte actualizado' })
      setAporteEdit(null)
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al actualizar aporte' }),
  })

  const deleteAporteMutation = useMutation({
    mutationFn: panelSocios.deleteAporte,
    onSuccess: () => {
      invalidar()
      toast({ title: 'Aporte eliminado' })
    },
  })

  // Mutations retiros
  const createRetiroMutation = useMutation({
    mutationFn: panelSocios.createRetiro,
    onSuccess: () => {
      invalidar()
      toast({ title: 'Retiro registrado' })
      setIsRetiroOpen(false)
      retiroForm.reset()
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al registrar retiro' }),
  })

  const updateRetiroMutation = useMutation({
    mutationFn: (payload: { id: string; data: panelSocios.RetiroSocioUpdate }) =>
      panelSocios.updateRetiro(payload.id, payload.data),
    onSuccess: () => {
      invalidar()
      toast({ title: 'Retiro actualizado' })
      setRetiroEdit(null)
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al actualizar retiro' }),
  })

  const deleteRetiroMutation = useMutation({
    mutationFn: panelSocios.deleteRetiro,
    onSuccess: () => {
      invalidar()
      toast({ title: 'Retiro eliminado' })
    },
  })

  // Mutations socios
  const createSocioMutation = useMutation({
    mutationFn: panelSocios.createSocio,
    onSuccess: () => {
      invalidar()
      toast({ title: 'Socio creado' })
      setIsSocioOpen(false)
      socioForm.reset()
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al crear socio' }),
  })

  // Mutations planillas
  const createTipoMutation = useMutation({
    mutationFn: panelSocios.createTipoIngreso,
    onSuccess: () => {
      invalidar()
      toast({ title: 'Planilla creada' })
      tipoForm.reset()
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al crear planilla' }),
  })

  const updateTipoMutation = useMutation({
    mutationFn: (payload: { id: string; data: panelSocios.TipoIngresoUpdate }) =>
      panelSocios.updateTipoIngreso(payload.id, payload.data),
    onSuccess: () => {
      invalidar()
      toast({ title: 'Planilla actualizada' })
      setTipoEdit(null)
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al actualizar planilla' }),
  })

  const deleteTipoMutation = useMutation({
    mutationFn: panelSocios.deleteTipoIngreso,
    onSuccess: () => {
      invalidar()
      toast({ title: 'Planilla eliminada' })
    },
  })

  // Mutation: eliminar transaccion (usado para gastos e ingresos que no son aportes)
  const deleteTransaccionMutation = useMutation({
    mutationFn: finanzasService.deleteTransaccion,
    onSuccess: () => {
      invalidar()
      toast({ title: 'Movimiento eliminado' })
    },
    onError: () => toast({ variant: 'destructive', title: 'Error al eliminar' }),
  })

  // Forms
  const aporteForm = useForm<AporteForm>({
    resolver: zodResolver(aporteSchema),
    defaultValues: { fecha: new Date().toISOString().split('T')[0] },
  })

  const retiroForm = useForm<RetiroForm>({
    resolver: zodResolver(retiroSchema),
    defaultValues: { fecha: new Date().toISOString().split('T')[0] },
  })

  const socioForm = useForm<SocioForm>({
    resolver: zodResolver(socioSchema),
    defaultValues: { porcentaje_participacion: 50 },
  })

  const tipoForm = useForm<TipoIngresoForm>({
    resolver: zodResolver(tipoIngresoSchema),
    defaultValues: { color: '#10B981', orden: 0, es_aporte_socio: false },
  })

  const onSubmitAporte = (data: AporteForm) => {
    createAporteMutation.mutate({
      ...data,
      cuenta_id: data.cuenta_id || undefined,
    })
  }

  const onSubmitRetiro = (data: RetiroForm) => {
    createRetiroMutation.mutate({
      ...data,
      cuenta_id: data.cuenta_id || undefined,
    })
  }

  const onSubmitSocio = (data: SocioForm) => {
    createSocioMutation.mutate({
      ...data,
      email: data.email || undefined,
    })
  }

  const onSubmitTipo = (data: TipoIngresoForm) => {
    createTipoMutation.mutate({
      nombre: data.nombre,
      color: data.color,
      orden: data.orden,
      es_aporte_socio: data.es_aporte_socio,
    })
  }

  const openRetiroPara = (socioId: string) => {
    setSocioSeleccionado(socioId)
    retiroForm.setValue('socio_id', socioId)
    setIsRetiroOpen(true)
  }

  const hayDatos = useMemo(() => !!resumen, [resumen])

  // Preset rangos
  const setMesActual = () => {
    setFechaDesde(primerDiaMes())
    setFechaHasta(ultimoDiaMes())
  }
  const setMesAnterior = () => {
    const d = new Date()
    const desde = new Date(d.getFullYear(), d.getMonth() - 1, 1).toISOString().split('T')[0]
    const hasta = new Date(d.getFullYear(), d.getMonth(), 0).toISOString().split('T')[0]
    setFechaDesde(desde)
    setFechaHasta(hasta)
  }
  const setAnioActual = () => {
    const anio = new Date().getFullYear()
    setFechaDesde(`${anio}-01-01`)
    setFechaHasta(`${anio}-12-31`)
  }

  // Indice de aportes/retiros por id para lookup rapido en edicion
  const aportesById = useMemo(() => {
    const m: Record<string, AporteSocio> = {}
    aportesFull?.forEach((a) => { m[a.id] = a })
    return m
  }, [aportesFull])
  const retirosById = useMemo(() => {
    const m: Record<string, RetiroSocio> = {}
    retirosFull?.forEach((r) => { m[r.id] = r })
    return m
  }, [retirosFull])

  return (
    <div className="space-y-6">
      {/* Filtros y acciones */}
      <Card>
        <CardContent className="p-4 flex flex-col md:flex-row md:items-end gap-4">
          <div className="grid grid-cols-2 gap-3 flex-1">
            <div className="space-y-1">
              <Label className="text-xs">Desde</Label>
              <Input
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Hasta</Label>
              <Input
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={setMesActual}>Mes actual</Button>
            <Button variant="outline" size="sm" onClick={setMesAnterior}>Mes anterior</Button>
            <Button variant="outline" size="sm" onClick={setAnioActual}>Año</Button>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => setIsAporteOpen(true)}>
              <Plus className="h-4 w-4 mr-1" /> Aporte
            </Button>
            <Button variant="outline" onClick={() => setIsRetiroOpen(true)}>
              <Plus className="h-4 w-4 mr-1" /> Retiro
            </Button>
            <Button variant="outline" onClick={() => setIsPlanillasOpen(true)}>
              <Settings2 className="h-4 w-4 mr-1" /> Planillas
            </Button>
            {isAdmin && (
              <Button variant="ghost" onClick={() => setIsSocioOpen(true)}>
                <Users className="h-4 w-4 mr-1" /> Socio
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {isLoading || !hayDatos ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          {/* Totales principales */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="border-green-200 bg-green-50/50">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-sm">Total ingresos</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-700">
                  {formatCurrency(resumen!.total_ingresos)}
                </div>
              </CardContent>
            </Card>

            <Card className="border-red-200 bg-red-50/50">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-sm">Total gastos</CardTitle>
                <TrendingDown className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-700">
                  {formatCurrency(resumen!.total_gastos)}
                </div>
              </CardContent>
            </Card>

            <Card className={`${resumen!.ganancia >= 0 ? 'border-emerald-300 bg-emerald-50' : 'border-red-300 bg-red-50'}`}>
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-sm">Ganancia</CardTitle>
                <DollarSign className={`h-4 w-4 ${resumen!.ganancia >= 0 ? 'text-emerald-600' : 'text-red-600'}`} />
              </CardHeader>
              <CardContent>
                <div className={`text-3xl font-bold ${resumen!.ganancia >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                  {formatCurrency(resumen!.ganancia)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Ingresos − Gastos
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Planillas: ingresos vs gastos */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* INGRESOS */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ArrowUpRight className="h-5 w-5 text-green-600" />
                  Planillas de ingresos
                </CardTitle>
                <CardDescription>
                  Click en una planilla para ver el detalle.
                  <button
                    onClick={() => setIsPlanillasOpen(true)}
                    className="ml-2 text-primary hover:underline"
                  >
                    Gestionar planillas
                  </button>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {resumen!.planillas_ingresos.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-6">
                    No hay planillas de ingreso configuradas.
                  </p>
                ) : (
                  resumen!.planillas_ingresos.map((p) => {
                    const key = p.tipo_id || `virtual-${p.nombre}`
                    const abierta = openPlanilla === key
                    return (
                      <div key={key} className="rounded border">
                        <button
                          type="button"
                          onClick={() => setOpenPlanilla(abierta ? null : key)}
                          className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition"
                        >
                          <div className="flex items-center gap-3">
                            {abierta ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            <div
                              className="w-3 h-3 rounded-full flex-shrink-0"
                              style={{ backgroundColor: p.color }}
                            />
                            <div className="text-left">
                              <p className="font-medium">{p.nombre}</p>
                              <p className="text-xs text-muted-foreground">{p.cantidad} movimiento(s)</p>
                            </div>
                          </div>
                          <p className="font-bold text-green-700">
                            {formatCurrency(p.total)}
                          </p>
                        </button>
                        {abierta && (
                          <div className="border-t bg-muted/20">
                            {p.items.length === 0 ? (
                              <div className="p-4 text-sm text-muted-foreground text-center">
                                Sin movimientos en este periodo.
                              </div>
                            ) : (
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    <TableHead className="w-24">Fecha</TableHead>
                                    <TableHead>Concepto</TableHead>
                                    <TableHead>Referencia</TableHead>
                                    <TableHead className="text-right">Monto</TableHead>
                                    <TableHead className="w-20 text-center">Acciones</TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {p.items.map((i) => {
                                    const aporte = aportesById[i.id]
                                    return (
                                      <TableRow key={i.id}>
                                        <TableCell className="text-xs">{formatDate(i.fecha)}</TableCell>
                                        <TableCell className="text-sm">{i.concepto}</TableCell>
                                        <TableCell className="text-xs text-muted-foreground">
                                          {i.referencia || '-'}
                                        </TableCell>
                                        <TableCell className="text-right text-green-700 font-medium">
                                          {formatCurrency(i.monto)}
                                        </TableCell>
                                        <TableCell className="text-center">
                                          {aporte ? (
                                            <div className="flex justify-center gap-1">
                                              <Button
                                                size="icon"
                                                variant="ghost"
                                                className="h-7 w-7"
                                                onClick={() => setAporteEdit(aporte)}
                                              >
                                                <Pencil className="h-3 w-3" />
                                              </Button>
                                              {isAdmin && (
                                                <Button
                                                  size="icon"
                                                  variant="ghost"
                                                  className="h-7 w-7"
                                                  onClick={() => deleteAporteMutation.mutate(aporte.id)}
                                                >
                                                  <Trash2 className="h-3 w-3 text-destructive" />
                                                </Button>
                                              )}
                                            </div>
                                          ) : isAdmin ? (
                                            <Button
                                              size="icon"
                                              variant="ghost"
                                              className="h-7 w-7"
                                              onClick={() => {
                                                if (confirm(`Eliminar ingreso "${i.concepto}" por ${formatCurrency(i.monto)}?`)) {
                                                  deleteTransaccionMutation.mutate(i.id)
                                                }
                                              }}
                                            >
                                              <Trash2 className="h-3 w-3 text-destructive" />
                                            </Button>
                                          ) : (
                                            <span className="text-xs text-muted-foreground">-</span>
                                          )}
                                        </TableCell>
                                      </TableRow>
                                    )
                                  })}
                                </TableBody>
                              </Table>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })
                )}
                <div className="pt-3 mt-2 border-t flex justify-between items-center">
                  <span className="font-semibold">TOTAL INGRESOS</span>
                  <span className="font-bold text-green-700 text-lg">
                    {formatCurrency(resumen!.total_ingresos)}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* GASTOS */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ArrowDownRight className="h-5 w-5 text-red-600" />
                  Planillas de gastos
                </CardTitle>
                <CardDescription>Agrupado por categoria</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {resumen!.planillas_gastos.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-6">
                    No hay gastos registrados en el periodo.
                  </p>
                ) : (
                  resumen!.planillas_gastos.map((p) => {
                    const key = p.categoria_id || `sin-cat-${p.categoria}`
                    const abierta = openGasto === key
                    return (
                      <div key={key} className="rounded border">
                        <button
                          type="button"
                          onClick={() => setOpenGasto(abierta ? null : key)}
                          className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition"
                        >
                          <div className="flex items-center gap-3">
                            {abierta ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            <div className="text-left">
                              <p className="font-medium">{p.categoria}</p>
                              <p className="text-xs text-muted-foreground">{p.cantidad} gasto(s)</p>
                            </div>
                          </div>
                          <p className="font-bold text-red-700">
                            {formatCurrency(p.total)}
                          </p>
                        </button>
                        {abierta && (
                          <div className="border-t bg-muted/20">
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead className="w-24">Fecha</TableHead>
                                  <TableHead>Concepto</TableHead>
                                  <TableHead>Referencia</TableHead>
                                  <TableHead className="text-right">Monto</TableHead>
                                  {isAdmin && <TableHead className="w-16 text-center">Acciones</TableHead>}
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {p.items.map((i) => (
                                  <TableRow key={i.id}>
                                    <TableCell className="text-xs">{formatDate(i.fecha)}</TableCell>
                                    <TableCell className="text-sm">{i.concepto}</TableCell>
                                    <TableCell className="text-xs text-muted-foreground">
                                      {i.referencia || '-'}
                                    </TableCell>
                                    <TableCell className="text-right text-red-700 font-medium">
                                      {formatCurrency(i.monto)}
                                    </TableCell>
                                    {isAdmin && (
                                      <TableCell className="text-center">
                                        <Button
                                          size="icon"
                                          variant="ghost"
                                          className="h-7 w-7"
                                          onClick={() => {
                                            if (confirm(`Eliminar gasto "${i.concepto}" por ${formatCurrency(i.monto)}?`)) {
                                              deleteTransaccionMutation.mutate(i.id)
                                            }
                                          }}
                                        >
                                          <Trash2 className="h-3 w-3 text-destructive" />
                                        </Button>
                                      </TableCell>
                                    )}
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </div>
                        )}
                      </div>
                    )
                  })
                )}
                <div className="pt-3 mt-2 border-t flex justify-between items-center">
                  <span className="font-semibold">TOTAL GASTOS</span>
                  <span className="font-bold text-red-700 text-lg">
                    {formatCurrency(resumen!.total_gastos)}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Distribucion por socio */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Distribucion de ganancia entre socios
              </CardTitle>
              <CardDescription>
                Cada socio recibe segun su porcentaje. Los retiros se descuentan de su ganancia.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {resumen!.socios.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-6">
                  Todavia no hay socios cargados. Crea uno para distribuir la ganancia.
                </p>
              ) : (
                resumen!.socios.map((s) => {
                  const abierta = openSocio === s.socio_id
                  return (
                    <div key={s.socio_id} className="rounded border">
                      <button
                        type="button"
                        onClick={() => setOpenSocio(abierta ? null : s.socio_id)}
                        className="w-full p-4 hover:bg-muted/40 transition"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <div className="flex items-center gap-3">
                            {abierta ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            <div className="text-left">
                              <p className="font-semibold">{s.nombre}</p>
                              <Badge variant="outline" className="mt-1">
                                {s.porcentaje_participacion}% de participacion
                              </Badge>
                            </div>
                          </div>
                          <div className="flex gap-6 text-right">
                            <div>
                              <p className="text-xs text-muted-foreground">Ganancia</p>
                              <p className={`font-bold ${s.ganancia_asignada >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                                {formatCurrency(s.ganancia_asignada)}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Retiros</p>
                              <p className="font-bold text-red-700">
                                −{formatCurrency(s.total_retiros)}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Saldo</p>
                              <p className={`font-bold text-lg ${s.saldo_disponible >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                                {formatCurrency(s.saldo_disponible)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </button>
                      {abierta && (
                        <div className="border-t bg-muted/20 p-4 space-y-3">
                          <div className="flex items-center justify-between">
                            <h4 className="text-sm font-semibold flex items-center gap-2">
                              <Wallet className="h-4 w-4" />
                              Retiros del periodo
                            </h4>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation()
                                openRetiroPara(s.socio_id)
                              }}
                            >
                              <Plus className="h-3 w-3 mr-1" /> Registrar retiro
                            </Button>
                          </div>
                          {s.retiros.length === 0 ? (
                            <p className="text-sm text-muted-foreground text-center py-4">
                              Sin retiros en este periodo.
                            </p>
                          ) : (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead className="w-24">Fecha</TableHead>
                                  <TableHead>Concepto</TableHead>
                                  <TableHead>Cuenta</TableHead>
                                  <TableHead className="text-right">Monto</TableHead>
                                  <TableHead className="w-24 text-center">Acciones</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {s.retiros.map((r) => {
                                  const retiro = retirosById[r.id]
                                  return (
                                    <TableRow key={r.id}>
                                      <TableCell className="text-xs">{formatDate(r.fecha)}</TableCell>
                                      <TableCell className="text-sm">{r.concepto}</TableCell>
                                      <TableCell className="text-xs text-muted-foreground">
                                        {r.referencia || '-'}
                                      </TableCell>
                                      <TableCell className="text-right text-red-700 font-medium">
                                        −{formatCurrency(r.monto)}
                                      </TableCell>
                                      <TableCell className="text-center">
                                        <div className="flex justify-center gap-1">
                                          {retiro && (
                                            <Button
                                              size="icon"
                                              variant="ghost"
                                              className="h-7 w-7"
                                              onClick={(e) => {
                                                e.stopPropagation()
                                                setRetiroEdit(retiro)
                                              }}
                                            >
                                              <Pencil className="h-3 w-3" />
                                            </Button>
                                          )}
                                          {isAdmin && (
                                            <Button
                                              size="icon"
                                              variant="ghost"
                                              className="h-7 w-7"
                                              onClick={(e) => {
                                                e.stopPropagation()
                                                deleteRetiroMutation.mutate(r.id)
                                              }}
                                            >
                                              <Trash2 className="h-3 w-3 text-destructive" />
                                            </Button>
                                          )}
                                        </div>
                                      </TableCell>
                                    </TableRow>
                                  )
                                })}
                              </TableBody>
                            </Table>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Dialog: Aporte (crear) */}
      <Dialog open={isAporteOpen} onOpenChange={setIsAporteOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar aporte de socio</DialogTitle>
            <DialogDescription>El aporte suma como ingreso de la empresa.</DialogDescription>
          </DialogHeader>
          <form onSubmit={aporteForm.handleSubmit(onSubmitAporte)} className="space-y-4">
            <div className="space-y-2">
              <Label>Socio *</Label>
              <Select onValueChange={(v) => aporteForm.setValue('socio_id', v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar socio" />
                </SelectTrigger>
                <SelectContent>
                  {socios?.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.nombre} {s.apellido || ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {aporteForm.formState.errors.socio_id && (
                <p className="text-sm text-destructive">{aporteForm.formState.errors.socio_id.message}</p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Monto *</Label>
                <Input
                  type="number"
                  step="0.01"
                  {...aporteForm.register('monto', { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label>Fecha *</Label>
                <Input type="date" {...aporteForm.register('fecha')} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Cuenta destino</Label>
              <Select onValueChange={(v) => aporteForm.setValue('cuenta_id', v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Opcional" />
                </SelectTrigger>
                <SelectContent>
                  {cuentas?.map((c) => (
                    <SelectItem key={c.id} value={c.id}>{c.nombre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Concepto</Label>
              <Input {...aporteForm.register('concepto')} placeholder="Ej: Aporte de capital" />
            </div>
            <div className="space-y-2">
              <Label>Observaciones</Label>
              <Textarea {...aporteForm.register('observaciones')} rows={2} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsAporteOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createAporteMutation.isPending}>
                Registrar aporte
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Aporte (editar) */}
      <Dialog open={!!aporteEdit} onOpenChange={(o) => !o && setAporteEdit(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Editar aporte</DialogTitle>
            <DialogDescription>
              Socio: {aporteEdit?.socio_nombre}
            </DialogDescription>
          </DialogHeader>
          {aporteEdit && (
            <EditForm
              tipo="aporte"
              initial={aporteEdit}
              cuentas={cuentas || []}
              loading={updateAporteMutation.isPending}
              onCancel={() => setAporteEdit(null)}
              onSubmit={(data) => updateAporteMutation.mutate({ id: aporteEdit.id, data })}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog: Retiro (crear) */}
      <Dialog open={isRetiroOpen} onOpenChange={setIsRetiroOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar retiro de socio</DialogTitle>
            <DialogDescription>Se descuenta de la ganancia del socio.</DialogDescription>
          </DialogHeader>
          <form onSubmit={retiroForm.handleSubmit(onSubmitRetiro)} className="space-y-4">
            <div className="space-y-2">
              <Label>Socio *</Label>
              <Select
                value={socioSeleccionado}
                onValueChange={(v) => {
                  setSocioSeleccionado(v)
                  retiroForm.setValue('socio_id', v)
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar socio" />
                </SelectTrigger>
                <SelectContent>
                  {socios?.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.nombre} {s.apellido || ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {retiroForm.formState.errors.socio_id && (
                <p className="text-sm text-destructive">{retiroForm.formState.errors.socio_id.message}</p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Monto *</Label>
                <Input
                  type="number"
                  step="0.01"
                  {...retiroForm.register('monto', { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label>Fecha *</Label>
                <Input type="date" {...retiroForm.register('fecha')} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Cuenta origen</Label>
              <Select onValueChange={(v) => retiroForm.setValue('cuenta_id', v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Opcional" />
                </SelectTrigger>
                <SelectContent>
                  {cuentas?.map((c) => (
                    <SelectItem key={c.id} value={c.id}>{c.nombre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Concepto</Label>
              <Input {...retiroForm.register('concepto')} placeholder="Ej: Retiro mensual" />
            </div>
            <div className="space-y-2">
              <Label>Observaciones</Label>
              <Textarea {...retiroForm.register('observaciones')} rows={2} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsRetiroOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createRetiroMutation.isPending}>
                Registrar retiro
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Retiro (editar) */}
      <Dialog open={!!retiroEdit} onOpenChange={(o) => !o && setRetiroEdit(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Editar retiro</DialogTitle>
            <DialogDescription>
              Socio: {retiroEdit?.socio_nombre}
            </DialogDescription>
          </DialogHeader>
          {retiroEdit && (
            <EditForm
              tipo="retiro"
              initial={retiroEdit}
              cuentas={cuentas || []}
              loading={updateRetiroMutation.isPending}
              onCancel={() => setRetiroEdit(null)}
              onSubmit={(data) => updateRetiroMutation.mutate({ id: retiroEdit.id, data })}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog: Socio */}
      <Dialog open={isSocioOpen} onOpenChange={setIsSocioOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Nuevo socio</DialogTitle>
            <DialogDescription>
              Los porcentajes de participacion se usan para distribuir la ganancia.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={socioForm.handleSubmit(onSubmitSocio)} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Nombre *</Label>
                <Input {...socioForm.register('nombre')} />
              </div>
              <div className="space-y-2">
                <Label>Apellido</Label>
                <Input {...socioForm.register('apellido')} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Porcentaje de participacion (%)</Label>
              <Input
                type="number"
                step="0.01"
                {...socioForm.register('porcentaje_participacion', { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input type="email" {...socioForm.register('email')} />
            </div>
            <div className="space-y-2">
              <Label>Telefono</Label>
              <Input {...socioForm.register('telefono')} />
            </div>
            <div className="space-y-2">
              <Label>Notas</Label>
              <Textarea {...socioForm.register('notas')} rows={2} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsSocioOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createSocioMutation.isPending}>
                Crear socio
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog: Gestion de planillas de ingreso */}
      <Dialog open={isPlanillasOpen} onOpenChange={setIsPlanillasOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Gestionar planillas de ingreso</DialogTitle>
            <DialogDescription>
              Podés agregar, renombrar o eliminar planillas. Se aplican al elegir "Planilla" al cargar un ingreso.
            </DialogDescription>
          </DialogHeader>

          {/* Alta */}
          <form onSubmit={tipoForm.handleSubmit(onSubmitTipo)} className="grid grid-cols-[1fr_100px_auto] gap-2 items-end">
            <div className="space-y-1">
              <Label className="text-xs">Nueva planilla</Label>
              <Input {...tipoForm.register('nombre')} placeholder="Ej: Comisiones, Alquileres..." />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Color</Label>
              <Input type="color" {...tipoForm.register('color')} />
            </div>
            <Button type="submit" disabled={createTipoMutation.isPending}>
              <Plus className="h-4 w-4 mr-1" /> Agregar
            </Button>
          </form>

          {/* Lista */}
          <div className="space-y-2 mt-4">
            {tiposIngreso?.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No hay planillas creadas.
              </p>
            ) : (
              tiposIngreso?.map((t) => (
                <div key={t.id} className="flex items-center gap-3 p-3 rounded border">
                  <div
                    className="w-4 h-4 rounded flex-shrink-0"
                    style={{ backgroundColor: t.color }}
                  />
                  {tipoEdit?.id === t.id ? (
                    <>
                      <Input
                        defaultValue={t.nombre}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            const v = (e.target as HTMLInputElement).value
                            if (v.trim()) {
                              updateTipoMutation.mutate({ id: t.id, data: { nombre: v.trim() } })
                            }
                          }
                          if (e.key === 'Escape') setTipoEdit(null)
                        }}
                        autoFocus
                        className="flex-1"
                      />
                      <Button size="sm" variant="ghost" onClick={() => setTipoEdit(null)}>
                        Cancelar
                      </Button>
                    </>
                  ) : (
                    <>
                      <div className="flex-1">
                        <p className="font-medium">{t.nombre}</p>
                        {t.es_aporte_socio && (
                          <Badge variant="outline" className="mt-1 text-xs">
                            Planilla de aportes de socios
                          </Badge>
                        )}
                      </div>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => setTipoEdit(t)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      {isAdmin && (
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => {
                            if (confirm(`Eliminar planilla "${t.nombre}"? Los ingresos ya cargados quedaran sin clasificar.`)) {
                              deleteTipoMutation.mutate(t.id)
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      )}
                    </>
                  )}
                </div>
              ))
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPlanillasOpen(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}


// ============ EditForm (aporte / retiro) ============

interface EditFormProps {
  tipo: 'aporte' | 'retiro'
  initial: AporteSocio | RetiroSocio
  cuentas: Array<{ id: string; nombre: string }>
  loading: boolean
  onCancel: () => void
  onSubmit: (data: panelSocios.AporteSocioUpdate | panelSocios.RetiroSocioUpdate) => void
}

function EditForm({ tipo, initial, cuentas, loading, onCancel, onSubmit }: EditFormProps) {
  const [monto, setMonto] = useState<number>(initial.monto)
  const [fecha, setFecha] = useState<string>(initial.fecha)
  const [concepto, setConcepto] = useState<string>(initial.concepto || '')
  const [observaciones, setObservaciones] = useState<string>(initial.observaciones || '')
  const [cuentaId, setCuentaId] = useState<string | undefined>(initial.cuenta_id || undefined)

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit({
          monto,
          fecha,
          concepto: concepto || undefined,
          observaciones: observaciones || undefined,
          cuenta_id: cuentaId || undefined,
        })
      }}
      className="space-y-4"
    >
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>Monto *</Label>
          <Input
            type="number"
            step="0.01"
            value={monto}
            onChange={(e) => setMonto(Number(e.target.value))}
          />
        </div>
        <div className="space-y-2">
          <Label>Fecha *</Label>
          <Input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label>{tipo === 'aporte' ? 'Cuenta destino' : 'Cuenta origen'}</Label>
        <Select value={cuentaId} onValueChange={setCuentaId}>
          <SelectTrigger>
            <SelectValue placeholder="Opcional" />
          </SelectTrigger>
          <SelectContent>
            {cuentas.map((c) => (
              <SelectItem key={c.id} value={c.id}>{c.nombre}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-2">
        <Label>Concepto</Label>
        <Input value={concepto} onChange={(e) => setConcepto(e.target.value)} />
      </div>
      <div className="space-y-2">
        <Label>Observaciones</Label>
        <Textarea
          value={observaciones}
          onChange={(e) => setObservaciones(e.target.value)}
          rows={2}
        />
      </div>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={loading}>
          Guardar cambios
        </Button>
      </DialogFooter>
    </form>
  )
}
