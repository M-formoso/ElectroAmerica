import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { getClientesLista, type ClienteListItem } from '@/services/clientes'
import { depositosService, type Deposito } from '@/services/depositos'

interface Props {
  value: string  // deposito_id final (puede ser deposito padre o subdeposito)
  onChange: (depositoId: string) => void
  disabled?: boolean
  showLabels?: boolean
}

/**
 * Selector encadenado Cliente -> Deposito -> Subdeposito (opcional).
 * Devuelve el `deposito_id` final: si se eligio subdeposito, devuelve ese;
 * sino, el deposito padre.
 */
export function DepositoSelector({ value, onChange, disabled, showLabels = true }: Props) {
  const [clienteId, setClienteId] = useState<string>('')
  const [depositoPadreId, setDepositoPadreId] = useState<string>('')
  const [subdepositoId, setSubdepositoId] = useState<string>('')

  const { data: clientes } = useQuery<ClienteListItem[]>({
    queryKey: ['clientes-lista'],
    queryFn: getClientesLista,
  })

  const { data: depositosPadre } = useQuery<Deposito[]>({
    queryKey: ['depositos-cliente', clienteId],
    queryFn: () => depositosService.list(clienteId),
    enabled: !!clienteId,
  })

  const { data: subdepositos } = useQuery<Deposito[]>({
    queryKey: ['subdepositos', depositoPadreId],
    queryFn: () => depositosService.list(undefined, depositoPadreId),
    enabled: !!depositoPadreId,
  })

  // Cuando cambia cliente, resetear depositos
  useEffect(() => {
    setDepositoPadreId('')
    setSubdepositoId('')
  }, [clienteId])

  // Cuando cambia deposito padre, resetear subdeposito
  useEffect(() => {
    setSubdepositoId('')
  }, [depositoPadreId])

  // Notificar al padre cuando cambia el deposito final
  useEffect(() => {
    const finalId = subdepositoId || depositoPadreId
    if (finalId !== value) {
      onChange(finalId)
    }
  }, [subdepositoId, depositoPadreId])

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        {showLabels && <Label>Cliente</Label>}
        <Select value={clienteId} onValueChange={setClienteId} disabled={disabled}>
          <SelectTrigger>
            <SelectValue placeholder="Seleccioná un cliente" />
          </SelectTrigger>
          <SelectContent>
            {clientes?.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.razon_social || c.nombre_fantasia || c.codigo}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {clienteId && (
        <div className="space-y-2">
          {showLabels && <Label>Depósito</Label>}
          <Select
            value={depositoPadreId}
            onValueChange={setDepositoPadreId}
            disabled={disabled}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccioná un depósito" />
            </SelectTrigger>
            <SelectContent>
              {depositosPadre && depositosPadre.length > 0 ? (
                depositosPadre.map((d) => (
                  <SelectItem key={d.id} value={d.id}>
                    {d.nombre}
                  </SelectItem>
                ))
              ) : (
                <div className="px-2 py-1.5 text-sm text-muted-foreground">
                  Este cliente no tiene depósitos
                </div>
              )}
            </SelectContent>
          </Select>
        </div>
      )}

      {depositoPadreId && subdepositos && subdepositos.length > 0 && (
        <div className="space-y-2">
          {showLabels && <Label>Subdepósito (opcional)</Label>}
          <Select
            value={subdepositoId}
            onValueChange={(v) => setSubdepositoId(v === '__none__' ? '' : v)}
            disabled={disabled}
          >
            <SelectTrigger>
              <SelectValue placeholder="Sin subdepósito" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__none__">— Depósito principal —</SelectItem>
              {subdepositos.map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  {s.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
    </div>
  )
}
