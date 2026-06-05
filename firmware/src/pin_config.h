#pragma once
/* =====================================================================
 *  PIN MAP — Waveshare ESP32-S3-Touch-LCD-2 (ST7789T3, 4-wire SPI)
 *
 *  ⚠ DO NOT TRUST THESE NUMBERS YET. Online sources disagree on the exact
 *  GPIOs for this board (Reddit, AI reviews, and the sibling 2.8" board all
 *  list DIFFERENT pins), and several people got a black screen using
 *  "community" values. The ONLY authority is the pin_config.h shipped in
 *  Waveshare's OFFICIAL Arduino demo for THIS exact board:
 *      waveshare.com/wiki/ESP32-S3-Touch-LCD-2  ->  Arduino  ->  demo .zip
 *
 *  Bring-up procedure:
 *    1. Copy the LCD pin numbers from that demo's pin_config.h into here.
 *    2. Flash. The boot SELF-TEST (full-screen R/G/B/W bars) runs first.
 *    3. See clean colour bars -> bus + pins are right; gauge UI follows.
 *       Black/garbled screen -> pins are wrong; fix and re-flash.
 *
 *  (Values below are the best-documented guess from the sibling 2.8" board,
 *   marked so they are obviously provisional — replace before relying on it.)
 * ===================================================================== */
#define PIN_LCD_DC    41   // TODO: set from vendor pin_config.h
#define PIN_LCD_CS    42   // TODO
#define PIN_LCD_SCK   40   // TODO
#define PIN_LCD_MOSI  45   // TODO
#define PIN_LCD_MISO  -1   // display-only SPI; MISO unused
#define PIN_LCD_RST   39   // TODO
#define PIN_LCD_BL     5   // backlight; TODO (GPIO2 on some variants)

#define LCD_W 240
#define LCD_H 320

// FAIL-CLOSED: this build will NOT compile until you copy the verified pins from
// Waveshare's official demo above and uncomment the next line. This makes it
// impossible to flash a black-screen build with unconfirmed pins.
// #define PINS_VERIFIED
#ifndef PINS_VERIFIED
#error "claude-usage-gauge: copy the real LCD pins into pin_config.h from Waveshare's official ESP32-S3-Touch-LCD-2 Arduino demo, then uncomment '#define PINS_VERIFIED'."
#endif
