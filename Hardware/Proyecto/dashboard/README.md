# Dashboard ECG

Interfaz web (React + Vite + Tailwind v4 + shadcn/ui + axios) del monitor ECG.

El dashboard **no habla con el ESP8266**: consulta la API de Express de la
carpeta `server/`, que es quien lee el puerto serie de la placa. La puesta en
marcha completa y el contrato de la API están en el
[README de la raíz](../README.md).

## Desarrollo

Desde la raíz del proyecto, para levantar API y dashboard a la vez:

```sh
pnpm dev
```

O sólo el dashboard, con la API ya corriendo aparte:

```sh
pnpm dev   # dentro de dashboard/
```

Vite redirige `/api` a `http://localhost:3001`. Si la API corre en otra
máquina:

```sh
API_HOST=http://192.168.1.20:3001 pnpm dev
```

Sin hardware, activa el switch **«Señal de prueba»** para ver una señal ECG
sintética.

## Datos que consume

`GET /api/samples?since=<cursor>` devuelve las muestras en **voltios** (0–3.3)
más los metadatos que muestran las tarjetas de estado:

```json
{ "samples": [1.63, 1.71], "cursor": 1540, "bpm": 72, "sampleRate": 100, "connected": true }
```

El `cursor` de cada respuesta se reenvía en la siguiente consulta, así que no
se pierden ni se repiten muestras entre sondeos.

## Estados de conexión

| Insignia | Significado |
| -------- | ----------- |
| Detenido | El polling no está activo. |
| Conectado | Llegan muestras de la placa. |
| Sin señal | La API responde pero el ESP8266 no transmite. |
| Sin servidor | La API no está corriendo. |

## Estructura

- `src/lib/api.ts` — cliente axios y tipos de la lectura ECG.
- `src/hooks/use-ecg-stream.ts` — polling con cursor, buffer circular y modo demo.
- `src/components/ecg-chart.tsx` — trazo ECG sobre `<canvas>` con cuadrícula tipo papel ECG.
- `src/components/ui/` — componentes shadcn/ui.
- `src/App.tsx` — layout del dashboard (estadísticas, controles, gráfica).
