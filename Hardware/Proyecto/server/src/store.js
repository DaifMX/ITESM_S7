/**
 * Buffer circular de muestras con cursor monotónico.
 *
 * El cursor permite que varios clientes lean el flujo sin pisarse: cada uno
 * pide `?since=<cursor>` y recibe sólo lo que le falta. Un cliente que no
 * manda cursor (el contrato original del dashboard) usa un cursor global
 * compartido, es decir, vacía lo acumulado desde su última consulta.
 */
export class SampleStore {
  /** @param {{capacity?: number}} [options] */
  constructor(options = {}) {
    this.capacity = options.capacity ?? 60_000 // ~10 min a 100 Hz
    /** @type {number[]} */
    this.buffer = []
    /** Total de muestras vistas desde el arranque; extremo derecho del cursor. */
    this.total = 0
    /** Cursor de los clientes que no mandan `since`. */
    this.pullCursor = 0
    /** @type {number|null} Tasa de muestreo estimada (EWMA), en Hz. */
    this.rate = null
    /** @type {number|null} */
    this.declaredRate = null
    /** @type {number|null} BPM reportado por el firmware, si lo manda. */
    this.reportedBpm = null
    /** @type {string|null} */
    this.device = null
    /** @type {number|null} */
    this.lastPushAt = null
    this.startedAt = Date.now()
  }

  /**
   * @param {number[]} samples  muestras en voltios, más antigua primero
   * @param {{bpm?: number, sampleRate?: number, device?: string}} [meta]
   */
  push(samples, meta = {}) {
    if (meta.bpm != null) this.reportedBpm = meta.bpm
    if (meta.sampleRate != null) this.declaredRate = meta.sampleRate
    if (meta.device) this.device = meta.device
    if (!samples.length) return

    const now = Date.now()
    if (this.lastPushAt != null) {
      const dt = (now - this.lastPushAt) / 1000
      // Ignoramos intervalos absurdos (reconexiones, pausas del firmware).
      if (dt > 0.0005 && dt < 5) {
        const instant = samples.length / dt
        this.rate = this.rate == null ? instant : this.rate * 0.85 + instant * 0.15
      }
    }
    this.lastPushAt = now

    this.buffer.push(...samples)
    this.total += samples.length
    if (this.buffer.length > this.capacity) {
      this.buffer.splice(0, this.buffer.length - this.capacity)
    }
  }

  /** Índice absoluto de la muestra más antigua que seguimos guardando. */
  get firstIndex() {
    return this.total - this.buffer.length
  }

  /** Tasa de muestreo efectiva: la declarada por el firmware o la estimada. */
  get sampleRate() {
    if (this.declaredRate) return this.declaredRate
    return this.rate ? Math.round(this.rate) : null
  }

  /**
   * @param {number|null} [since] cursor del cliente; `null` usa el cursor global
   * @returns {{samples: number[], cursor: number, dropped: number}}
   */
  read(since = null) {
    const useShared = since == null || !Number.isFinite(since)
    let from = useShared ? this.pullCursor : since
    from = Math.min(Math.max(from, 0), this.total)

    // Muestras que se perdieron porque el buffer dio la vuelta.
    const dropped = Math.max(0, this.firstIndex - from)
    const start = Math.max(from, this.firstIndex)
    const samples = this.buffer.slice(start - this.firstIndex)

    if (useShared) this.pullCursor = this.total
    return { samples, cursor: this.total, dropped }
  }

  /** Ventana reciente sin mover ningún cursor (para calcular BPM). */
  window(count) {
    return count >= this.buffer.length ? this.buffer : this.buffer.slice(-count)
  }

  reset() {
    this.buffer = []
    this.total = 0
    this.pullCursor = 0
    this.rate = null
    this.reportedBpm = null
    this.lastPushAt = null
  }
}
