import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchSamples } from '@/lib/api'

/** `error` = no hay servidor; `waiting` = servidor arriba pero el ESP8266 no emite. */
export type ConnectionStatus = 'idle' | 'connected' | 'waiting' | 'error'

export interface EcgStream {
  /** Buffer circular con las muestras más recientes, en voltios. */
  buffer: number[]
  bpm: number | null
  status: ConnectionStatus
  sampleRate: number
  running: boolean
  demo: boolean
  start: () => void
  stop: () => void
  setDemo: (on: boolean) => void
}

/** El firmware muestrea a ~100 Hz (`delay(10)`), así que esto es ~10 s de traza. */
const BUFFER_SIZE = 1000
const POLL_INTERVAL_MS = 200

const DEMO_RATE = 100
const DEMO_BPM = 72
const DEMO_BEAT_SAMPLES = Math.round((DEMO_RATE * 60) / DEMO_BPM)

/** Señal ECG sintética en voltios (onda P, complejo QRS, onda T) para probar sin hardware. */
function demoSamples(t: number, count: number): number[] {
  const out: number[] = []
  for (let i = 0; i < count; i++) {
    const phase = ((t + i) % DEMO_BEAT_SAMPLES) / DEMO_BEAT_SAMPLES
    let v = 1.65 // línea base a media escala, como el AD8232
    v += 0.13 * Math.exp(-(((phase - 0.18) / 0.035) ** 2)) // P
    v -= 0.19 * Math.exp(-(((phase - 0.36) / 0.012) ** 2)) // Q
    v += 1.13 * Math.exp(-(((phase - 0.4) / 0.014) ** 2)) // R
    v -= 0.29 * Math.exp(-(((phase - 0.44) / 0.014) ** 2)) // S
    v += 0.26 * Math.exp(-(((phase - 0.65) / 0.06) ** 2)) // T
    v += (Math.random() - 0.5) * 0.02 // ruido
    out.push(v)
  }
  return out
}

export function useEcgStream(): EcgStream {
  const [buffer, setBuffer] = useState<number[]>([])
  const [bpm, setBpm] = useState<number | null>(null)
  const [status, setStatus] = useState<ConnectionStatus>('idle')
  const [sampleRate, setSampleRate] = useState(0)
  const [running, setRunning] = useState(false)
  const [demo, setDemo] = useState(false)

  const demoClock = useRef(0)
  /** Última posición leída del flujo del servidor. */
  const cursor = useRef<number | null>(null)

  const push = useCallback((incoming: number[]) => {
    setBuffer((prev) => {
      const next = prev.concat(incoming)
      return next.length > BUFFER_SIZE ? next.slice(next.length - BUFFER_SIZE) : next
    })
  }, [])

  useEffect(() => {
    if (!running) return

    let cancelled = false
    // Al arrancar (o al salir del modo demo) pedimos desde donde esté el servidor.
    cursor.current = null

    const tick = async () => {
      if (demo) {
        const count = Math.round((DEMO_RATE * POLL_INTERVAL_MS) / 1000)
        push(demoSamples(demoClock.current, count))
        demoClock.current += count
        setBpm(DEMO_BPM)
        setSampleRate(DEMO_RATE)
        setStatus('connected')
        return
      }
      try {
        const reading = await fetchSamples(cursor.current)
        if (cancelled) return
        if (reading.cursor != null) cursor.current = reading.cursor
        push(reading.samples)
        setBpm(reading.bpm ?? null)
        setSampleRate(reading.sampleRate ?? 0)
        setStatus(reading.connected ? 'connected' : 'waiting')
      } catch {
        if (!cancelled) setStatus('error')
      }
    }

    tick()
    const id = setInterval(tick, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [running, demo, push])

  const start = useCallback(() => setRunning(true), [])
  const stop = useCallback(() => {
    setRunning(false)
    setStatus('idle')
  }, [])

  return { buffer, bpm, status, sampleRate, running, demo, start, stop, setDemo }
}
