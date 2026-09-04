import { useEffect, useRef } from 'react'

interface EcgChartProps {
  /** Muestras en voltios (0–3.3), la más antigua primero. */
  samples: number[]
  className?: string
}

/**
 * Canvas-based scrolling ECG trace. Canvas (instead of an SVG chart library)
 * keeps redraws cheap at ECG sample rates.
 */
export function EcgChart({ samples, className }: EcgChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    const { clientWidth: w, clientHeight: h } = canvas
    if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
      canvas.width = w * dpr
      canvas.height = h * dpr
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    const styles = getComputedStyle(canvas)
    const gridColor = styles.getPropertyValue('--color-border') || '#ddd'
    const traceColor = '#22c55e'

    ctx.clearRect(0, 0, w, h)

    // Grid: minor every 8px, major every 40px (mimics ECG paper)
    ctx.lineWidth = 1
    for (let x = 0; x < w; x += 8) {
      ctx.strokeStyle = gridColor
      ctx.globalAlpha = x % 40 === 0 ? 0.8 : 0.3
      ctx.beginPath()
      ctx.moveTo(x + 0.5, 0)
      ctx.lineTo(x + 0.5, h)
      ctx.stroke()
    }
    for (let y = 0; y < h; y += 8) {
      ctx.strokeStyle = gridColor
      ctx.globalAlpha = y % 40 === 0 ? 0.8 : 0.3
      ctx.beginPath()
      ctx.moveTo(0, y + 0.5)
      ctx.lineTo(w, y + 0.5)
      ctx.stroke()
    }
    ctx.globalAlpha = 1

    if (samples.length < 2) return

    // Auto-scale vertically around the visible window with some headroom
    const min = Math.min(...samples)
    const max = Math.max(...samples)
    // Rango mínimo de 0.2 V para que una señal plana no se amplifique a ruido.
    const range = Math.max(max - min, 0.2)
    const pad = range * 0.15
    const toY = (v: number) => h - ((v - min + pad) / (range + 2 * pad)) * h

    ctx.strokeStyle = traceColor
    ctx.lineWidth = 2
    ctx.lineJoin = 'round'
    ctx.beginPath()
    for (let i = 0; i < samples.length; i++) {
      const x = (i / (samples.length - 1)) * w
      const y = toY(samples[i])
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.stroke()
  }, [samples])

  return <canvas ref={canvasRef} className={className} />
}
