import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fichajesService } from '@/services/fichajes'
import type { FichajeListItem } from '@/services/fichajes'
import { useToast } from '@/hooks/use-toast'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { LogIn, LogOut, Clock, History, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

function formatDuration(ms: number) {
  const totalSeconds = Math.floor(ms / 1000)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function formatHora(iso: string) {
  return new Date(iso).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
}

function formatFecha(iso: string) {
  return new Date(iso).toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
}

function estadoBadge(estado: string) {
  const map: Record<string, string> = {
    activo: 'bg-green-100 text-green-800',
    completado: 'bg-blue-100 text-blue-800',
    cancelado: 'bg-gray-100 text-gray-600',
  }
  const labels: Record<string, string> = {
    activo: 'Activo',
    completado: 'Completado',
    cancelado: 'Cancelado',
  }
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', map[estado] ?? 'bg-gray-100')}>
      {labels[estado] ?? estado}
    </span>
  )
}

export default function FichajePage() {
  const { toast } = useToast()
  const qc = useQueryClient()
  const [elapsed, setElapsed] = useState(0)
  const [showFinalizarDialog, setShowFinalizarDialog] = useState(false)
  const [notasFin, setNotasFin] = useState('')

  const { data: activo, isLoading } = useQuery({
    queryKey: ['fichaje-activo'],
    queryFn: () => fichajesService.obtenerActivo(),
    refetchInterval: 60_000,
  })

  const { data: historial = [] } = useQuery({
    queryKey: ['mis-fichajes'],
    queryFn: () => fichajesService.misFichajes(10),
  })

  // Timer
  useEffect(() => {
    if (!activo) {
      setElapsed(0)
      return
    }
    const update = () => {
      setElapsed(Date.now() - new Date(activo.hora_inicio).getTime())
    }
    update()
    const interval = setInterval(update, 1000)
    return () => clearInterval(interval)
  }, [activo])

  const iniciarMutation = useMutation({
    mutationFn: () => fichajesService.iniciar(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fichaje-activo'] })
      qc.invalidateQueries({ queryKey: ['mis-fichajes'] })
      toast({ title: 'Entrada fichada', description: 'Tu jornada comenzó. ¡Buen trabajo!' })
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ title: 'Error', description: detail || 'No se pudo fichar entrada', variant: 'destructive' })
    },
  })

  const finalizarMutation = useMutation({
    mutationFn: (id: string) => fichajesService.finalizar(id, { notas_fin: notasFin || undefined }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['fichaje-activo'] })
      qc.invalidateQueries({ queryKey: ['mis-fichajes'] })
      setShowFinalizarDialog(false)
      setNotasFin('')
      toast({
        title: 'Salida fichada',
        description: `Jornada finalizada. Trabajaste ${data.horas_trabajadas}hs.`,
      })
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ title: 'Error', description: detail || 'No se pudo fichar salida', variant: 'destructive' })
    },
  })

  const cancelarMutation = useMutation({
    mutationFn: (id: string) => fichajesService.cancelar(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fichaje-activo'] })
      qc.invalidateQueries({ queryKey: ['mis-fichajes'] })
      toast({ title: 'Fichaje cancelado' })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Clock className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const hayActivo = !!activo

  return (
    <div className="max-w-md mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Fichaje</h1>
        <p className="text-muted-foreground text-sm">
          {new Date().toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </p>
      </div>

      {/* Main clock card */}
      <Card className={cn('text-center', hayActivo && 'border-green-500 border-2')}>
        <CardContent className="pt-8 pb-8 space-y-6">
          {hayActivo ? (
            <>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase tracking-wider">En jornada desde</p>
                <p className="text-2xl font-bold text-green-600">{formatHora(activo.hora_inicio)}</p>
              </div>

              {/* Live timer */}
              <div className="bg-green-50 rounded-2xl py-6 px-4">
                <p className="font-mono text-5xl font-bold text-green-700 tracking-widest">
                  {formatDuration(elapsed)}
                </p>
              </div>

              <div className="flex flex-col gap-3">
                <Button
                  size="lg"
                  className="h-16 text-lg bg-red-600 hover:bg-red-700"
                  onClick={() => setShowFinalizarDialog(true)}
                >
                  <LogOut className="mr-2 h-5 w-5" />
                  FICHAR SALIDA
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground"
                  onClick={() => cancelarMutation.mutate(activo.id)}
                  disabled={cancelarMutation.isPending}
                >
                  <XCircle className="mr-1 h-4 w-4" />
                  Cancelar fichaje
                </Button>
              </div>
            </>
          ) : (
            <>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Estado</p>
                <p className="text-xl font-semibold text-muted-foreground">Sin jornada activa</p>
              </div>

              <div className="bg-gray-50 rounded-2xl py-8 px-4">
                <Clock className="h-16 w-16 mx-auto text-gray-300" />
              </div>

              <Button
                size="lg"
                className="h-16 text-lg w-full"
                onClick={() => iniciarMutation.mutate()}
                disabled={iniciarMutation.isPending}
              >
                <LogIn className="mr-2 h-5 w-5" />
                FICHAR ENTRADA
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Historial reciente */}
      {historial.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <History className="h-4 w-4" />
              Últimos fichajes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {historial.map((f: FichajeListItem) => (
              <div key={f.id} className="flex items-center justify-between py-2 border-b last:border-0">
                <div className="text-sm">
                  <p className="font-medium capitalize">{formatFecha(f.fecha)}</p>
                  <p className="text-muted-foreground text-xs">
                    {formatHora(f.hora_inicio)}
                    {f.hora_fin ? ` → ${formatHora(f.hora_fin)}` : ''}
                    {f.horas_trabajadas ? ` · ${f.horas_trabajadas}hs` : ''}
                  </p>
                </div>
                {estadoBadge(f.estado)}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Finalizar dialog */}
      <Dialog open={showFinalizarDialog} onOpenChange={setShowFinalizarDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Fichar salida</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <p className="text-muted-foreground text-sm">
              Tiempo trabajado: <span className="font-mono font-bold">{formatDuration(elapsed)}</span>
            </p>
            <div className="space-y-2">
              <Label>Notas de cierre (opcional)</Label>
              <Textarea
                placeholder="Ej: Terminé el cableado del tablero 2..."
                value={notasFin}
                onChange={(e) => setNotasFin(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFinalizarDialog(false)}>
              Cancelar
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700"
              onClick={() => activo && finalizarMutation.mutate(activo.id)}
              disabled={finalizarMutation.isPending}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Confirmar salida
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
