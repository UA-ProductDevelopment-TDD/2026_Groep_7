// Bittle wifi camera: firmware for a Seeed XIAO ESP32S3 (Sense), stacked on a Grove Vision AI V2, with an optional
// SRF05 ultrasonic distance sensor.
//
// The XIAO makes the camera reachable for the Bittle Platform, over wifi or over its own USB-C cable:
//   * tcp port 3333 (wifi) or the XIAO's USB serial port: the Grove Vision AI V2's own SSCMA AT protocol (the same JSON
//     lines it speaks over its own USB, with its AI model's boxes and the JPEG of every frame). The XIAO passes the
//     bytes through unchanged over its UART pins (D6 = TX, D7 = RX, 921600 baud). A wifi client goes first; while none
//     is connected the USB port is the bridge.
//     Without a Vision AI V2 on the pins a wifi client gets the XIAO's own Sense camera instead (frames only, no AI).
//   * SRF05: found by itself at start on trigger/echo = MTMS/MTDI (GPIO42/41, the pads on the back) or D2/D1
//     (GPIO3/2); the echo goes through a 1k/2k divider (the SRF05 gives 5 V). Every reading is put between the camera's
//     lines as one extra JSON line: {"type": 1, "name": "DISTANCE", "code": 0, "data": {"cm": 123.4}}
//     ("cm": null when nothing echoes within reach), never inside one of the camera's lines.
//   * http port 80: a small status page, /status (JSON), /frame.jpg (the Sense camera) and a button to forget the wifi.
//   * mDNS name bittle-camera.local.
//
// First start, or after "forget wifi" (or holding BOOT 5 s): the XIAO opens the hotspot "Bittle-Camera".
// Join it with a phone or laptop; the setup page opens (or browse to 192.168.4.1), pick your 2.4 GHz network and type
// its password there. The XIAO keeps it and connects by itself from then on. The USB bridge works meanwhile.
// Libraries: WiFiManager (tzapu).
#include <WiFi.h>
#include <WiFiManager.h>
#include <ESPmDNS.h>
#include <esp_http_server.h>
#include <esp_camera.h>
#include <mbedtls/base64.h>
#include <driver/gpio.h>

static const char *NAME = "bittle-camera";
static const char *HOTSPOT = "Bittle-Camera";
static const char *VERSION = "bittle-camera 1.2";
static const uint16_t BRIDGE_PORT = 3333;
static const uint32_t VISION_BAUD = 921600;
static const int VISION_RX = 44, VISION_TX = 43;  // D7, D6 on the XIAO header
static const int LED = 21;                        // the XIAO's orange user LED, on when low
static const int BOOT_BUTTON = 0;
static const uint32_t FORGET_HOLD_MS = 5000;

// The XIAO ESP32S3 Sense camera connector.
static const int CAM_XCLK = 10, CAM_SIOD = 40, CAM_SIOC = 39, CAM_VSYNC = 38, CAM_HREF = 47, CAM_PCLK = 13;
static const int CAM_D[8] = {15, 17, 18, 16, 14, 12, 11, 48};  // Y2 .. Y9

// SRF05 wirings tried at start: {trigger, echo, name}. The back pads first: nothing else is on them.
struct Wiring { int trigger, echo; const char *name; };
static const Wiring WIRINGS[] = {
  {42, 41, "MTMS/MTDI"}, {41, 42, "MTDI/MTMS"}, {3, 2, "D2/D1"}, {2, 3, "D1/D2"},
};
static const uint32_t PING_MS = 70;          // SRF05: at least 50 ms between pings
static const uint32_t NO_ECHO_US = 25000;    // a longer echo (about 4.3 m) means nothing in reach
static const uint32_t SEARCH_MS = 5000;      // look for a sensor again this often while none is found

HardwareSerial vision(1);
WiFiServer bridge(BRIDGE_PORT);
WiFiClient client;
WiFiManager manager;
httpd_handle_t web = nullptr;

