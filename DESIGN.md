# Design System — Claude Usage Gauge

> The source of truth for every visual decision in this project. It governs **both**
> the ESP32 firmware (`firmware/src/main.cpp`) and the 1:1 browser simulator
> (`preview.html`) — they must stay pixel-identical. Read this before changing
> anything you can see.

## North Star

A calm object on the desk that, at a glance, answers three things — **in this order**:

1. **Does Claude need me?** (the attention beacon)
2. **How close am I to my usage limit?** (the gauge)
3. **...and it looks good doing it.** (the aesthetic)

Every decision serves these three jobs, in that priority. When they conflict, the
higher-numbered one yields. Job 1 outranks job 2 outranks job 3.

## Governing Constraint — the 2" panel

This ships on a **Waveshare ESP32-S3-Touch-LCD-2: a 2.0" 240×320 IPS panel**, read
from arm's length on a desk and recognized from across a room. That is the whole
design problem. So:

- **Every pixel earns its place.** The screen budget is full. Adding an element
  means removing one — never just cramming more in.
- **Glanceable beats complete.** You read it in under a second without focusing.
  Information you have to study does not belong here.
- **Legible at two distances:** the exact number at arm's length, the *state*
  (color + face + flash) from across the room.

## The Four Laws

1. **Color means exactly ONE thing: closeness to your redline.**
   🟢 `< 50%` · 🟠 `50–80%` · 🔴 `> 80%`. No rainbow, no gradients, no second
   meaning. The whole fill is one flat color. The attention beacon is the *single,
   deliberate exception* (see below) and is disambiguated by form, motion, and a
   text label precisely because color is otherwise sacred.

2. **Attention pre-empts.** Job 1 wins. When Claude needs you, the beacon takes the
   whole screen — the gauge dims to a scrim so there is one unambiguous thing to
   look at. When nothing needs you, the usage gauge is the resting state. Absence
   of a beacon means "nothing needed" — that is information, so it is never faked.

3. **The face is the glance.** You read the creature's expression
   (calm → focused → worried → dead-eyed) before any number. The face is the
   low-resolution channel that survives across-the-room distance; the % is the
   high-resolution channel for arm's length.

4. **Data honesty.** Track Claude's real limit *types* — a rolling **5-hour session**
   and a rolling **7-day week** — never an invented "hourly" number. The redlines are
   the user's personal estimates (a "vibe gauge"); the device never claims to know
   Anthropic's unpublished limits. It never holds stale data behind a safe-looking
   number — a dropped feed shows an explicit **WAITING / NO DATA** state.

5. **No slop.** No gradients, no decorative blobs, no rainbow fills, no ornament. The
   pixel creature + two fill bars + one-meaning color do all the work. If a region
   feels empty, it needs better information, not decoration.

## Typography

- **Primary: monospace** — Consolas Bold on the web simulator
  (`Consolas, "Courier New", monospace`), a bitmap mono on the device.
- This is a **deliberate retro-utility choice**, not a fallback. A pixel desk gauge
  is a piece of instrumentation; monospaced digits read as a readout, and fixed-width
  numerals keep the big % from reflowing as it changes.
- **Roles:** big session % (38px), bar labels (11px, uppercase, `#8A8A93`), beacon
  banner (12px bold). There is no body copy — this is a readout, not a document.

## Color

The palette is tiny on purpose. Every token below is the *whole* system.

| Token | Hex | Role |
|-------|-----|------|
| Screen | `#161616` | panel background, the resting field |
| Green | `#4ADE80` | closeness `< 50%` (and the "done" beacon) |
| Amber | `#F59E0B` | closeness `50–80%` (and the "needs you" beacon) |
| Red | `#EF4444` | closeness `> 80%` |
| Empty track | `#2C2C2C` | unfilled portion of a bar |
| Creature body | `#C2613D` | the pixel creature |
| Creature rim | `#E0986E` | top-edge highlight (the only "lighting") |
| Eyes | `#100F12` | face features |
| Sweat | `#BFE3FF` | the "worried" face accent |

- **Approach: restrained.** Color is rare and always means closeness. The creature's
  orange is identity, not status.
- **No dark/light theme.** The device is always the dark panel. There is no light mode.

## The Creature (the face system)

