import { Activity, HeartPulse, Radio } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { EcgChart } from '@/components/ecg-chart'
import { StatCard } from '@/components/stat-card'
import { useEcgStream } from '@/hooks/use-ecg-stream'

const STATUS_LABEL = {
  idle: 'Detenido',
  connected: 'Conectado',
  waiting: 'Sin señal',
  error: 'Sin servidor',
} as const

const STATUS_VARIANT = {
  idle: 'secondary',
  connected: 'default',
  waiting: 'outline',
  error: 'destructive',
} as const

export default function App() {
  const ecg = useEcgStream()

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <HeartPulse className="size-6 text-green-500" />
            <h1 className="text-lg font-semibold">Monitor ECG — ESP8266</h1>
          </div>
          <Badge variant={STATUS_VARIANT[ecg.status]}>{STATUS_LABEL[ecg.status]}</Badge>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-6 py-6">
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Frecuencia cardíaca"
            value={ecg.bpm != null ? String(ecg.bpm) : '--'}
            unit="bpm"
            icon={<HeartPulse className="size-8" />}
          />
          <StatCard
            label="Tasa de muestreo"
            value={ecg.sampleRate > 0 ? String(ecg.sampleRate) : '--'}
            unit="Hz"
            icon={<Activity className="size-8" />}
          />
          <StatCard
            label="Muestras en buffer"
            value={String(ecg.buffer.length)}
            icon={<Radio className="size-8" />}
          />
        </div>

        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle>Electrocardiograma</CardTitle>
              <CardDescription>Señal en tiempo real desde el transmisor</CardDescription>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Switch id="demo" checked={ecg.demo} onCheckedChange={ecg.setDemo} />
                <Label htmlFor="demo">Señal de prueba</Label>
              </div>
              {ecg.running ? (
                <Button variant="outline" onClick={ecg.stop}>Detener</Button>
              ) : (
                <Button onClick={ecg.start}>Iniciar</Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <EcgChart samples={ecg.buffer} className="h-72 w-full rounded-md border" />
          </CardContent>
        </Card>

        <p className="text-sm text-muted-foreground">
          El dashboard consulta <code>/api/samples</code> cada 200 ms. La API de Express lee el
          puerto serie del ESP8266 (115200 baudios) y expone las muestras en voltios; arráncala con{' '}
          <code>pnpm server</code>. «Sin señal» significa que la API responde pero la placa no está
          transmitiendo: revisa que el Monitor Serie del IDE de Arduino esté cerrado. Activa «Señal
          de prueba» para trabajar sin el hardware.
        </p>
      </main>
    </div>
  )
}