volatile bool visionFound = false;   // a Grove Vision AI V2 answered on the UART pins
volatile bool ownCamera = false;     // the Sense camera started
volatile bool clientConnected = false;
bool online = false;                 // wifi joined and the servers started
bool wifiSaved = false, portalOpen = false;
uint32_t wifiStart = 0;
static const uint32_t WIFI_WAIT_MS = 20000;
String clientAddress;
uint32_t buttonDown = 0;

// The distance sensor.
const Wiring *sonar = nullptr;
volatile uint32_t echoRise = 0, echoWidth = 0;
volatile bool echoDone = false;
uint32_t lastPing = 0, lastSearch = 0;
bool pinging = false;
volatile float distanceCm = -1;      // newest reading; -1: nothing in reach
volatile uint32_t distanceAt = 0;    // millis() of that reading, 0: none yet
bool distancePending = false;        // a reading still to be sent to the platform
bool midLine = false;                // the last byte passed to the platform was not the end of a line

// ---- Grove Vision AI V2 ----

// Ask the board for its name: any answer means it is there.
bool probeVision() {
  vision.write("\rAT+BREAK\r");
  delay(100);
  while (vision.available()) vision.read();
  vision.write("AT+NAME?\r");
  String seen;
  uint32_t start = millis();
  while (millis() - start < 1500) {
    while (vision.available()) {
      char c = vision.read();
      if (seen.length() < 512) seen += c;
    }
    if (seen.indexOf("NAME?") >= 0) return true;
    delay(5);
  }
  return false;
}

// ---- SRF05 ----

void IRAM_ATTR onEcho() {
  uint32_t now = micros();
  if (gpio_get_level((gpio_num_t)sonar->echo)) {
    echoRise = now;
  } else if (echoRise) {
    echoWidth = now - echoRise;
    echoRise = 0;
    echoDone = true;
  }
}

void ping(int trigger) {
  digitalWrite(trigger, HIGH);
  delayMicroseconds(12);
  digitalWrite(trigger, LOW);
}

// Does a sensor answer on this wiring? It answers every ping with an echo pulse (up to 30 ms when nothing is in
// reach). One unanswered ping ends the try quickly, so a search between camera frames stays short.
bool answers(const Wiring &wiring) {
  pinMode(wiring.echo, INPUT_PULLDOWN);  // an unwired pin must not look like an echo
  pinMode(wiring.trigger, OUTPUT);
  digitalWrite(wiring.trigger, LOW);
  delayMicroseconds(50);
  int heard = 0;
  for (int i = 0; i < 3; i++) {
    ping(wiring.trigger);
    if (pulseIn(wiring.echo, HIGH, 40000) > 50) heard++;
    else if (heard == 0) break;
    delay(PING_MS - 30);
  }
  pinMode(wiring.trigger, INPUT);
  return heard >= 2;
}

void useSonar(const Wiring &wiring) {
  sonar = &wiring;
  pinMode(sonar->echo, INPUT_PULLDOWN);
  pinMode(sonar->trigger, OUTPUT);
  digitalWrite(sonar->trigger, LOW);
  attachInterrupt(sonar->echo, onEcho, CHANGE);
}

// all: try every wiring (at start); otherwise the next one only (between camera frames).
void findSonar(bool all) {
  static size_t next = 0;
  lastSearch = millis();
  size_t count = sizeof(WIRINGS) / sizeof(WIRINGS[0]);
  for (size_t tried = 0; tried < (all ? count : 1); tried++) {
    const Wiring &wiring = WIRINGS[next];
    next = (next + 1) % count;
    if (answers(wiring)) {
      useSonar(wiring);
      return;
    }
  }
}

