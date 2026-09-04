import WebSocket from 'ws'
import { parseReading } from './parse.js'

/**
 * Cliente WebSocket hacia el ESP8266 cuando el firmware corre
 * `WebSocketsServer webSocket(81)` y hace `broadcastTXT`.
 *
 * El servidor se conecta como cliente (la placa es el servidor), reconecta
 * sola si la placa se reinicia o se cae el WiFi, y vuelca todo al mismo
 * store que el enlace serie, así que el dashboard no nota la diferencia.
 */

const RECONNECT_MS = 2000
const STALE_MS = 5000

export class EspLink {
  /**
   * @param {{
   *   store: import('./store.js').SampleStore,
   *   host: string,
   *   port?: number,
   *   unit?: 'volts'|'adc'|'auto',
   *   log?: (msg: string) => void,
   * }} options
   */
  constructor(options) {
    this.store = options.store
    this.host = options.host
    this.port = options.port ?? 81
    this.unit = options.unit ?? 'auto'
    this.log = options.log ?? (() => {})

    this.url = `ws://${this.host}:${this.port}`
    this.connected = false
    /** @type {number|null} */
    this.lastMessageAt = null
    /** @type {string|null} */
    this.lastError = null
    this.stopped = false
    this.ws = null
    this.timer = null
  }

  start() {
    this.connect()
  }

  connect() {
    if (this.stopped) return
    const ws = new WebSocket(this.url)
    this.ws = ws

    ws.on('open', () => {
      this.connected = true
      this.lastError = null
      this.log(`WebSocket: conectado a ${this.url}.`)
    })

    ws.on('message', (data) => {
      this.lastMessageAt = Date.now()
      const reading = parseReading(Buffer.isBuffer(data) ? data : Buffer.from(data), {
        unit: this.unit,
      })
      if (reading.samples.length) {
        this.store.push(reading.samples, { ...reading, device: reading.device ?? this.url })
      }
    })

    ws.on('error', (err) => {
      this.lastError = err.message
    })

    ws.on('close', () => {
      if (this.connected) this.log(`WebSocket: se perdió ${this.url}.`)
      this.connected = false
      this.retry()
    })
  }

  retry() {
    if (this.stopped || this.timer) return
    this.timer = setTimeout(() => {
      this.timer = null
      this.connect()
    }, RECONNECT_MS)
    this.timer.unref?.()
  }

  stop() {
    this.stopped = true
    if (this.timer) clearTimeout(this.timer)
    this.ws?.terminate?.()
  }

  status() {
    return {
      enabled: true,
      connected: this.connected,
      url: this.url,
      // Conectado pero mudo: el firmware dejó de emitir.
      stale: this.connected && this.lastMessageAt != null && Date.now() - this.lastMessageAt > STALE_MS,
      error: this.lastError,
    }
  }
}
