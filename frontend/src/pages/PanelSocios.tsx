import { PanelSociosTab } from '@/components/finanzas/PanelSociosTab'

export function PanelSociosPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Panel de Socios</h1>
        <p className="text-muted-foreground">
          Control gerencial: ingresos, gastos, ganancia y distribución entre socios
        </p>
      </div>
      <PanelSociosTab />
    </div>
  )
}
