import { parseReading } from './parse.js'

/**
 * Lee el puerto serie del ESP8266 y empuja las muestras al store.
 *
 * Corresponde al sketch que sólo hace `Serial.println(voltaje)`: una línea
 * de texto por muestra, a 115200 baudios y ~100 Hz. Cada línea pasa por
 * `parseReading`, así que también sirve si más adelante el firmware agrupa
 * muestras en un array JSON por línea.
 *
 * `serialport` es una dependencia nativa: si no está instalada el servidor
 * arranca igual y sólo quedan disponibles los otros orígenes de datos.
 */

/** Identificadores USB de los conversores que montan las placas ESP8266. */
const KNOWN_VENDORS = [
  '10c4', // Silicon Labs CP210x (NodeMCU v2, Wemos D1)
  '1a86', // WCH CH340/CH341 (NodeMCU v3)
  '0403', // FTDI
  '303a', // Espressif USB nativo (ESP32-S2/S3/C3)
]

const RECONNECT_MS = 2000

export class SerialLink {
  /**
   * @param {{
   *   store: import('./store.js').SampleStore,
   *   path?: string|null,
   *   baudRate?: number,
   *   unit?: 'volts'|'adc'|'auto',
   *   log?: (msg: string) => void,
   * }} options
   */
  constructor(options) {
    this.store = options.store
    this.path = options.path ?? null
    this.baudRate = options.baudRate ?? 115200
    this.unit = options.unit ?? 'auto'
    this.resetOnConnect = options.resetOnConnect ?? false
    this.log = options.log ?? (() => {})

    this.connected = false
    this.available = true
    /** @type {string|null} Puerto realmente abierto. */
    this.activePath = null
    /** @type {string|null} */
    this.lastError = null
    this.stopped = false

    this.port = null
    this.timer = null
    this.SerialPort = null
    this.ReadlineParser = null
  }

  async start() {
    try {
      const [{ SerialPort }, { ReadlineParser }] = await Promise.all([
        import('serialport'),
        import('@serialport/parser-readline'),
      ])
      this.SerialPort = SerialPort
      this.ReadlineParser = ReadlineParser
    } catch {
      this.available = false
      this.lastError = 'serialport no está instalado'
      this.log('Serie: módulo `serialport` no disponible, se omite este origen.')
      return
    }
    this.connect()
  }

  /** Primer puerto que parece un ESP8266; si no hay, el primer USB serie. */
  async resolvePath() {
    if (this.path) return this.path
    const ports = await this.SerialPort.list()
    const candidates = ports.filter((p) => p.path && !p.path.includes('Bluetooth'))
    const known = candidates.find((p) =>
      KNOWN_VENDORS.includes(String(p.vendorId ?? '').toLowerCase()),
    )
    if (known) return known.path
    const usb = candidates.find((p) => /usb|wch|slab|modem/i.test(p.path))
    return usb ? usb.path : null
  }

  async connect() {
    if (this.stopped) return
    let path
    try {
      path = await this.resolvePath()
    } catch (err) {
      this.lastError = err.message
      return this.retry()
    }

    if (!path) {
      this.lastError = 'ningún puerto serie detectado'
      return this.retry()
    }

    const port = new this.SerialPort({ path, baudRate: this.baudRate, autoOpen: false })
    this.port = port

    port.open((err) => {
      if (err) {
        this.connected = false
        this.lastError = err.message
        // El Monitor/Plotter Serie del IDE de Arduino toma el puerto en exclusiva.
        if (/access denied|resource busy|cannot open|lock/i.test(err.message)) {
          this.log(`Serie: ${path} ocupado. Cierra el Monitor Serie del IDE de Arduino.`)
        }
        return this.retry()
      }
      this.connected = true
      this.activePath = path
      this.lastError = null
      this.log(`Serie: conectado a ${path} @ ${this.baudRate} baudios.`)
      this.applyControlLines(port)
    })

    const parser = port.pipe(new this.ReadlineParser({ delimiter: '\n' }))
    parser.on('data', (line) => {
      const reading = parseReading(line, { unit: this.unit })
      if (reading.samples.length) {
        this.store.push(reading.samples, { ...reading, device: reading.device ?? `serial:${path}` })
      }
    })

    port.on('error', (err) => {
      this.lastError = err.message
    })
    port.on('close', () => {
      if (this.connected) this.log(`Serie: se cerró ${path}.`)
      this.connected = false
      this.activePath = null
      this.retry()
    })
  }

  /**
   * Deja las líneas de control en reposo.
   *
   * En las placas ESP8266/ESP32 con autoreset, RTS va a RESET y DTR a GPIO0.
   * `serialport` las activa al abrir, así que sin esto la placa se queda
   * retenida en reset (o arranca en modo bootloader) y no transmite nada.
   */
  applyControlLines(port) {
    port.set({ dtr: false, rts: false }, (err) => {
      // Best-effort: un pty o un puerto virtual no implementa estos ioctl,
      // y eso no impide leer datos. No lo tratamos como error de conexión.
      if (err) return
      if (this.resetOnConnect) this.pulseReset(port)
    })
  }

  /** Reinicia la placa: RESET abajo 150 ms con GPIO0 en alto (arranque normal). */
  pulseReset(port) {
    port.set({ dtr: false, rts: true }, () => {
      setTimeout(() => {
        port.set({ dtr: false, rts: false }, () => this.log('Serie: placa reiniciada.'))
      }, 150).unref?.()
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
    this.port?.close?.(() => {})
  }

  status() {
    return {
      enabled: this.available,
      connected: this.connected,
      path: this.activePath,
      baudRate: this.baudRate,
      error: this.lastError,
    }
  }
}