// Non-blocking: ping every PING_MS, the echo is timed by the interrupt.
void measure() {
  uint32_t now = millis();
  if (!sonar) {
    if (now - lastSearch > SEARCH_MS / 4) findSonar(false);
    return;
  }
  if (echoDone) {
    echoDone = false;
    pinging = false;
    uint32_t width = echoWidth;
    distanceCm = width >= NO_ECHO_US ? -1 : width / 58.0f;
    distanceAt = now;
    distancePending = true;
  }
  if (now - lastPing >= PING_MS) {
    if (pinging) {  // no echo pulse at all: the sensor is gone
      distanceCm = -1;
      distanceAt = now;
      distancePending = true;
    }
    lastPing = now;
    echoRise = 0;
    pinging = true;
    ping(sonar->trigger);
  }
}

String distanceLine() {
  String cm = distanceCm < 0 ? String("null") : String(distanceCm, 1);
  return "{\"type\": 1, \"name\": \"DISTANCE\", \"code\": 0, \"data\": {\"cm\": " + cm + ", \"sensor\": \"srf05\"}}\r\n";
}

// ---- Passing the camera's bytes to the platform (wifi client or USB) ----

// Send the camera's bytes; a waiting distance line goes in right after the end of a line, never inside one.
void forward(Stream &host, const uint8_t *data, int n) {
  if (distancePending && !midLine) {
    host.print(distanceLine());
    distancePending = false;
  }
  if (distancePending) {
    const uint8_t *end = (const uint8_t *)memchr(data, '\n', n);
    if (end) {
      int first = end - data + 1;
      host.write(data, first);
      host.print(distanceLine());
      distancePending = false;
      data += first;
      n -= first;
    }
  }
  if (n > 0) {
    host.write(data, n);
    midLine = data[n - 1] != '\n';
  }
}

void pump(Stream &host, bool hostReady) {
  static uint8_t fromVision[4096], fromHost[512];
  int n = vision.available();
  if (n > 0) {
    n = vision.read(fromVision, min(n, (int)sizeof(fromVision)));
    if (hostReady) forward(host, fromVision, n);
  } else if (hostReady && distancePending && !midLine) {
    host.print(distanceLine());
    distancePending = false;
  }
  int m = host.available();
  if (m > 0) {
    m = host.readBytes(fromHost, min(m, (int)sizeof(fromHost)));
    vision.write(fromHost, m);
  }
  if (!hostReady) distancePending = false;
}

// ---- The XIAO's own Sense camera (wifi client, no Vision AI V2) ----

bool startOwnCamera() {
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = CAM_D[0]; config.pin_d1 = CAM_D[1]; config.pin_d2 = CAM_D[2]; config.pin_d3 = CAM_D[3];
  config.pin_d4 = CAM_D[4]; config.pin_d5 = CAM_D[5]; config.pin_d6 = CAM_D[6]; config.pin_d7 = CAM_D[7];
  config.pin_xclk = CAM_XCLK;
  config.pin_pclk = CAM_PCLK;
  config.pin_vsync = CAM_VSYNC;
  config.pin_href = CAM_HREF;
  config.pin_sccb_sda = CAM_SIOD;
  config.pin_sccb_scl = CAM_SIOC;
  config.pin_pwdn = -1;
  config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_240X240;
  config.jpeg_quality = 12;
  config.fb_count = psramFound() ? 2 : 1;
  config.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;
  bool ok = esp_camera_init(&config) == ESP_OK;
  if (!ok) esp_camera_deinit();
  return ok;
}

// The platform's image sizes (AT+SENSOR option 0, 1, 2) for the Sense camera.
framesize_t frameSizeFor(int option) {
  if (option == 1) return FRAMESIZE_HVGA;  // 480 x 320
  if (option == 2) return FRAMESIZE_VGA;   // 640 x 480
  return FRAMESIZE_240X240;
}

void reply(WiFiClient &to, const String &name, int code, const String &data) {
  to.print("{\"type\": 0, \"name\": \"" + name + "\", \"code\": " + String(code) + ", \"data\": " + data + "}\r\n");
}

