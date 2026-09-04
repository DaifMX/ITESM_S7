/*
 * Monitor ECG — transmisión por WiFi con WebSocket (opción alterna)
 *
 * La placa levanta un servidor WebSocket en el puerto 81 y empuja las
 * lecturas. La API de Express se conecta como cliente si arrancas con
 * ESP_HOST apuntando a la IP que imprime este sketch:
 *
 *     ESP_HOST=192.168.1.50 pnpm server
 *
 * Librería: "WebSockets" de Markus Sattler (Links2004), desde el Library Manager.
 *
 * Nota: tener el WiFi activo mete ruido en el ADC del ESP8266. Aquí se
 * promedian varias lecturas por muestra para compensarlo.
 */

#include <ESP8266WiFi.h>
#include <WebSocketsServer.h>

WebSocketsServer webSocket(81);

const int PIN_ANALOGICO = A0;
const int PROMEDIO = 4;           // lecturas promediadas por muestra
const unsigned long PERIODO_MS = 10;  // ~100 Hz

unsigned long ultimaLectura = 0;

void setup() {
  Serial.begin(115200);
  WiFi.begin("TU_SSID", "TU_PASSWORD");
  while (WiFi.status() != WL_CONNECTED) delay(500);
  Serial.println(WiFi.localIP());
  webSocket.begin();
}

void loop() {
  // Sin delay() en el loop: bloquearlo tira las conexiones WebSocket.
  webSocket.loop();

  if (millis() - ultimaLectura >= PERIODO_MS) {
    ultimaLectura = millis();

    long suma = 0;
    for (int i = 0; i < PROMEDIO; i++) suma += analogRead(PIN_ANALOGICO);
    float voltaje = ((suma / (float)PROMEDIO) / 1023.0) * 3.3;

    webSocket.broadcastTXT(String(voltaje, 3));
  }
}
