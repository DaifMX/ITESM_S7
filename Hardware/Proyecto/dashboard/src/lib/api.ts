import axios from 'axios'

/**
 * Cliente del servidor Express que hace de puente con el ESP8266.
 *
 *   GET /api/samples?since=<cursor>
 *     → { samples: [1.63, 1.71, ...], cursor, bpm, sampleRate, connected }
 *
 * `samples` son voltios (0–3.3). El firmware manda `Serial.println(voltaje)`
 * por el puerto serie —o `broadcastTXT` por WebSocket si ya migraste a WiFi—
 * y el servidor normaliza ambos casos a la misma forma.
 *
 * El `cursor` que devuelve cada respuesta se manda en la siguiente consulta
 * para recibir sólo lo nuevo, sin huecos ni muestras repetidas.
 */

export interface EcgReading {
  /** Muestras en voltios, la más antigua primero. */
  samples: number[]
  /** Posición en el flujo; mándalo como `since` en la siguiente consulta. */
  cursor?: number
  /** Muestras que se perdieron porque el buffer del servidor dio la vuelta. */
  dropped?: number
  bpm?: number | null
  /** Tasa de muestreo medida por el servidor, en Hz. */
  sampleRate?: number | null
  device?: string | null
  /** El servidor sigue recibiendo datos del ESP8266. */
  connected?: boolean
  unit?: string
}

export const api = axios.create({
  baseURL: '/api',
  timeout: 3000,
})

export function setBaseUrl(url: string) {
  api.defaults.baseURL = url
}

export async function fetchSamples(since?: number | null): Promise<EcgReading> {
  const { data } = await api.get<EcgReading>('/samples', {
    params: since != null ? { since } : undefined,
  })
  return data
}