// One frame as an SSCMA SAMPLE event, the JPEG base64 encoded piece by piece.
bool sendFrame(WiFiClient &to, uint32_t count) {
  camera_fb_t *frame = esp_camera_fb_get();
  if (!frame) return false;
  to.print("{\"type\": 1, \"name\": \"SAMPLE\", \"code\": 0, \"data\": {\"count\": " + String(count) +
           ", \"resolution\": [" + String(frame->width) + ", " + String(frame->height) + "], \"image\": \"");
  static unsigned char encoded[4100];
  for (size_t at = 0; at < frame->len && to.connected(); at += 3072) {
    size_t take = min((size_t)3072, frame->len - at), written = 0;
    mbedtls_base64_encode(encoded, sizeof(encoded), &written, frame->buf + at, take);
    to.write(encoded, written);
  }
  to.print("\"}}\r\n");
  esp_camera_fb_return(frame);
  return true;
}

// Answer the AT commands the platform uses, with the Sense camera instead of a Vision AI V2.
void runOwnCamera(WiFiClient &to) {
  String line;
  bool streaming = false;
  uint32_t count = 0;
  while (to.connected()) {
    while (to.available()) {
      char c = to.read();
      if (c != '\r' && c != '\n') {
        if (line.length() < 128) line += c;
        continue;
      }
      line.trim();
      if (!line.startsWith("AT+")) {
        line = "";
        continue;
      }
      String command = line.substring(3);
      String name = command.substring(0, command.indexOf('=') < 0 ? command.length() : command.indexOf('='));
      line = "";
      if (name == "BREAK") {
        streaming = false;
        reply(to, name, 0, "{}");
      } else if (name == "NAME?") {
        reply(to, name, 0, "\"XIAO ESP32S3 Sense camera\"");
      } else if (name == "VER?") {
        reply(to, name, 0, String("{\"software\": \"") + VERSION + "\", \"hardware\": \"xiao-esp32s3\"}");
      } else if (name == "INFO?") {
        reply(to, name, 0, "{\"crc16_maxim\": 0, \"info\": \"\"}");  // no AI model on the XIAO
      } else if (name == "SENSOR") {
        int option = command.substring(command.lastIndexOf(',') + 1).toInt();
        sensor_t *sensor = ownCamera ? esp_camera_sensor_get() : nullptr;
        bool ok = sensor && sensor->set_framesize(sensor, frameSizeFor(option)) == 0;
        reply(to, name, ok ? 0 : 4, "{}");
      } else if (name == "SAMPLE") {
        streaming = ownCamera;
        reply(to, name, ownCamera ? 0 : 4, "{}");
      } else {
        reply(to, name, 3, "{}");  // not supported here (AT+INVOKE needs the Vision AI V2)
      }
    }
    measure();
    if (distancePending) {
      to.print(distanceLine());
      distancePending = false;
    }
    if (streaming) {
      if (!sendFrame(to, count++)) delay(20);
    } else {
      delay(5);
    }
    checkButton();
  }
}

// ---- Web page ----

String statusJson() {
  String mode = visionFound ? "vision-ai" : ownCamera ? "xiao-camera" : "none";
  String cm = distanceCm < 0 ? String("null") : String(distanceCm, 1);
  return "{\"name\": \"" + String(NAME) + "\", \"version\": \"" + VERSION + "\", \"mode\": \"" + mode +
         "\", \"ip\": \"" + WiFi.localIP().toString() + "\", \"ssid\": \"" + WiFi.SSID() +
         "\", \"rssi\": " + String(WiFi.RSSI()) + ", \"bridge_port\": " + String(BRIDGE_PORT) +
         ", \"client\": " + (clientConnected ? "\"" + clientAddress + "\"" : String("null")) +
         ", \"distance_sensor\": " + (sonar ? "\"" + String(sonar->name) + "\"" : String("null")) +
         ", \"distance_cm\": " + cm + "}";
}

esp_err_t handleStatus(httpd_req_t *req) {
  String body = statusJson();
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, body.c_str(), body.length());
}

