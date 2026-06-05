"""
bridge.py  --  PC -> ESP32 gauge over USB serial
-----------------------------------------------------------------
Reads your live Claude usage (via usage.py) and sends "session,week\\n"
(two ints 0-100) to the board every few seconds. This is the phase-1
data path: the PC does the reading, the board just draws.

Setup:
    pip install pyserial

Run (find the COM port in Device Manager, or `pio device list`):
    py bridge.py COM5            # Windows
    python bridge.py /dev/ttyACM0   # Linux / macOS

The redlines below are PERSONAL ESTIMATES (a vibe gauge), not Anthropic's
real limits. Keep them in sync with the ones in preview.html.
-----------------------------------------------------------------
"""
import sys
import time

import serial          # pip install pyserial
import usage           # the existing stdlib reader in this repo

SESSION_BUDGET = 100_000_000   # ~5h session redline (personal estimate)
WEEKLY_BUDGET  = 900_000_000   # ~7d weekly redline  (personal estimate)
BAUD = 115200
INTERVAL_S = 3


def pct(used, budget):
    """Clamp used/budget to an integer 0-100."""
    if budget <= 0:
        return 0
    return max(0, min(100, round(100 * used / budget)))


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "COM5"
    print("bridge -> %s @ %d baud (Ctrl+C to stop)" % (port, BAUD))
    with serial.Serial(port, BAUD, timeout=1) as ser:
        while True:
            d = usage.collect()
            s = pct(d["session"]["total"], SESSION_BUDGET)
            w = pct(d["week"]["total"], WEEKLY_BUDGET)
            line = "%d,%d\n" % (s, w)
            ser.write(line.encode("ascii"))
            print("sent", line.strip())
            time.sleep(INTERVAL_S)


if __name__ == "__main__":
    main()
