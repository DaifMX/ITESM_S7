# Monitor ECG — ESP8266

Cadena completa: **puerto serie → API de Express → dashboard React**.

```
ESP8266 (A0)                servidor Express                dashboard React
Serial.println(voltaje)  →  lee el puerto serie,        →   GET /api/samples
115200 baudios, ~100 Hz     acumula y calcula BPM           cada 200 ms
```

El ESP8266 no habla HTTP: sólo escribe texto por el cable USB. La API es la
que abre el puerto, convierte cada línea en una muestra y la expone por HTTP,
que es lo que el navegador sí puede consumir.

## Arranque

```sh
pnpm install                 # dependencias de la raíz
pnpm --dir server install    # API
pnpm --dir dashboard install # dashboard
pnpm dev                     # levanta API (:3001) y dashboard (:5173)
```

Abre <http://localhost:5173> y pulsa **Iniciar**.

También puedes correrlos por separado con `pnpm server` y `pnpm dashboard`.

**Cierra el Monitor Serie y el Serial Plotter del IDE de Arduino** antes de
arrancar: toman el puerto en exclusiva y la API no podrá abrirlo (lo verás en
el log como «puerto ocupado»).

Para producción, `pnpm start` compila el dashboard y lo sirve desde el propio
Express en <http://localhost:3001>, con datos y UI en un mismo origen.

## Firmware

- `firmware/ecg_serial/` — el sketch en uso: `Serial.println(voltaje)` a 100 Hz.
- `firmware/ecg_websocket/` — variante WiFi con `WebSocketsServer` en el puerto 81.

Para la variante WiFi, arranca la API con la IP que imprime la placa:

```sh
ESP_HOST=192.168.1.50 pnpm server
```

## API

| Método | Ruta                        | Para qué |
| ------ | --------------------------- | -------- |
| `GET`  | `/api/samples?since=<cur>`  | Lectura del dashboard. Sin `since` devuelve lo acumulado desde la consulta anterior. |
| `POST` | `/api/samples`              | Ingesta por HTTP. Acepta JSON, texto plano/CSV o uint16 little-endian. |
| `GET`  | `/api/ingest?values=1.6,1.7`| Ingesta para firmware que sólo sabe hacer GET. |
| `GET`  | `/api/health`               | Estado del servidor y de cada origen de datos. |
| `POST` | `/api/reset`                | Vacía el buffer. |

Respuesta de `/api/samples`:

```json
{
  "samples": [1.63, 1.71, 1.58],
  "cursor": 1540,
  "dropped": 0,
  "bpm": 72,
  "sampleRate": 100,
  "device": "serial:/dev/tty.usbserial-140",
  "connected": true,
  "unit": "V"
}
```

`cursor` es la posición en el flujo: el dashboard la reenvía como `since` en la
siguiente consulta y así recibe sólo lo nuevo, sin huecos ni repeticiones.
`dropped` avisa si el buffer del servidor dio la vuelta antes de que el cliente
alcanzara a leer.

### Formatos que acepta la ingesta

Todos acaban normalizados a voltios, así que el dashboard no cambia:

| Entrada | Ejemplo |
| ------- | ------- |
| Una muestra por línea | `1.63\n1.71` |
| CSV | `1.63,1.71,1.58` |
| Array JSON | `[1.63, 1.71]` |
| Objeto JSON | `{"samples":[1.63],"bpm":72}` |
| Cuentas del ADC | `512` → 1.65 V (todo lo que pase de 3.6 se toma como cuenta) |
| Unidad explícita | `{"samples":[512],"unit":"adc"}` |
| Binario | uint16 little-endian |

## Variables de entorno del servidor

| Variable | Por defecto | Para qué |
| -------- | ----------- | -------- |
| `PORT` | `3001` | Puerto de la API. |
| `SERIAL_PATH` | autodetectado | Puerto serie, p. ej. `/dev/tty.usbserial-140`. |
| `SERIAL_BAUD` | `115200` | Debe coincidir con el `Serial.begin()` del sketch. |
| `SERIAL` | `on` | `off` desactiva la lectura del puerto serie. |
| `SERIAL_RESET` | `off` | `on` reinicia la placa al conectar. |
| `ESP_HOST` | — | IP del ESP8266 para la variante WebSocket. |
| `ESP_WS_PORT` | `81` | Puerto del WebSocket de la placa. |
| `INPUT_UNIT` | `auto` | `volts` o `adc` para forzar la interpretación. |
| `BUFFER_SIZE` | `60000` | Muestras guardadas (~10 min a 100 Hz). |

La autodetección busca los conversores USB que montan estas placas: CP210x
(`10c4`), CH340 (`1a86`), FTDI (`0403`) y USB nativo de Espressif (`303a`).

## Estructura

- `server/src/index.js` — app de Express y rutas.
- `server/src/serial-link.js` — lectura del puerto serie con reconexión.
- `server/src/esp-link.js` — cliente WebSocket para la variante WiFi.
- `server/src/parse.js` — normaliza cualquier formato de entrada a voltios.
- `server/src/store.js` — buffer circular con cursor y estimación de la tasa de muestreo.
- `server/src/bpm.js` — detección de picos R con umbral adaptativo.
- `dashboard/src/lib/api.ts` — cliente axios y tipos.
- `dashboard/src/hooks/use-ecg-stream.ts` — polling, buffer y modo demo.
- `dashboard/src/components/ecg-chart.tsx` — trazo sobre `<canvas>`.

## Diagnóstico

| Síntoma | Causa habitual |
| ------- | -------------- |
| «Sin servidor» | La API no está corriendo: `pnpm server`. |
| «Sin señal» | La API responde pero la placa no transmite. Revisa que el Monitor Serie esté cerrado y que el sketch esté cargado. |
| Puerto ocupado en el log | El IDE de Arduino tiene el puerto tomado. |
| `sampleRate` muy por debajo de 100 Hz | El `delay(10)` del sketch más el tiempo de `Serial.println` no llegan a 100 Hz reales; es normal que baje a ~85 Hz. |
| Traza plana | Sin electrodos conectados A0 queda flotando. Activa «Señal de prueba» para descartar el software. |

Comprueba qué está llegando sin abrir el navegador:

```sh
curl -s localhost:3001/api/health | python3 -m json.tool
```