esp_err_t handleIndex(httpd_req_t *req) {
  String mode = visionFound ? "Grove Vision AI V2 gevonden (beeld + AI)" : ownCamera ? "Eigen camera van de XIAO (beeld, geen AI)" : "Geen camera gevonden";
  String distance = !sonar ? String("geen SRF05 gevonden")
                  : "SRF05 op " + String(sonar->name) + ": " + (distanceCm < 0 ? String("niets binnen bereik") : String(distanceCm, 1) + " cm");
  String page =
    "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>Bittle camera</title>"
    "<meta http-equiv=refresh content=2>"
    "<style>body{font:16px system-ui;margin:24px;max-width:560px}td{padding:4px 12px 4px 0}button{font:inherit;padding:6px 12px}</style>"
    "<h1>Bittle camera</h1><table>"
    "<tr><td>Camera<td>" + mode +
    "<tr><td>Afstand<td>" + distance +
    "<tr><td>Wifi<td>" + WiFi.SSID() + " (" + String(WiFi.RSSI()) + " dBm)"
    "<tr><td>Adres<td>" + WiFi.localIP().toString() + " &middot; " + NAME + ".local"
    "<tr><td>Platform<td>" + (clientConnected ? "verbonden vanaf " + clientAddress : String("niet verbonden via wifi")) +
    "<tr><td>Versie<td>" + VERSION + "</table>"
    "<p>Kies in het Bittle Platform bij de camera <b>Wifi-camera</b> met adres <b>" + NAME + ".local</b> (of " +
    WiFi.localIP().toString() + ").</p>" + (ownCamera ? "<p><img src=/frame.jpg style='max-width:100%'></p>" : "") +
    "<form method=post action=/forget onsubmit=\"return confirm('Wifi vergeten? De camera opent daarna weer de hotspot Bittle-Camera.')\">"
    "<button>Wifi vergeten</button></form>";
  httpd_resp_set_type(req, "text/html; charset=utf-8");
  return httpd_resp_send(req, page.c_str(), page.length());
}

esp_err_t handleFrame(httpd_req_t *req) {
  camera_fb_t *frame = ownCamera ? esp_camera_fb_get() : nullptr;
  if (!frame) {
    httpd_resp_send_err(req, HTTPD_404_NOT_FOUND, "Geen eigen camera");
    return ESP_FAIL;
  }
  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  esp_err_t result = httpd_resp_send(req, (const char *)frame->buf, frame->len);
  esp_camera_fb_return(frame);
  return result;
}

void forgetWifi() {
  manager.resetSettings();
  delay(200);
  ESP.restart();
}

esp_err_t handleForget(httpd_req_t *req) {
  const char *page = "<!doctype html><meta charset=utf-8><p>Wifi vergeten. Verbind met de hotspot <b>Bittle-Camera</b> om een netwerk te kiezen.</p>";
  httpd_resp_set_type(req, "text/html; charset=utf-8");
  httpd_resp_send(req, page, strlen(page));
  delay(500);
  forgetWifi();
  return ESP_OK;
}

void startWeb() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  if (httpd_start(&web, &config) != ESP_OK) return;
  httpd_uri_t pages[] = {
    {"/", HTTP_GET, handleIndex, nullptr},
    {"/status", HTTP_GET, handleStatus, nullptr},
    {"/frame.jpg", HTTP_GET, handleFrame, nullptr},
    {"/forget", HTTP_POST, handleForget, nullptr},
  };
  for (auto &page : pages) httpd_register_uri_handler(web, &page);
}

// Once the wifi is joined: the setup page closes and the camera's own servers start.
void goOnline() {
  if (portalOpen) manager.stopConfigPortal();
  portalOpen = false;
  WiFi.mode(WIFI_STA);  // the setup hotspot goes off
  WiFi.setSleep(false);  // full speed for the picture stream
  WiFi.setAutoReconnect(true);
  MDNS.begin(NAME);
  MDNS.addService("http", "tcp", 80);
  MDNS.addService("bittle-cam", "tcp", BRIDGE_PORT);
  startWeb();
  bridge.begin();
  bridge.setNoDelay(true);
  online = true;
}

