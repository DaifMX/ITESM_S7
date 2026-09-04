/**
 * Estimación de frecuencia cardíaca por detección de picos R.
 *
 * Umbral adaptativo sobre la ventana reciente (no un valor fijo) para que
 * funcione con cualquier ganancia y con la componente de continua del
 * AD8232, más un periodo refractario que evita contar dos veces el mismo
 * complejo QRS. Suficiente para un dashboard; no es Pan-Tompkins.
 */

/** Amplitud mínima pico a pico, en voltios, para considerar que hay señal. */
const MIN_AMPLITUDE_V = 0.05
const MIN_BPM = 25
const MAX_BPM = 250

/**
 * @param {number[]} samples  muestras en voltios, más antigua primero
 * @param {number|null} sampleRate  Hz
 * @returns {number|null}
 */
export function estimateBpm(samples, sampleRate) {
  if (!sampleRate || sampleRate <= 0) return null
  // Necesitamos al menos un par de latidos para medir un intervalo.
  if (samples.length < sampleRate * 2) return null

  let min = Infinity
  let max = -Infinity
  for (const v of samples) {
    if (v < min) min = v
    if (v > max) max = v
  }
  const amplitude = max - min
  if (amplitude < MIN_AMPLITUDE_V) return null

  const threshold = min + amplitude * 0.65
  const refractory = Math.max(1, Math.round(sampleRate * 0.25)) // 240 bpm tope físico

  /** @type {number[]} */
  const peaks = []
  let i = 0
  while (i < samples.length) {
    if (samples[i] < threshold) {
      i++
      continue
    }
    // Recorremos la meseta por encima del umbral y nos quedamos con el máximo.
    let j = i
    let peak = i
    while (j < samples.length && samples[j] >= threshold) {
      if (samples[j] > samples[peak]) peak = j
      j++
    }
    peaks.push(peak)
    i = Math.max(j, peak + refractory)
  }

  if (peaks.length < 2) return null

  const intervals = []
  for (let k = 1; k < peaks.length; k++) intervals.push(peaks[k] - peaks[k - 1])
  // Mediana: un latido mal detectado no arrastra el resultado.
  intervals.sort((a, b) => a - b)
  const median = intervals[Math.floor(intervals.length / 2)]
  if (!median) return null

  const bpm = Math.round((60 * sampleRate) / median)
  return bpm >= MIN_BPM && bpm <= MAX_BPM ? bpm : null
}
