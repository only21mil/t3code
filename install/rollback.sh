#!/usr/bin/env bash
# notice-package-20261023 rollback (ROLLBACK.md):  rollback.sh <install-record-dir>
# Disables the new requeue units, runs the events down-migration with the installed candidate module, then
# restores every .bak the install wrote. Restarts no service; the watchdog runs the old module at its next tick.
# Archived requeue entries stay archived: moving them back would queue stale and DONE notices again.
set -euo pipefail
umask 077
RECORD="${1:?usage: rollback.sh <install-record-dir>}"
# shellcheck disable=SC1091
. "$RECORD/install.env"
LIB="$HOME/.local/lib/sats-stall-watchdog"
UNITDIR="$HOME/.config/systemd/user"
DB="$HOME/.local/state/sats-stall-watchdog/asks.sqlite3"
say() { printf '%s %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { say "STOP: $*"; exit 1; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
declare -A DST=([asks]="$LIB/sats_stall_asks.py" [notify]="$HOME/.local/bin/sats-completion-notify"
                [mcp]="$HOME/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py")
declare -A MODE=([asks]=644 [notify]=755 [mcp]=644)

# Between watchdog ticks, as at install.
for _ in $(seq 1 120); do
  state=$(systemctl --user show -p ActiveState --value sats-stall-watchdog.service)
  next=$(systemctl --user show -p NextElapseUSecRealtime --value sats-stall-watchdog.timer)
  left=$(( $(date -d "$next" +%s 2>/dev/null || echo 0) - $(date +%s) ))
  if [ "$state" != activating ] && [ "$state" != active ] && [ "$left" -ge 90 ]; then break; fi
  sleep 5
done
[ "$state" != activating ] && [ "$state" != active ] && [ "$left" -ge 90 ] || die "watchdog busy or its tick is near"

# 1. The new units: stop, disable, move the files into the record (kept, not deleted).
systemctl --user disable --now sats-completion-requeue.timer || true
systemctl --user stop sats-completion-requeue.service || true
for u in sats-completion-requeue.service sats-completion-requeue.timer; do
  [ -f "$UNITDIR/$u" ] && mv "$UNITDIR/$u" "$RECORD/$u.removed"
done
systemctl --user daemon-reload
say "requeue units disabled and removed"

# 2. Events down-migration with the candidate module the install recorded (one transaction, no VACUUM or
#    checkpoint). Per-ask BLOCKED rows after the first of a generation move to events_parked.
mkdir -p "$RECORD/rollback-lib"
cp -p "$RECORD/sats_stall_asks.candidate.py" "$RECORD/rollback-lib/sats_stall_asks.py"
cp -p "$LIB/sats_stall_collector.py" "$LIB/sats_stall_mcp.py" "$RECORD/rollback-lib/"
python3 -I "$RECORD/events_migration.py" --lib "$RECORD/rollback-lib" down "$DB" > "$RECORD/migration-down.json" \
  || die "down-migration failed; the old module still runs on the per-ask schema (ROLLBACK.md, last resort)"
say "events downgraded"

# 3. Restore every backed-up file (same-directory temp, then rename) and drop the stale bytecode.
for k in asks notify mcp; do
  bak="${DST[$k]}.bak-notice-package-$TS"
  [ -f "$bak" ] || continue
  tmp="$(dirname "${DST[$k]}")/.$(basename "${DST[$k]}").rollback-$TS"
  install -m "${MODE[$k]}" "$bak" "$tmp"
  mv -f "$tmp" "${DST[$k]}"
  [ "$(sha "${DST[$k]}")" = "$(sha "$bak")" ] || die "$k restore"
  say "$k restored ($(sha "$bak" | cut -c1-12))"
done
rm -f "$LIB"/__pycache__/sats_stall_asks.*.pyc

python3 -I -c 'import sqlite3,sys
d=sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
assert d.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
assert not any(r[1]=="ask" for r in d.execute("PRAGMA table_xinfo(events)"))
print("asks.sqlite3 back on the one-per-generation schema, integrity ok")' "$DB"
[ "$(systemctl --user show -p ActiveEnterTimestamp --value sats-stall-watchdog.timer)" = "$WD_TIMER_BEFORE" ] || say "note: watchdog timer ActiveEnterTimestamp changed since install"
say "rolled back; canon commits are reverted separately (ROLLBACK.md step 4)"
