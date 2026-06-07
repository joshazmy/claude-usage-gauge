"""
hook.py  --  Claude Code hooks -> the gauge's attention beacon
-----------------------------------------------------------------
Wired into ~/.claude/settings.json so Claude Code calls it on three events:

    UserPromptSubmit -> py hook.py prompt   (you're back: clear flash, stamp turn start)
    Stop             -> py hook.py stop      (turn finished: flash "done" if it ran long)
    Notification     -> py hook.py notify    (Claude needs you: flash "needs you")

It writes a tiny state file, ~/.claude/gauge-alert.json, which usage.py reads and
the gauge (browser preview now, ESP32 later) turns into a flashing border:
amber = needs you, green = done.

Design rules that keep it from being annoying or fragile:
  * "done" only flashes when the turn ran >= DONE_MIN_SECONDS. Stop fires on EVERY
    reply; without this gate the gauge would strobe while you're actively chatting.
  * Submitting your next prompt clears the flash (you've come back to the terminal).
  * Alerts expire (usage.py side) so a missed clear never strobes forever.
  * Always exits 0 and never prints to stdout -- a hook must never wedge a session,
    and UserPromptSubmit stdout would get injected into Claude's context.
-----------------------------------------------------------------
"""
import sys
import os
import json
import time

HOME = os.path.expanduser("~")
CLAUDE_DIR = os.path.join(HOME, ".claude")
ALERT_FILE = os.path.join(CLAUDE_DIR, "gauge-alert.json")
STATE_DIR = os.path.join(CLAUDE_DIR, "gauge-state")   # per-session turn-start marks

DONE_MIN_SECONDS = 30   # turns shorter than this do NOT flash "done" (anti-noise gate)


def _read_stdin_json():
    """Claude Code hands hooks a JSON object on stdin. Parse it defensively."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw and raw.strip() else {}
    except Exception:
        return {}


def _project_name(data):
    cwd = (data.get("cwd") if isinstance(data, dict) else None) or os.getcwd()
    try:
        return os.path.basename(os.path.normpath(cwd)) or "claude"
    except Exception:
        return "claude"


def _session_id(data):
    sid = data.get("session_id") if isinstance(data, dict) else None
    return str(sid or "default")


def _start_path(sid):
    safe = "".join(c for c in sid if c.isalnum() or c in "-_")[:64] or "default"
    return os.path.join(STATE_DIR, "start-" + safe)


def _write_alert(kind, project):
    try:
        os.makedirs(CLAUDE_DIR, exist_ok=True)
        tmp = ALERT_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"type": kind, "project": project, "ts": time.time()}, f)
        os.replace(tmp, ALERT_FILE)   # atomic: a reader never sees a half-written file
    except Exception:
        pass


def _clear_alert():
    try:
        if os.path.exists(ALERT_FILE):
            os.remove(ALERT_FILE)
    except Exception:
        pass


def cmd_prompt(data):
    """You submitted a prompt: you're driving again. Clear the flash, stamp the
    start time so Stop can measure how long this turn ran."""
    _clear_alert()
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(_start_path(_session_id(data)), "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except Exception:
        pass


def cmd_stop(data):
    """Main agent finished a turn. Flash "done" only if the turn was long enough
    that you'd likely have walked away."""
    sid = _session_id(data)
    sp = _start_path(sid)
    started = None
    try:
        with open(sp, "r", encoding="utf-8") as f:
            started = float(f.read().strip())
    except Exception:
        started = None
    # Conservative: if we can't tell how long the turn ran, don't flash (no noise).
    if started is not None and (time.time() - started) >= DONE_MIN_SECONDS:
        _write_alert("done", _project_name(data))
    try:
        if os.path.exists(sp):
            os.remove(sp)
    except Exception:
        pass


# Notification fires for several reasons; only some mean "you must act".
# Suppress the known non-actionable ones (login ok, elicitation acks) so the
# gauge only flashes amber when you actually have to do something. Unknown or
# missing types still flash, to stay forward-compatible with new event kinds.
_QUIET_NOTIFICATIONS = {"auth_success", "elicitation_complete", "elicitation_response"}


def cmd_notify(data):
    """Claude needs you: a permission prompt, or the input sat idle. Skip
    non-actionable notifications so the beacon stays high-signal."""
    ntype = data.get("notification_type") if isinstance(data, dict) else None
    if str(ntype or "") in _QUIET_NOTIFICATIONS:
        return
    _write_alert("attention", _project_name(data))


def main():
    try:
        cmd = sys.argv[1] if len(sys.argv) > 1 else ""
        data = _read_stdin_json()
        if cmd == "prompt":
            cmd_prompt(data)
        elif cmd == "stop":
            cmd_stop(data)
        elif cmd == "notify":
            cmd_notify(data)
        # unknown command -> no-op
    except Exception:
        # A hook must NEVER wedge a Claude Code session. Swallow anything that
        # slips past the inner guards (e.g. os.getcwd() raising on a deleted
        # working dir) and still exit clean.
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
