"""
Claude usage reader  --  v1
-----------------------------------------------------------------
Reads the conversation logs Claude Code already writes to your
machine and adds up how many tokens you've used. No internet, no
API key, no login -- it just reads files that are already on disk.

Run it:
    py usage.py

It prints one line of JSON, for example:
    {"generated_at": "...", "session": {...}, "week": {...}}

Later, the little round desk screen will read these same numbers
and draw the gauge (Claude logo + a ring that fills green->amber->red).
-----------------------------------------------------------------
"""

import os
import json
import glob
import time
import datetime

# Folder where Claude Code stores every conversation (one folder per project).
LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "projects")

# Attention beacon written by hook.py on Claude Code's Stop/Notification hooks.
# collect() folds it into the /usage JSON so the gauge can flash amber (needs you)
# or green (done). Old alerts expire so a missed clear never strobes forever.
ALERT_FILE = os.path.join(os.path.expanduser("~"), ".claude", "gauge-alert.json")
ALERT_EXPIRE_S = 300   # an alert older than this is treated as cleared


def read_alert():
    """Read the gauge attention beacon. Returns {type, project, age_s}; type is
    'none' when there's no fresh alert (file missing, malformed, or expired)."""
    none = {"type": "none", "project": "", "age_s": 0}
    try:
        with open(ALERT_FILE, "r", encoding="utf-8") as fh:
            a = json.load(fh)
        if not isinstance(a, dict):
            return none
        age = max(0, int(time.time() - float(a.get("ts") or 0)))
        kind = a.get("type")
        if kind not in ("attention", "done") or age > ALERT_EXPIRE_S:
            return {**none, "age_s": age}
        # Cap project length: a corrupt or hand-written alert file with a huge
        # "project" string would otherwise be truncated one char at a time in
        # preview.html's banner-fit loop every frame and freeze the browser.
        return {"type": kind, "project": str(a.get("project") or "")[:64], "age_s": age}
    except Exception:
        # A corrupt or half-written alert file (bad JSON, non-dict, non-numeric
        # ts) must NEVER take down /usage or the serial bridge — degrade to "no
        # alert" instead of raising out of collect().
        return none


def parse_ts(raw):
    """Turn the timestamp text in the log into a real date/time we can compare."""
    if not raw:
        return None
    try:
        return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def blank():
    """An empty tally of the four kinds of tokens, plus a total."""
    return {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "total": 0}


def add(bucket, usage):
    """Add one message's token counts into a tally."""
    i = usage.get("input_tokens", 0) or 0
    o = usage.get("output_tokens", 0) or 0
    cr = usage.get("cache_read_input_tokens", 0) or 0
    cc = usage.get("cache_creation_input_tokens", 0) or 0
    bucket["input"] += i
    bucket["output"] += o
    bucket["cache_read"] += cr
    bucket["cache_creation"] += cc
    bucket["total"] += i + o + cr + cc


def iter_usage_records():
    """Go through recent log files and hand back (time, usage) for every
    assistant message that reported token usage."""
    now = datetime.datetime.now().astimezone()
    cutoff = now - datetime.timedelta(days=8)   # cover the weekly window; still only recent files
    pattern = os.path.join(LOG_DIR, "**", "*.jsonl")
    for path in glob.glob(pattern, recursive=True):
        try:
            if datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone() < cutoff:
                continue
        except OSError:
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    if '"usage"' not in line:          # quick skip: no usage on this line
                        continue
                    try:
                        obj = json.loads(line)
                    except ValueError:
                        continue
                    usage = (obj.get("message") or {}).get("usage")
                    if not usage:
                        continue
                    yield parse_ts(obj.get("timestamp")), usage
        except OSError:
            continue


def collect():
    """Add everything up and hand back the usage numbers as a dictionary.
    Both the command line (main) and the preview web server use this."""
    now = datetime.datetime.now().astimezone()
    today = now.date()
    one_hour_ago = now - datetime.timedelta(hours=1)
    five_hours_ago = now - datetime.timedelta(hours=5)   # Claude's session limit is a rolling 5h window
    week_ago = now - datetime.timedelta(days=7)

    hour_bucket = blank()
    session_bucket = blank()     # last 5 hours -> PRIMARY "session" ring
    today_bucket = blank()
    week_bucket = blank()        # last 7 days  -> SECONDARY "week" ring

    for ts, usage in iter_usage_records():
        if ts is None:
            continue
        if ts >= one_hour_ago:
            add(hour_bucket, usage)
        if ts >= five_hours_ago:
            add(session_bucket, usage)
        if ts >= week_ago:
            add(week_bucket, usage)
        if ts.date() == today:
            add(today_bucket, usage)

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "session": session_bucket,   # primary ring  (rolling 5 hours)
        "hour": hour_bucket,         # kept for reference / debugging
        "today": today_bucket,
        "week": week_bucket,         # secondary ring (rolling 7 days)
        "alert": read_alert(),       # attention beacon: needs you / done / none
    }


def main():
    print(json.dumps(collect()))


if __name__ == "__main__":
    main()
