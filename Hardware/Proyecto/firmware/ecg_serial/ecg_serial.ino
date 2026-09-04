/*
 * Monitor ECG — transmisión por puerto serie (opción en uso)
 *
 * Envía una línea de texto por muestra con el voltaje ya convertido:
 *
 *     1.63
 *     1.71
 *
 * La API de Express (carpeta server/) abre este puerto a 115200 baudios,
 * convierte cada línea en una muestra y se la sirve al dashboard. No hace
 * falta WiFi ni cambiar nada del sketch.
 *
 * Importante: el Monitor Serie y el Serial Plotter del IDE de Arduino toman
 * el puerto en exclusiva. Ciérralos antes de arrancar el servidor.
 */

// Pin analógico del ESP8266
const int PIN_ANALOGICO = A0;

void setup() {
  // Iniciar la comunicación serie a 115200 baudios
  Serial.begin(115200);

  // Opcional: Desactivar WiFi para reducir interferencias eléctricas en la lectura analógica
  // WiFi.mode(WIFI_OFF);
}

void loop() {
  // Leer el valor del pin A0 (Devuelve un valor de 0 a 1023)
  int valorADC = analogRead(PIN_ANALOGICO);

  // Convertir el valor digital a voltaje estimado (0.0 V a 3.3 V)
  float voltaje = (valorADC / 1023.0) * 3.3;

  // Enviar únicamente el valor para graficar en el Serial Plotter
  Serial.println(voltaje);

  // Pausa de 10 ms (frecuencia de muestreo aproximada de 100 Hz)
  delay(10);
}
