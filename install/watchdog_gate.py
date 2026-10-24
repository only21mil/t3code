#!/usr/bin/env python3
"""Is the F-D stall watchdog between ticks, with its next tick at least --min seconds away? Read-only.

    watchdog_gate.py [--min 90]     prints one JSON line; exit 0 when install.sh or rollback.sh may act now, else 3

The watchdog timer is monotonic (OnBootSec=5min, OnUnitActiveSec=5min). systemd 259 leaves its
NextElapseUSecRealtime empty, so a gate that parses that property never passes (DS-H1). The next tick comes from
`systemctl --user list-timers --all --output=json` (`next`, microseconds since the epoch), else from
NextElapseUSecMonotonic against CLOCK_MONOTONIC. While the service runs a tick the timer has no next elapse, which
is busy. A stopped timer schedules no tick. The script runs only `systemctl --user show` and `list-timers`.
"""
import argparse
import json
import re
import subprocess
import sys
import time

SERVICE, TIMER = 'sats-stall-watchdog.service', 'sats-stall-watchdog.timer'
BUSY = {'active', 'activating', 'deactivating', 'reloading', 'refreshing'}
UNITS = {'y': 31557600, 'month': 2629800, 'w': 604800, 'd': 86400, 'h': 3600, 'min': 60, 's': 1, 'ms': 1e-3, 'us': 1e-6}
SPAN_RE = re.compile(r'(\d+(?:\.\d+)?)(month|min|ms|us|y|w|d|h|s)')


def systemctl(*args):
    return subprocess.run(['systemctl', '--user', *args], capture_output=True, text=True, timeout=20)


def show(unit, prop):
    return systemctl('show', '-p', prop, '--value', unit).stdout.strip()


def timespan(text):
    """Seconds in a systemd timespan ("2d 15h 17min 58.829349s"), else None ("infinity", empty, unparsed)."""
    text = text.replace(' ', '')
    if not text or SPAN_RE.sub('', text):
        return None
    return sum(float(value) * UNITS[unit] for value, unit in SPAN_RE.findall(text))


def next_tick():
    """(seconds to the next tick, source), or (None, None) when the timer has none."""
    listing = systemctl('list-timers', '--all', '--output=json')
    if listing.returncode == 0:
        try:
            row = next((r for r in json.loads(listing.stdout) if r.get('unit') == TIMER), None)
        except (ValueError, AttributeError):
            row = None
        if row is not None:
            value = row.get('next')
            return (value / 1e6 - time.time(), 'list-timers') if type(value) is int and value > 0 else (None, 'list-timers')
    monotonic = timespan(show(TIMER, 'NextElapseUSecMonotonic'))
    return (monotonic - time.monotonic(), 'monotonic') if monotonic is not None else (None, None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--min', type=float, default=90)
    args = parser.parse_args(argv)
    service, timer = show(SERVICE, 'ActiveState'), show(TIMER, 'ActiveState')
    left, source = next_tick()
    ok = service not in BUSY and (timer != 'active' or (left is not None and left >= args.min))
    print(json.dumps({'service': service, 'timer': timer, 'left': None if left is None else round(left, 1),
                      'source': source, 'min': args.min, 'ok': ok}, sort_keys=True))
    return 0 if ok else 3


if __name__ == '__main__':
    sys.exit(main())
