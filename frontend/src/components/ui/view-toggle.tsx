import { LayoutGrid, List } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export type ViewMode = 'cards' | 'list'

interface ViewToggleProps {
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
  className?: string
}

export function ViewToggle({ viewMode, onViewModeChange, className }: ViewToggleProps) {
  return (
    <div className={cn('flex items-center border rounded-md', className)}>
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          'rounded-r-none px-3',
          viewMode === 'cards' && 'bg-muted'
        )}
        onClick={() => onViewModeChange('cards')}
        title="Vista de tarjetas"
      >
        <LayoutGrid className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          'rounded-l-none px-3 border-l',
          viewMode === 'list' && 'bg-muted'
        )}
        onClick={() => onViewModeChange('list')}
        title="Vista de lista"
      >
        <List className="h-4 w-4" />
      </Button>
    </div>
  )
}
