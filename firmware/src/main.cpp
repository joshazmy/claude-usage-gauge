/*
 * Claude Usage Gauge — firmware for the Waveshare ESP32-S3-Touch-LCD-2
 * 2.0" 240x320 IPS, ST7789T3 driver (SPI), ESP32-S3R8.
 *
 * Renders "Version B": a pixel Claude creature whose face escalates with usage,
 * a big SESSION %, and two color-by-fill bars (SESSION 5h / WEEK 7d).
 * Colour means exactly ONE thing — how close you are to your self-set redline:
 *     green < 50%,  amber 50-80%,  red > 80%.   (a vibe gauge, not an official limit)
 *
 * Data path (phase 1): a PC script (../bridge.py) reads your live Claude token
 * usage and sends "session,week\n" (two ints 0-100) over USB serial @115200.
 * If that feed stops, the screen shows an explicit WAITING / NO DATA state — it
 * never silently holds a stale "safe-looking" number.
 *
 * Library: GFX Library for Arduino (moononournation/Arduino_GFX).
 * Pins: see pin_config.h — copy them from Waveshare's official demo at bring-up.
 */
#include <Arduino_GFX_Library.h>
#include "pin_config.h"

Arduino_DataBus *bus   = new Arduino_ESP32SPI(PIN_LCD_DC, PIN_LCD_CS, PIN_LCD_SCK, PIN_LCD_MOSI, PIN_LCD_MISO);
Arduino_GFX     *panel = new Arduino_ST7789(bus, PIN_LCD_RST, 0 /*rotation: portrait*/, true /*IPS*/, LCD_W, LCD_H);
Arduino_GFX     *gfx   = new Arduino_Canvas(LCD_W, LCD_H, panel);   // PSRAM framebuffer => flicker-free

// ---------- palette (RGB565) ----------
#define RGB565(r,g,b) ((uint16_t)((((r)&0xF8)<<8)|(((g)&0xFC)<<3)|((b)>>3)))
const uint16_t C_BG     = RGB565(22,22,22);
const uint16_t C_GREEN  = RGB565(74,222,128);
const uint16_t C_AMBER  = RGB565(245,158,11);
const uint16_t C_RED    = RGB565(239,68,68);
const uint16_t C_EMPTY  = RGB565(44,44,44);
const uint16_t C_ORANGE = RGB565(194,97,61);
const uint16_t C_HILITE = RGB565(224,152,110);
const uint16_t C_EYE    = RGB565(16,15,18);
const uint16_t C_SWEAT  = RGB565(191,227,255);
const uint16_t C_LABEL  = RGB565(138,138,147);
const uint16_t C_DIM    = RGB565(90,90,98);

uint16_t colorFor(int p) { return p < 50 ? C_GREEN : (p < 80 ? C_AMBER : C_RED); }
int faceLevel(int p)     { return p < 50 ? 0 : (p < 80 ? 1 : (p < 95 ? 2 : 3)); }

// ---------- pixel creature (no cream outline; lighter top-rim) ----------
const int ART_ROWS = 13, ART_COLS = 16;
const char *ART[ART_ROWS] = {
  ".OOOOOOOOOOOOOO.", ".OOOOOOOOOOOOOO.", "OOOOOOOOOOOOOOOO", "OOOOOOOOOOOOOOOO",
  ".OOOBBOOOOBBOOO.", ".OOOBBOOOOBBOOO.", ".OOOOOOOOOOOOOO.", ".OOOOOOOOOOOOOO.",
  ".OOOOOOOOOOOOOO.", ".OOOOOOOOOOOOOO.", ".OOOOOOOOOOOOOO.", ".OOO..OOOO..OOO.",
  ".OOO..OOOO..OOO."
};
const int8_t FACE0[][2] = {{4,4},{5,4},{4,5},{5,5},{10,4},{11,4},{10,5},{11,5}};
const int8_t FACE1[][2] = {{3,5},{4,5},{5,5},{10,5},{11,5},{12,5}};
const int8_t FACE2[][2] = {{4,5},{5,5},{10,5},{11,5},{5,3},{4,3},{3,4},{10,3},{11,3},{12,4},{7,9},{8,9}};
const int8_t FACE3[][2] = {{3,3},{5,3},{4,4},{3,5},{5,5},{9,3},{11,3},{10,4},{9,5},{11,5},{6,9},{7,9},{8,9},{9,9}};
const int8_t SWEAT2[][2] = {{13,3},{13,4}};

