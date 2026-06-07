# Claude Usage Gauge

A 2" ESP32-S3 desk gauge (240×320) that shows live Claude Code usage as pixel art
and flashes when a session needs you or finishes. A PC script reads
`~/.claude/projects/**/*.jsonl` token usage and Claude Code hooks
(`hook.py`) write attention events; the device (or the 1:1 browser simulator
`preview.html`) draws them.

## Design System

**Always read `DESIGN.md` before making any visual or UI change.** Colors, the
"color = closeness" law, the face/beacon system, typography, layout, and motion are
defined there. Do not deviate without explicit user approval. In QA or review, flag
any code that doesn't match DESIGN.md.

The firmware (`firmware/src/main.cpp`) and the browser simulator (`preview.html`)
must stay **pixel-identical** — DESIGN.md governs both. The offline PIL renderers
(`_diagnose.py`, `_diagnose_flash.py`) mirror the same draw math for screenshots.

## Layout

| File | What it is |
|------|------------|
| `usage.py` | Reads `~/.claude` logs, sums tokens, reads the attention beacon file (stdlib only) |
| `server.py` | Local web server for the browser simulator (port 8780) |
| `preview.html` | 1:1 `<canvas>` simulator of the 240×320 device |
| `hook.py` | Claude Code hooks → `~/.claude/gauge-alert.json` (the attention beacon) |
| `bridge.py` | PC → board serial bridge |
| `firmware/` | PlatformIO project for the ESP32-S3 |
