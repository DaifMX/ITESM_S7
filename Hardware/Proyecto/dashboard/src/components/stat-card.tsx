import { Card, CardContent } from '@/components/ui/card'

interface StatCardProps {
  label: string
  value: string
  unit?: string
  icon?: React.ReactNode
}

export function StatCard({ label, value, unit, icon }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        {icon && <div className="text-muted-foreground">{icon}</div>}
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-semibold tabular-nums">
            {value}
            {unit && <span className="ml-1 text-sm font-normal text-muted-foreground">{unit}</span>}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