A 16×13 pixel creature, solid `#C2613D` with a one-row `#E0986E` top rim (no outline).
Its face escalates on the **worse** of session/week %:

| Level | Trigger | Expression |
|-------|---------|-----------|
| 0 calm | `< 50%` | neutral eyes |
| 1 focused | `50–80%` | narrowed eyes |
| 2 worried | `80–95%` | raised brows + a sweat drop |
| 3 dead | `≥ 95%` | x_x eyes |

The face is the across-the-room signal. It must remain readable at the size it
ships (6px per cell) — never shrink it to make room for more data.

## Layout (fixed device coordinates)

Not a fluid grid — a fixed 240×320 composition. Top to bottom:

- **Creature** centered at ~(120, 80), 6px cells.
- **Big session %** centered at y≈166, 38px, colored by closeness.
- **SESSION · 5h** bar at y=202, **WEEK · 7d** bar at y=254 — 180px wide, 18px tall,
  fully rounded pills, color = closeness, empty track `#2C2C2C`.

**Screen budget (hard rule):** the resting screen shows at most — face, session %,
two labeled bars. That is the full budget. Touch is capacitive and reserved for a
future phase; nothing taps today.

## The Attention Beacon (primary mode — job #1)

Fires from Claude Code hooks (`hook.py`) via `~/.claude/gauge-alert.json`. Two states:

- **Amber "NEEDS YOU"** — Claude is blocked on you (a permission prompt, or input idle).
- **Green "DONE"** — a long turn (≥30s) you walked away from has finished.

**Rendering (this is the disambiguation that lets it reuse the closeness colors):**

- **Scrim:** the gauge dims to ~55% so it recedes and the alert owns the screen.
  One thing to glance at, and the dimmed gauge's own green/amber can't clash with
  the beacon's.
- **Pulsing inset frame** (12px, ~0.6 Hz) in the beacon color.
- **Banner pill** with the label (`NEEDS YOU` / `DONE`) + the project name, the name
  truncated with an ellipsis so it never overflows the pill. The label is the
  non-color carrier of meaning and always stays whole.

**Anti-noise (part of the design, not just the code):** "done" only fires for turns
long enough that you'd have walked away; any beacon clears the instant you return
(submit a prompt); a missed clear expires after 5 minutes. A beacon that cried wolf
would destroy the calm-gauge value, so the bar to flash is deliberately high.

## Motion

Minimal-functional only. No motion exists for decoration.

- Bars **ease** toward their target (~⅛ of the remaining distance per frame).
- The beacon frame **pulses** ~0.6 Hz (alpha 0.45→1.0).
- The face changes **instantly** — it is a state readout, not an animation.

## Known Limitations

- **Colorblind glance distance.** Amber-vs-green is the red/green-deficient confusable
  pair, and at across-the-room distance the beacon is color-only. The `NEEDS YOU` /
  `DONE` labels differentiate it up close, but true non-color glance-distance
  differentiation is hard on a 240px panel. Accepted for now. If revisited, the move
  is distinct frame *patterns* (solid vs double) rather than swapping the colors.
- **Canvas is opaque to assistive tech.** The browser simulator is a `<canvas>`; screen
  readers can't read it. Acceptable — it's a 1:1 simulator of a hardware panel, not a
  web app.

## What NOT to do (anti-slop, project-specific)

- No gradient fills on the bars or background. One flat color per fill.
- No second meaning for green/amber/red. The beacon is the only exception, and only
  because the scrim + label + pulse carry the meaning, not the hue.
- No adding a third bar, a clock, a sparkline, or a logo "because there's room." There
  isn't — see the screen budget.
- No shrinking the face to fit more text. The face is the glance.
- No replacing the monospace with a proportional UI font. The mono is the instrument.

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-06 | Codified the existing locked system into DESIGN.md | Created by /design-consultation after spec→review→design→qa on the attention beacon, to give /design-review and /qa a calibration target |
| 2026-06-06 | Reordered the north star: attention > usage > aesthetics | User stated the beacon ("does Claude need my help") is the #1 reason the device sits on their desk |
| 2026-06-06 | Beacon dims the gauge (scrim) instead of just framing it | /design-review F1/F2/F4 — color collision with the usage palette + two competing glance signals; the scrim makes the alert pre-empt cleanly |
