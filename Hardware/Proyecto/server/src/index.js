import path from 'node:path'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'
import express from 'express'
import cors from 'cors'

import { SampleStore } from './store.js'
import { estimateBpm } from './bpm.js'
import { parseReading } from './parse.js'
import { SerialLink } from './serial-link.js'
import { EspLink } from './esp-link.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const DIST_DIR = path.resolve(__dirname, '../../dashboard/dist')

const PORT = Number(process.env.PORT ?? 3001)
const BUFFER_SIZE = Number(process.env.BUFFER_SIZE ?? 60_000)
/** 'volts' | 'adc' | 'auto' — cómo interpretar los números que llegan. */
const INPUT_UNIT = process.env.INPUT_UNIT ?? 'auto'

// Origen serie (el sketch actual: Serial.println(voltaje) a 115200).
const SERIAL_ENABLED = process.env.SERIAL !== 'off'
const SERIAL_PATH = process.env.SERIAL_PATH || null // p. ej. /dev/tty.usbserial-0001
const SERIAL_BAUD = Number(process.env.SERIAL_BAUD ?? 115200)
/** SERIAL_RESET=on reinicia la placa al conectar, para no perder el inicio del flujo. */
const SERIAL_RESET = process.env.SERIAL_RESET === 'on'

// Origen WiFi (el sketch con WebSocketsServer en el puerto 81).
const ESP_HOST = process.env.ESP_HOST || null
const ESP_WS_PORT = Number(process.env.ESP_WS_PORT ?? 81)

const log = (msg) => console.log(`[ecg] ${msg}`)

const store = new SampleStore({ capacity: BUFFER_SIZE })

/** Ventana de 6 s para el detector de picos R. */
function currentBpm() {
  if (store.reportedBpm != null) return store.reportedBpm
  const rate = store.sampleRate
  if (!rate) return null
  return estimateBpm(store.window(rate * 6), rate)
}

/** Sin muestras nuevas en este tiempo damos la fuente por caída. */
const IDLE_MS = 2000

function isLive() {
  return store.lastPushAt != null && Date.now() - store.lastPushAt < IDLE_MS
}

const app = express()
app.use(cors())
// Los tres cuerpos que puede mandar un firmware por HTTP.
app.use(express.json({ limit: '2mb' }))
app.use(express.text({ type: ['text/plain', 'text/csv'], limit: '2mb' }))
app.use(express.raw({ type: 'application/octet-stream', limit: '2mb' }))

const api = express.Router()

/**
 * Lectura del dashboard.
 *
 * `?since=<cursor>` devuelve sólo lo posterior a ese cursor. Sin `since` se
 * usa un cursor global: cada consulta vacía lo acumulado desde la anterior,
 * que es el comportamiento que ya esperaba el dashboard.
 */
api.get('/samples', (req, res) => {
  const since = req.query.since != null ? Number(req.query.since) : null
  const { samples, cursor, dropped } = store.read(Number.isFinite(since) ? since : null)
  res.json({
    samples,
    cursor,
    dropped,
    bpm: currentBpm(),
    sampleRate: store.sampleRate,
    device: store.device,
    connected: isLive(),
    unit: 'V',
  })
})

/**
 * Ingesta por HTTP, para un firmware que prefiera empujar en vez de que el
 * servidor lo lea. Acepta JSON, texto plano/CSV y uint16 little-endian.
 */
function ingest(req, res) {
  const reading = parseReading(req.body, { unit: INPUT_UNIT })
  if (!reading.samples.length) {
    return res.status(400).json({ ok: false, error: 'sin muestras reconocibles en el cuerpo' })
  }
  store.push(reading.samples, { ...reading, device: reading.device ?? req.ip })
  // Respuesta corta: el ESP8266 tiene poca RAM para parsear.
  res.json({ ok: true, received: reading.samples.length, total: store.total })
}

api.post('/samples', ingest)
api.post('/ingest', ingest)

/** Ingesta por query string, para firmware que sólo sabe hacer GET. */
api.get('/ingest', (req, res) => {
  const raw = req.query.values ?? req.query.samples ?? req.query.v
  const reading = parseReading(String(raw ?? ''), { unit: INPUT_UNIT })
  if (!reading.samples.length) {
    return res.status(400).json({ ok: false, error: 'usa ?values=1.23,1.24' })
  }
  store.push(reading.samples, { device: `http:${req.ip}` })
  res.json({ ok: true, received: reading.samples.length, total: store.total })
})

api.get('/health', (_req, res) => {
  res.json({
    ok: true,
    live: isLive(),
    uptimeSeconds: Math.round((Date.now() - store.startedAt) / 1000),
    buffered: store.buffer.length,
    total: store.total,
    sampleRate: store.sampleRate,
    bpm: currentBpm(),
    device: store.device,
    lastSampleAt: store.lastPushAt,
    sources: {
      serial: serialLink ? serialLink.status() : { enabled: false },
      websocket: espLink ? espLink.status() : { enabled: false },
      http: { enabled: true },
    },
  })
})

api.post('/reset', (_req, res) => {
  store.reset()
  res.json({ ok: true })
})

app.use('/api', api)

// En producción el dashboard compilado se sirve desde aquí, así que todo
// (datos y UI) vive en un mismo origen y no hacen falta encabezados CORS.
if (fs.existsSync(DIST_DIR)) {
  app.use(express.static(DIST_DIR))
  app.use((req, res, next) => {
    if (req.method !== 'GET' || req.path.startsWith('/api')) return next()
    res.sendFile(path.join(DIST_DIR, 'index.html'))
  })
} else {
  app.get('/', (_req, res) => {
    res.type('text/plain').send(
      'API ECG activa en /api/samples.\n' +
        'El dashboard compilado no existe todavía: corre `pnpm build` en dashboard/,\n' +
        'o usa `pnpm dev` y entra por el servidor de Vite.\n',
    )
  })
}

/** @type {SerialLink|null} */
let serialLink = null
/** @type {EspLink|null} */
let espLink = null

if (SERIAL_ENABLED) {
  serialLink = new SerialLink({
    store,
    path: SERIAL_PATH,
    baudRate: SERIAL_BAUD,
    unit: INPUT_UNIT,
    resetOnConnect: SERIAL_RESET,
    log,
  })
  serialLink.start()
}

if (ESP_HOST) {
  espLink = new EspLink({ store, host: ESP_HOST, port: ESP_WS_PORT, unit: INPUT_UNIT, log })
  espLink.start()
}

const server = app.listen(PORT, () => {
  log(`API escuchando en http://localhost:${PORT}/api`)
  if (SERIAL_ENABLED) log(`Serie: buscando el ESP8266${SERIAL_PATH ? ` en ${SERIAL_PATH}` : ''}…`)
  if (ESP_HOST) log(`WebSocket: ${ESP_HOST}:${ESP_WS_PORT}`)
  if (!SERIAL_ENABLED && !ESP_HOST) log('Sin orígenes activos; sólo ingesta por HTTP.')
})

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    serialLink?.stop()
    espLink?.stop()
    server.close(() => process.exit(0))
  })
}