inline void cell(int c, int r, int ox, int oy, int px, uint16_t col) {
  gfx->fillRect(ox + c * px, oy + r * px, px, px, col);
}
void drawFace(int ox, int oy, int px, int level) {
  const int8_t (*eyes)[2]; int n;
  switch (level) {
    case 0:  eyes = FACE0; n = 8;  break;
    case 1:  eyes = FACE1; n = 6;  break;
    case 2:  eyes = FACE2; n = 12; break;
    default: eyes = FACE3; n = 14; break;
  }
  for (int i = 0; i < n; i++) cell(eyes[i][0], eyes[i][1], ox, oy, px, C_EYE);
  if (level == 2) for (int i = 0; i < 2; i++) cell(SWEAT2[i][0], SWEAT2[i][1], ox, oy, px, C_SWEAT);
}
void drawCreature(int cx, int cy, int px, int level, uint16_t body, uint16_t rim) {
  int ox = cx - (ART_COLS * px) / 2;
  int oy = cy - (ART_ROWS * px) / 2;
  for (int r = 0; r < ART_ROWS; r++)
    for (int c = 0; c < ART_COLS; c++)
      if (ART[r][c] != '.') cell(c, r, ox, oy, px, body);
  for (int c = 0; c < ART_COLS; c++)
    for (int r = 0; r < ART_ROWS; r++)
      if (ART[r][c] != '.') { cell(c, r, ox, oy, px, rim); break; }
  drawFace(ox, oy, px, level);
}
void drawBar(const char *label, int x, int y, int w, int h, int pct, uint16_t col) {
  gfx->setTextSize(1); gfx->setTextColor(C_LABEL);
  gfx->setCursor(x, y - 11); gfx->print(label);
  int r = h / 2;
  gfx->fillRoundRect(x, y, w, h, r, C_EMPTY);
  int fw = (pct * w) / 100; if (fw < h) fw = h;
  gfx->fillRoundRect(x, y, fw, h, r, col);
}
void centerText(const char *s, int y, int size, uint16_t col) {
  gfx->setTextSize(size); gfx->setTextColor(col);
  int tw = (int)strlen(s) * 6 * size;
  gfx->setCursor(120 - tw / 2, y); gfx->print(s);
}

// ---------- state ----------
int sTarget = 0, wTarget = 0, sShown = 0, wShown = 0;
bool haveData = false;
unsigned long lastDataMs = 0;
const unsigned long STALE_MS = 12000;   // bridge sends every 3s; 12s of silence = stale
enum Mode { WAITING, LIVE, STALE };
Mode lastMode = (Mode)-1;
String inbuf;

void drawLive() {
  gfx->fillScreen(C_BG);
  int mx = sShown > wShown ? sShown : wShown;
  drawCreature(120, 80, 6, faceLevel(mx), C_ORANGE, C_HILITE);
  char buf[8]; snprintf(buf, sizeof(buf), "%d%%", sShown);
  centerText(buf, 138, 5, colorFor(sShown));
  drawBar("SESSION 5h", 30, 196, 180, 18, sShown, colorFor(sShown));
  drawBar("WEEK 7d",    30, 248, 180, 18, wShown, colorFor(wShown));
  gfx->flush();
}
void drawStatus(const char *title, const char *hint) {
  gfx->fillScreen(C_BG);
  drawCreature(120, 96, 6, 0, C_DIM, C_DIM);     // dimmed/asleep creature
  centerText(title, 176, 3, C_LABEL);
  centerText(hint, 210, 1, C_DIM);
  gfx->flush();
}

void selfTest() {
  // Full-screen colour bars on boot: if these look right, the SPI bus + pins are correct.
  const uint16_t bars[] = { C_RED, C_GREEN, RGB565(64,128,255), RGB565(255,255,255) };
  for (uint16_t c : bars) { gfx->fillScreen(c); gfx->flush(); delay(350); }
}

int approach(int cur, int tgt) {
  if (cur < tgt) { int n = cur + (tgt - cur + 7) / 8; return n > tgt ? tgt : n; }
  if (cur > tgt) { int n = cur - (cur - tgt + 7) / 8; return n < tgt ? tgt : n; }
  return cur;
}
// Strict: true only if str is non-empty, all digits, and parses to 0..100.
bool parsePct(String str, int &out) {
  str.trim();
  if (str.length() == 0 || str.length() > 3) return false;
  for (unsigned i = 0; i < str.length(); i++) if (!isDigit(str[i])) return false;
  int v = str.toInt();
  if (v < 0 || v > 100) return false;
  out = v;
  return true;
}
void parseLine(const String &s) {
  int comma = s.indexOf(',');
  if (comma < 0) return;
  int a, b;
  // Reject anything non-numeric ("nan,err", garbage). Do NOT refresh freshness on bad
  // data — a corrupt feed must fall through to STALE/NO DATA, never a fake live 0%.
  if (!parsePct(s.substring(0, comma), a) || !parsePct(s.substring(comma + 1), b)) return;
  sTarget = a;
  wTarget = b;
  haveData = true;
  lastDataMs = millis();
}
void readSerial() {
  while (Serial.available()) {
    char ch = (char)Serial.read();
    if (ch == '\n') { parseLine(inbuf); inbuf = ""; }
    else if (ch != '\r' && inbuf.length() < 16) inbuf += ch;
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LCD_BL, OUTPUT);
  digitalWrite(PIN_LCD_BL, HIGH);
  if (!gfx->begin()) Serial.println("gfx->begin() failed — check pins/PSRAM");
  selfTest();
  drawStatus("WAITING", "run bridge.py on your PC");
}

void loop() {
  readSerial();
  unsigned long now = millis();
  Mode mode = !haveData ? WAITING : (now - lastDataMs > STALE_MS ? STALE : LIVE);

  if (mode == LIVE) {
    int ns = approach(sShown, sTarget), nw = approach(wShown, wTarget);
    if (ns != sShown || nw != wShown || lastMode != LIVE) { sShown = ns; wShown = nw; drawLive(); }
  } else if (mode != lastMode) {
    if (mode == WAITING) drawStatus("WAITING", "run bridge.py on your PC");
    else                 drawStatus("NO DATA", "feed lost - check the bridge");
  }
  lastMode = mode;
  delay(33);
}
