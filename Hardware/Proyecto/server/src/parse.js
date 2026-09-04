/**
 * Normalización de las lecturas que llegan del ESP8266.
 *
 * El firmware emite un mensaje de texto por muestra con el voltaje ya
 * convertido, p. ej. `webSocket.broadcastTXT(String(voltaje, 3))` → "1.234".
 * Estas funciones aceptan además los formatos a los que se suele migrar
 * cuando la tasa de muestreo sube y conviene agrupar muestras:
 *
 *   "1.234"                        una muestra suelta
 *   "1.234\n1.240\n1.251"          varias por línea
 *   "1.234,1.240,1.251"            CSV
 *   [1.234, 1.240]                 array JSON
 *   { "samples": [...], "bpm": 72 }  objeto JSON con metadatos
 *   <binario>                      uint16 little-endian (cuentas del ADC)
 */

const SAMPLE_KEYS = ['samples', 'data', 'values', 'ecg', 'readings', 'buffer']
const SINGLE_KEYS = ['sample', 'value', 'voltaje', 'voltage', 'adc', 'v']
const BPM_KEYS = ['bpm', 'heartRate', 'heart_rate', 'hr', 'pulso', 'pulse']
const RATE_KEYS = ['sampleRate', 'sample_rate', 'fs', 'rate', 'hz']
const DEVICE_KEYS = ['device', 'deviceId', 'device_id', 'id', 'chip', 'name']

const ADC_MAX = 1023
const V_REF = 3.3

/** Por encima de este valor una lectura no puede ser un voltaje del ESP8266. */
const VOLT_CEILING = 3.6

function pick(obj, keys) {
  for (const key of keys) {
    if (obj[key] != null) return obj[key]
  }
  return undefined
}

function firstNumber(value) {
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : undefined
}

/**
 * Convierte a voltios. El firmware de referencia ya envía voltios, pero un
 * sketch que mande `analogRead()` en crudo también funciona: cualquier valor
 * por encima de 3.6 sólo puede ser una cuenta del ADC.
 *
 * @param {number[]} values
 * @param {'volts'|'adc'|'auto'} unit
 */
export function toVolts(values, unit = 'auto') {
  if (unit === 'volts') return values
  if (unit === 'adc') return values.map((v) => (v / ADC_MAX) * V_REF)
  const looksLikeAdc = values.some((v) => v > VOLT_CEILING)
  return looksLikeAdc ? values.map((v) => (v / ADC_MAX) * V_REF) : values
}

/** Extrae números de un array que puede traer escalares u objetos `{v: 1.2}`. */
function numbersFromArray(arr) {
  const out = []
  for (const item of arr) {
    if (typeof item === 'number') {
      if (Number.isFinite(item)) out.push(item)
    } else if (typeof item === 'string') {
      const n = Number(item)
      if (Number.isFinite(n)) out.push(n)
    } else if (item && typeof item === 'object') {
      const n = firstNumber(pick(item, SINGLE_KEYS))
      if (n != null) out.push(n)
    }
  }
  return out
}

/** Números separados por coma, punto y coma, espacio o salto de línea. */
function numbersFromText(text) {
  const out = []
  for (const token of text.split(/[\s,;]+/)) {
    if (!token) continue
    const n = Number(token)
    if (Number.isFinite(n)) out.push(n)
  }
  return out
}

function numbersFromBinary(buf) {
  const out = []
  for (let i = 0; i + 1 < buf.length; i += 2) out.push(buf.readUInt16LE(i))
  return out
}

/**
 * @param {unknown} payload  texto, Buffer u objeto ya parseado
 * @param {{unit?: 'volts'|'adc'|'auto'}} [options]
 * @returns {{samples: number[], bpm?: number, sampleRate?: number, device?: string}}
 */
export function parseReading(payload, options = {}) {
  const unit = options.unit ?? 'auto'
  let body = payload

  if (Buffer.isBuffer(payload)) {
    const text = payload.toString('utf8')
    // Un buffer que es texto imprimible viene del broadcastTXT del firmware;
    // si no, son muestras del ADC empaquetadas en binario.
    body = /^[\s\d.,;eE+\-[\]{}":a-zA-Z_]*$/.test(text) && text.trim()
      ? text
      : { samples: numbersFromBinary(payload) }
  }

  if (typeof body === 'string') {
    const trimmed = body.trim()
    if (!trimmed) return { samples: [] }
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        body = JSON.parse(trimmed)
      } catch {
        body = { samples: numbersFromText(trimmed) }
      }
    } else {
      body = { samples: numbersFromText(trimmed) }
    }
  }

  if (Array.isArray(body)) body = { samples: numbersFromArray(body) }
  if (!body || typeof body !== 'object') return { samples: [] }

  let raw = pick(body, SAMPLE_KEYS)
  if (raw == null) {
    const single = firstNumber(pick(body, SINGLE_KEYS))
    raw = single != null ? [single] : []
  }
  if (typeof raw === 'string') raw = numbersFromText(raw)
  const samples = Array.isArray(raw) ? numbersFromArray(raw) : []

  const declaredUnit = typeof body.unit === 'string' ? body.unit.toLowerCase() : null
  const effectiveUnit = declaredUnit === 'adc' || declaredUnit === 'raw'
    ? 'adc'
    : declaredUnit === 'v' || declaredUnit === 'volts' || declaredUnit === 'voltios'
      ? 'volts'
      : unit

  return {
    samples: toVolts(samples, effectiveUnit),
    bpm: firstNumber(pick(body, BPM_KEYS)),
    sampleRate: firstNumber(pick(body, RATE_KEYS)),
    device: pick(body, DEVICE_KEYS),
  }
}
