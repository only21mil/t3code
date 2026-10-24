#!/usr/bin/env bash
# Rehearse install.sh and rollback.sh end to end in sandbox HOMEs, never on live paths.
#   rehearse.sh <empty sandbox dir inside the lane> <asks.sqlite3 copy> <requeue copy dir>
# Each case gets its own HOME with the base files (from the candidate's base tag; the asks module is the live base
# cb8a6cc0, tests/preimage/live-20261023-needs-victor, with its 406e3fd9 .bak-needs-victor backup beside it as on F-D),
# a copy of asks.sqlite3 and of the
# requeue entries. A systemctl shim records calls and answers as live systemd 259 does for the monotonic watchdog
# timer: empty NextElapseUSecRealtime, a NextElapseUSecMonotonic timespan, list-timers JSON with the next epoch
# (DS-M4). A thread-reader fixture answers the replay recheck (SOL-7); nothing reads the network. sleep is a no-op.
# Cases: main (dry run, install, rollback), answered (the replay ask was answered after the triage), resume (an
# interrupted install resumed, then rolled back; SOL-8). REHEARSE_SCRIPTS=<dir> runs another install.sh and
# rollback.sh, and SHIM_REALTIME=1 brings back the old shim's realtime next elapse so pre-repair scripts get past
# their gate; both exist only for the before-repair receipts. Exit 0 only when every check passes.
# shellcheck disable=SC2034  # the path and state variables are read inside the check strings
set -uo pipefail
umask 077
SB="${1:?sandbox dir}" DBCOPY="${2:?asks.sqlite3 copy}" RQCOPY="${3:?requeue copy dir}"
CAND="$(cd "$(dirname "$0")/.." && pwd)"
LANE="$(dirname "$CAND")"
SCRIPTS="${REHEARSE_SCRIPTS:-$CAND/install}"
case "$(realpath -m "$SB")/" in "$LANE"/*) ;; *) echo "sandbox must be inside $LANE" >&2; exit 2 ;; esac
[ ! -e "$SB" ] || [ -z "$(ls -A "$SB")" ] || { echo "sandbox must be empty" >&2; exit 2; }
mkdir -p "$SB/shim"
BASE_ASKS=cb8a6cc0f676ab0062b31ecbde7a59c2137e3bb9cb197b9fd066dd603925ad94
FIRST_ASKS=406e3fd97579e823f67d27f4e02f4b81cab11a720f39df8ff5bb7e2af16a0a22  # the needs-victor fix's own backup
BASE_WATCHDOG=6ea2e6fb3fe1134b0a5f3b99962c2837842b20fda06ce9632e74e206dfa1a06d
BASE_NOTIFY=ad1f0106f6f8d0fad97067d7fa2807bd41c9991af5c9fc12adae91b45fc1ae62
BASE_MCP=d1bb0937f00685989da4debf547fa2bcc5675226d695f78a471ba08c4eb7e4e7
REPLAY=145cc028476c56146c1cb13ad440995e6f874fa7500365f23ddaf0e96f9551a6.json

cat > "$SB/shim/systemctl" <<'SHIM'
#!/usr/bin/env bash
echo "systemctl $*" >> "$SHIM_LOG"
case "$*" in
  *"show -p LoadState --value sats-stall-watchdog."*) echo loaded ;;
  *"show -p ActiveState --value sats-stall-watchdog.service") echo inactive ;;
  *"show -p ActiveState --value sats-stall-watchdog.timer") echo active ;;
  *"show -p NextElapseUSecRealtime --value sats-stall-watchdog.timer")  # empty: systemd 259, monotonic timer
    if [ -n "${SHIM_REALTIME:-}" ]; then date -d '+4 min' '+%a %Y-%m-%d %H:%M:%S %Z'; else echo; fi ;;
  *"show -p NextElapseUSecMonotonic --value sats-stall-watchdog.timer")
    python3 -I -c 'import time
t = time.monotonic() + 240; d, r = divmod(t, 86400); h, r = divmod(r, 3600); m, s = divmod(r, 60)
print("%dd %dh %dmin %.6fs" % (d, h, m, s))' ;;
  *"list-timers --all --output=json")
    [ -z "${SHIM_NO_LIST_TIMERS:-}" ] || exit 1
    python3 -I -c 'import json, time
n = int((time.time() + 240) * 1e6)  # systemd 259 prints next and left as the same epoch
print(json.dumps([{"next": n, "left": n, "last": n - 300000000, "passed": int((time.monotonic() - 60) * 1e6),
                   "unit": "sats-stall-watchdog.timer", "activates": "sats-stall-watchdog.service"}]))' ;;
  *"show -p ActiveEnterTimestamp --value sats-stall-watchdog.timer") echo 'Wed 2026-10-21 07:13:30 CDT' ;;
  *"is-active sats-completion-requeue.timer") echo active ;;
esac
exit 0
SHIM
printf '#!/usr/bin/env bash\nexit 0\n' > "$SB/shim/sleep"
cat > "$SB/shim/thread-reader" <<'READER'
#!/usr/bin/env -S python3 -I
"""t3_thread_read for the replay recheck from a fixture: f13pro a9acdeb1 after its ask (position 27), settled by the
sweep; REHEARSE_ANSWERED adds Victor's answer at position 40."""
import json, os, sys
host, args = sys.argv[1], json.loads(sys.argv[2])
with open(os.environ['SHIM_LOG'], 'a') as log:
    log.write('thread-read %s %s\n' % (host, json.dumps(args, sort_keys=True)))
assert host == 'f13pro' and args['threadId'] == 'mcp:a9acdeb1-4e97-4e68-953c-72681ef9cf07', args
items = [{'position': 28, 'type': 'assistant_message'}, {'position': 38, 'type': 'assistant_message'}]
if os.environ.get('REHEARSE_ANSWERED'):
    items.append({'position': 40, 'type': 'user_message'})
print(json.dumps({'thread': {'threadId': args['threadId'], 'settled': True, 'status': 'completed'},
                  'items': [i for i in items if i['position'] > args.get('afterPosition', -1)], 'hasMore': False}))
READER
chmod 700 "$SB/shim/systemctl" "$SB/shim/sleep" "$SB/shim/thread-reader"
export PATH="$SB/shim:$PATH" NOTICE_PACKAGE_THREAD_READER="$SB/shim/thread-reader"
sha() { sha256sum "$1" | cut -d' ' -f1; }
FAILED=0
check() { if eval "$2"; then echo "PASS $CASE: $1"; else echo "FAIL $CASE: $1"; FAILED=1; fi; }
run() { local out="$1"; shift; "$@" > "$out" 2>&1; echo "rc=$?" >> "$out"; }
ok() { tail -n 1 "$1" | grep -qx 'rc=0'; }

home() {  # a fresh sandbox HOME for case $1: base files, the asks.sqlite3 copy, the requeue copy
  CASE="$1" C="$SB/$1" H="$SB/$1/home"
  mkdir -p "$C" "$H/.local/lib/sats-stall-watchdog" "$H/.local/bin" "$H/work/t3-mcp-connect-2026-10-07/scripts" \
           "$H/.config/systemd/user" "$H/.local/state/sats-stall-watchdog" "$H/.local/state/sats-completion/requeue"
  for m in sats_stall_collector.py sats_stall_mcp.py sats_stall_watchdog.py; do
    git -C "$CAND" show "base:tools/sats-stall-watchdog/src/$m" > "$H/.local/lib/sats-stall-watchdog/$m"
  done
  git -C "$CAND" show HEAD:tools/sats-stall-watchdog/tests/preimage/live-20261023-needs-victor/sats_stall_asks.py \
    > "$H/.local/lib/sats-stall-watchdog/sats_stall_asks.py"
  git -C "$CAND" show base:tools/sats-stall-watchdog/src/sats_stall_asks.py \
    > "$H/.local/lib/sats-stall-watchdog/sats_stall_asks.py.bak-needs-victor-20261023T225552"
  git -C "$CAND" show base:notify/sats-completion-notify > "$H/.local/bin/sats-completion-notify"
  git -C "$CAND" show base:mcp/mcp_call.py > "$H/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py"
  chmod 755 "$H/.local/bin/sats-completion-notify"
  chmod 644 "$H/.local/lib/sats-stall-watchdog/"*.py "$H/.local/lib/sats-stall-watchdog/"*.bak-needs-victor-* \
    "$H/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py"
  cp "$DBCOPY" "$H/.local/state/sats-stall-watchdog/asks.sqlite3"
  cp -p "$RQCOPY"/*.json "$H/.local/state/sats-completion/requeue/"
  export SHIM_LOG="$C/systemctl.log" HOME="$H" NOTICE_PACKAGE_RECORD_ROOT="$C"
  ASKS="$H/.local/lib/sats-stall-watchdog/sats_stall_asks.py" WATCHDOG="$H/.local/lib/sats-stall-watchdog/sats_stall_watchdog.py"
  NOTIFY="$H/.local/bin/sats-completion-notify" MCP="$H/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py"
  DB="$H/.local/state/sats-stall-watchdog/asks.sqlite3" RQ="$H/.local/state/sats-completion/requeue"
  : > "$SHIM_LOG"
}
events() { sqlite3 -readonly "$DB" "SELECT sql FROM sqlite_master WHERE name='events'"; sqlite3 -readonly "$DB" "SELECT count(*) FROM events"; }
bases() {  # every base back, asks at the live base cb8a6cc0 (never 406e3fd9), and its needs-victor backup untouched
  [ "$(sha "$ASKS")" = $BASE_ASKS ] && [ "$(sha "$WATCHDOG")" = $BASE_WATCHDOG ] && [ "$(sha "$NOTIFY")" = $BASE_NOTIFY ] \
    && [ "$(sha "$MCP")" = $BASE_MCP ] && [ "$(stat -c %a "$NOTIFY")" = 755 ] \
    && [ "$(sha "$ASKS.bak-needs-victor-20261023T225552")" = $FIRST_ASKS ]
}
candidates() {
  [ "$(sha "$ASKS")" = "$(sha "$CAND/tools/sats-stall-watchdog/src/sats_stall_asks.py")" ] \
    && [ "$(sha "$WATCHDOG")" = "$(sha "$CAND/tools/sats-stall-watchdog/src/sats_stall_watchdog.py")" ] \
    && [ "$(sha "$NOTIFY")" = "$(sha "$CAND/notify/sats-completion-notify")" ] && [ "$(sha "$MCP")" = "$(sha "$CAND/mcp/mcp_call.py")" ]
}
only_requeue_units() { ! grep '^systemctl' "$SHIM_LOG" | grep -v -e ' show ' -e ' list-timers ' -e 'daemon-reload' | grep -q -v 'sats-completion-requeue'; }
record() { ls -d "$C"/install-record-* 2>/dev/null | tail -n 1; }

# ---- main: dry run, install, rollback -----------------------------------------------------------------------
home main
before=$(events)
run "$C/dry-run.txt" bash "$SCRIPTS/install.sh" --head HEAD --dry-run
check "dry run passes the gate on a monotonic timer (DS-H1)" 'ok "$C/dry-run.txt" && grep -q "\"source\": \"list-timers\"" "$C/dry-run.txt"'
check "dry run changes nothing" 'bases && [ -z "$(record)" ] && only_requeue_units && ! grep -q -e enable -e start -e daemon-reload "$SHIM_LOG"'
run "$C/install.txt" bash "$SCRIPTS/install.sh" --head HEAD
R=$(record)
check "install exits 0" 'ok "$C/install.txt"'
check "files are the candidate" 'candidates'
check "backups are the bases" '[ -n "$R" ] && [ "$(sha "$R/asks.bak")" = $BASE_ASKS ] && [ "$(sha "$R/watchdog.bak")" = $BASE_WATCHDOG ] && [ "$(sha "$R/notify.bak")" = $BASE_NOTIFY ] && [ "$(sha "$R/mcp.bak")" = $BASE_MCP ] && [ -f "$DB.bak-notice-package-${R##*install-record-}" ]'
check "migration up ok" '[ -n "$R" ] && python3 -I -c "import json,sys; r=json.load(open(sys.argv[1])); sys.exit(0 if r[\"ok\"] and r[\"applied\"] else 1)" "$R/migration-up.json"'
check "the unanswered replay is rechecked and stays queued (SOL-7)" '[ "$(ls "$RQ")" = "$REPLAY" ] && grep -q "thread-read f13pro" "$SHIM_LOG" && python3 -I -c "import json,sys; r=json.load(open(sys.argv[1])); sys.exit(0 if r[\"replay\"]==[sys.argv[2]] and not r[\"answered\"] and not r[\"unverified\"] else 1)" "$R/replay-recheck.json" "$REPLAY"'
check "archived entries kept with a manifest" '[ "$(ls "$H"/.local/state/sats-completion/requeue-archive-*/ | grep -c "\.json$")" = 25 ]'
check "systemctl touched only the requeue units" 'only_requeue_units'
: > "$SHIM_LOG"
run "$C/rollback.txt" bash "$SCRIPTS/rollback.sh" "$R"
check "rollback exits 0 past the gate" 'ok "$C/rollback.txt"'
check "rollback restores the bases" 'bases'
check "rollback restores the events schema and rows" '[ "$before" = "$(events)" ] && [ "$(sqlite3 -readonly "$DB" "PRAGMA integrity_check")" = ok ]'
check "rollback removed the units into the record" '[ ! -e "$H/.config/systemd/user/sats-completion-requeue.timer" ] && [ -f "$R/sats-completion-requeue.timer.removed" ]'
check "rollback systemctl calls" 'only_requeue_units'

