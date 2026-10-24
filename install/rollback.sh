#!/usr/bin/env bash
# notice-package-20261023 rollback (ROLLBACK.md):  rollback.sh <install-record-dir>
# Disables the new requeue units, runs the events down-migration with the installed candidate module, then
# restores every file from the ORIGINAL base backup the install recorded, a resumed install's earlier backup
# included (SOL-8). Restarts no service; the watchdog runs the old modules at its next tick.
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
FILES="asks watchdog notify mcp"
declare -A DST=([asks]="$LIB/sats_stall_asks.py" [watchdog]="$LIB/sats_stall_watchdog.py"
                [notify]="$HOME/.local/bin/sats-completion-notify" [mcp]="$HOME/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py")
declare -A MODE=([asks]=644 [watchdog]=644 [notify]=755 [mcp]=644)

# 0. Every file the install changed has a recorded original backup at its base sha, before anything changes.
declare -A BAK=() BASE=()
for k in $FILES; do
  bak_var="BAK_$k" base_var="BASE_$k" cand_var="CAND_$k"
  BAK[$k]="${!bak_var:-}" BASE[$k]="${!base_var:-}" want="${!cand_var:-}"
  [ -n "${BASE[$k]}" ] && [ -n "$want" ] || die "$RECORD/install.env names no base or candidate for $k"
  live=$(sha "${DST[$k]}")
  if [ "$live" = "${BASE[$k]}" ]; then continue; fi
  [ "$live" = "$want" ] || die "$k is $live, neither its base nor the installed candidate; nothing changed"
  [ -n "${BAK[$k]}" ] && [ -f "${BAK[$k]}" ] && [ ! -L "${BAK[$k]}" ] && [ "$(sha "${BAK[$k]}")" = "${BASE[$k]}" ] \
    || die "$k: no original backup at its base ${BASE[$k]:0:12} (recorded: ${BAK[$k]:-none}); nothing changed"
done

# Between watchdog ticks, as at install (the gate the install copied into the record; DS-H1).
GATE_PY="$RECORD/watchdog_gate.py"
[ -f "$GATE_PY" ] || GATE_PY="$(dirname "$0")/watchdog_gate.py"
ok=0
for i in $(seq 1 120); do
  if GATE=$(python3 -I "$GATE_PY"); then ok=1; break; fi
  [ "$i" = 120 ] || sleep 5
done
[ "$ok" = 1 ] || die "watchdog busy or its tick is near: $GATE"
say "watchdog idle: $GATE"

# 1. The new units: stop, disable, move the files into the record (kept, not deleted).
systemctl --user disable --now sats-completion-requeue.timer || true
systemctl --user stop sats-completion-requeue.service || true
for u in sats-completion-requeue.service sats-completion-requeue.timer; do
  [ -f "$UNITDIR/$u" ] && mv "$UNITDIR/$u" "$RECORD/$u.removed"
done
systemctl --user daemon-reload
say "requeue units disabled and removed"

# 2. Events down-migration with the candidate module the install recorded (one transaction, no VACUUM or
#    checkpoint), before the old module returns: on the per-ask schema it could claim a second BLOCKED (DS-M3).
mkdir -p "$RECORD/rollback-lib"
cp -p "$RECORD/sats_stall_asks.candidate.py" "$RECORD/rollback-lib/sats_stall_asks.py"
cp -p "$LIB/sats_stall_collector.py" "$LIB/sats_stall_mcp.py" "$RECORD/rollback-lib/"
python3 -I "$RECORD/events_migration.py" --lib "$RECORD/rollback-lib" down "$DB" > "$RECORD/migration-down.json" \
  || die "down-migration failed; restore nothing more and see ROLLBACK.md, last resort"
say "events downgraded"

# 3. Restore every changed file from its original backup (same-directory temp, then rename), drop stale bytecode.
for k in $FILES; do
  if [ "$(sha "${DST[$k]}")" = "${BASE[$k]}" ]; then say "$k already at its base"; continue; fi
  tmp="$(dirname "${DST[$k]}")/.$(basename "${DST[$k]}").rollback-$TS"
  install -m "${MODE[$k]}" "${BAK[$k]}" "$tmp"
  mv -f "$tmp" "${DST[$k]}"
  [ "$(sha "${DST[$k]}")" = "${BASE[$k]}" ] || die "$k restore"
  say "$k restored from ${BAK[$k]} (${BASE[$k]:0:12})"
done
rm -f "$LIB"/__pycache__/sats_stall_asks.*.pyc "$LIB"/__pycache__/sats_stall_watchdog.*.pyc

python3 -I -c 'import sqlite3,sys
d=sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
assert d.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
assert not any(r[1]=="ask" for r in d.execute("PRAGMA table_xinfo(events)"))
print("asks.sqlite3 back on the one-per-generation schema, integrity ok")' "$DB"
[ "$(systemctl --user show -p ActiveEnterTimestamp --value sats-stall-watchdog.timer)" = "$WD_TIMER_BEFORE" ] || say "note: watchdog timer ActiveEnterTimestamp changed since install"
say "rolled back; canon commits are reverted separately (ROLLBACK.md step 4)"
