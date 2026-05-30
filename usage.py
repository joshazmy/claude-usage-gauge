"""
Claude usage reader  --  v1
-----------------------------------------------------------------
Reads the conversation logs Claude Code already writes to your
machine and adds up how many tokens you've used. No internet, no
API key, no login -- it just reads files that are already on disk.

Run it:
    py usage.py

It prints one line of JSON, for example:
    {"generated_at": "...", "today": {...}, "last_5h": {...}}

Later, the little round desk screen will read these same numbers
and draw the gauge (Claude logo + a ring that fills green->amber->red).
-----------------------------------------------------------------
"""

import os
import json
import glob
import datetime

# Folder where Claude Code stores every conversation (one folder per project).
LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "projects")


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
    week_ago = now - datetime.timedelta(days=7)

    hour_bucket = blank()
    today_bucket = blank()
    week_bucket = blank()

    for ts, usage in iter_usage_records():
        if ts is None:
            continue
        if ts >= one_hour_ago:
            add(hour_bucket, usage)
        if ts >= week_ago:
            add(week_bucket, usage)
        if ts.date() == today:
            add(today_bucket, usage)

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "hour": hour_bucket,    # outer ring
        "today": today_bucket,
        "week": week_bucket,    # inner ring
    }


def main():
    print(json.dumps(collect()))


if __name__ == "__main__":
    main()
