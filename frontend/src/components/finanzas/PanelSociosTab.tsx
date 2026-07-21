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
  TrendingUp,
  TrendingDown,
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

type AporteForm = z.infer<typeof aporteSchema>
type RetiroForm = z.infer<typeof retiroSchema>
type SocioForm = z.infer<typeof socioSchema>

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

  const invalidar = () => {
    queryClient.invalidateQueries({ queryKey: ['panel-socios-resumen'] })
    queryClient.invalidateQueries({ queryKey: ['socios'] })
    queryClient.invalidateQueries({ queryKey: ['transacciones'] })
    queryClient.invalidateQueries({ queryKey: ['finanzas-dashboard'] })
  }

  // Mutations
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

  const deleteRetiroMutation = useMutation({
    mutationFn: panelSocios.deleteRetiro,
    onSuccess: () => {
      invalidar()
      toast({ title: 'Retiro eliminado' })
    },
  })

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
                <CardDescription>Click en una planilla para ver el detalle</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {resumen!.planillas_ingresos.map((p) => {
                  const abierta = openPlanilla === p.tipo
                  return (
                    <div key={p.tipo} className="rounded border">
                      <button
                        type="button"
                        onClick={() => setOpenPlanilla(abierta ? null : p.tipo)}
                        className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition"
                      >
                        <div className="flex items-center gap-3">
                          {abierta ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          <div className="text-left">
                            <p className="font-medium">{p.label}</p>
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
                                    <TableCell className="text-right text-green-700 font-medium">
                                      {formatCurrency(i.monto)}
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
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
                                  {isAdmin && <TableHead className="w-12" />}
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {s.retiros.map((r) => (
                                  <TableRow key={r.id}>
                                    <TableCell className="text-xs">{formatDate(r.fecha)}</TableCell>
                                    <TableCell className="text-sm">{r.concepto}</TableCell>
                                    <TableCell className="text-xs text-muted-foreground">
                                      {r.referencia || '-'}
                                    </TableCell>
                                    <TableCell className="text-right text-red-700 font-medium">
                                      −{formatCurrency(r.monto)}
                                    </TableCell>
                                    {isAdmin && (
                                      <TableCell>
                                        <Button
                                          size="icon"
                                          variant="ghost"
                                          onClick={(e) => {
                                            e.stopPropagation()
                                            deleteRetiroMutation.mutate(r.id)
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

      {/* Dialog: Aporte */}
      <Dialog open={isAporteOpen} onOpenChange={setIsAporteOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar aporte de socio</DialogTitle>
            <DialogDescription>
              El aporte suma como ingreso de la empresa.
            </DialogDescription>
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

      {/* Dialog: Retiro */}
      <Dialog open={isRetiroOpen} onOpenChange={setIsRetiroOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar retiro de socio</DialogTitle>
            <DialogDescription>
              El retiro se descuenta de la ganancia del socio.
            </DialogDescription>
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

      {/* Dialog: Socio nuevo */}
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
    </div>
  )
}