// Holding BOOT for 5 s forgets the wifi network (for when it moves to another place).
void checkButton() {
  if (digitalRead(BOOT_BUTTON) == LOW) {
    if (!buttonDown) buttonDown = millis();
    if (millis() - buttonDown > FORGET_HOLD_MS) forgetWifi();
  } else {
    buttonDown = 0;
  }
}

// ---- Start and main loop ----

void setup() {
  Serial.setTxTimeoutMs(0);  // never wait for a USB host that is not reading
  Serial.begin(921600);
  pinMode(LED, OUTPUT);
  digitalWrite(LED, HIGH);
  pinMode(BOOT_BUTTON, INPUT_PULLUP);

  vision.setRxBufferSize(65536);
  vision.begin(VISION_BAUD, SERIAL_8N1, VISION_RX, VISION_TX);
  delay(1500);  // the Vision AI V2 boots with the XIAO when they share power
  visionFound = probeVision();
  ownCamera = !visionFound && startOwnCamera();
  findSonar(true);
  Serial.printf("Vision AI V2: %s, eigen camera: %s, SRF05: %s\r\n", visionFound ? "ja" : "nee",
                ownCamera ? "ja" : "nee", sonar ? sonar->name : "niet gevonden");

  // Wifi starts in the background: the USB bridge works from the first second, with or without a network.
  WiFi.mode(WIFI_STA);
  WiFi.setHostname(NAME);
  manager.setDebugOutput(false);  // the USB port carries the camera's data
  manager.setHostname(NAME);
  manager.setConfigPortalBlocking(false);
  manager.setConfigPortalTimeout(300);
  manager.setTitle("Bittle camera");
  wifiSaved = manager.getWiFiIsSaved();
  if (wifiSaved) WiFi.begin();  // the network saved by the setup page
  wifiStart = millis();
}

// Not online yet: wait for the saved network; without one (or after 20 s) open the setup hotspot meanwhile.
void keepTryingWifi() {
  if (WiFi.isConnected()) {
    goOnline();
    return;
  }
  if (!portalOpen && (!wifiSaved || millis() - wifiStart > WIFI_WAIT_MS)) {
    manager.startConfigPortal(HOTSPOT);
    portalOpen = true;
  }
  if (!portalOpen) return;
  manager.process();
  if (!manager.getConfigPortalActive()) {  // 5 minutes without anyone on the setup page: try the network again
    portalOpen = false;
    wifiSaved = manager.getWiFiIsSaved();
    WiFi.mode(WIFI_STA);
    if (wifiSaved) WiFi.begin();
    wifiStart = millis();
  }
}

void loop() {
  checkButton();
  measure();
  if (!online) keepTryingWifi();
  digitalWrite(LED, WiFi.isConnected() ? LOW : HIGH);

  if (online && !clientConnected) {
    WiFiClient fresh = bridge.accept();
    if (fresh) {
      client = fresh;
      client.setNoDelay(true);
      clientAddress = client.remoteIP().toString();
      clientConnected = true;
      midLine = false;
      visionFound = probeVision();  // ask again: the board may have started later, or been taken off
      if (!visionFound) {
        if (!ownCamera) ownCamera = startOwnCamera();
        runOwnCamera(client);
        client.stop();
        clientConnected = false;
      }
    }
  }
  if (clientConnected && !client.connected()) {
    vision.write("\rAT+BREAK\r");  // stop the stream the wifi client started
    client.stop();
    clientConnected = false;
    midLine = false;
  }

  if (clientConnected) {
    pump(client, true);
  } else {
    pump(Serial, (bool)Serial);
  }
  if (!vision.available()) delay(1);
}