# ---- answered: Victor answered the replay's ask after the triage ----------------------------------------------
home answered
run "$C/install.txt" env REHEARSE_ANSWERED=1 bash "$SCRIPTS/install.sh" --head HEAD
R=$(record)
check "an ask answered since the triage is archived, not replayed (SOL-7)" '[ -z "$(ls "$RQ")" ] && ls "$H"/.local/state/sats-completion/requeue-archive-*/"$REPLAY" > /dev/null 2>&1'
check "the record names the answered entry" '[ -n "$R" ] && grep -q "$REPLAY" "$R/replay-recheck.json" && python3 -I -c "import json,sys; r=json.load(open(sys.argv[1])); sys.exit(0 if r[\"answered\"]==[sys.argv[2]] and not r[\"replay\"] else 1)" "$R/replay-recheck.json" "$REPLAY"'

# ---- resume: an install interrupted after placing asks.py, rerun, then rolled back ---------------------------
home resume
before=$(events)
EARLY="$ASKS.bak-notice-package-20261023T230000"
cp -p "$ASKS" "$EARLY"  # what the interrupted install backed up, then placed
install -m 644 "$CAND/tools/sats-stall-watchdog/src/sats_stall_asks.py" "$ASKS"
run "$C/install.txt" bash "$SCRIPTS/install.sh" --head HEAD
R=$(record)
check "the resumed install completes" 'ok "$C/install.txt" && candidates'
check "the original asks backup is kept and recorded (SOL-8)" '[ "$(sha "$EARLY")" = $BASE_ASKS ] && [ -n "$R" ] && [ "$(sha "$R/asks.bak")" = $BASE_ASKS ] && grep -q "^asks $BASE_ASKS $EARLY (an interrupted install)" "$R/backups.txt" && [ "$(ls "$ASKS".bak-notice-package-* | wc -l)" = 1 ]'
run "$C/rollback.txt" bash "$SCRIPTS/rollback.sh" "$R"
check "rollback of the resumed install restores every base, asks included (SOL-8)" 'ok "$C/rollback.txt" && bases'
check "rollback of the resumed install restores the events schema" '[ "$before" = "$(events)" ]'

# ---- first-pin: the live asks file went back to 406e3fd9 (the needs-victor fix rolled back) ---------------------
home first-pin
cp -p "$ASKS.bak-needs-victor-20261023T225552" "$ASKS"
run "$C/install.txt" bash "$SCRIPTS/install.sh" --head HEAD
check "a live 406e3fd9 stops the install before any change (LIVE-1)" '! ok "$C/install.txt" && grep -q "asks live hash $FIRST_ASKS is neither the base nor the candidate" "$C/install.txt" && [ -z "$(record)" ] && [ -z "$(ls "$ASKS".bak-notice-package-* 2>/dev/null)" ] && [ "$(sha "$ASKS")" = $FIRST_ASKS ]'

exit "$FAILED"
