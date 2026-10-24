#!/usr/bin/env bash
# Rehearse install.sh and rollback.sh end to end in a sandbox HOME, never on live paths.
#   rehearse.sh <empty sandbox dir inside the lane> <asks.sqlite3 copy> <requeue copy dir>
# The sandbox holds the base files (from the candidate's base tag), a copy of asks.sqlite3 and of the requeue
# entries; a systemctl shim records calls instead of acting. Exit 0 only when every assertion holds.
# shellcheck disable=SC2034  # the path and state variables are read inside the check strings
set -euo pipefail
umask 077
SB="${1:?sandbox dir}" DBCOPY="${2:?asks.sqlite3 copy}" RQCOPY="${3:?requeue copy dir}"
CAND="$(cd "$(dirname "$0")/.." && pwd)"
LANE="$(dirname "$CAND")"
case "$(realpath -m "$SB")/" in "$LANE"/*) ;; *) echo "sandbox must be inside $LANE" >&2; exit 2 ;; esac
[ ! -e "$SB" ] || [ -z "$(ls -A "$SB")" ] || { echo "sandbox must be empty" >&2; exit 2; }
H="$SB/home"
mkdir -p "$SB/shim" "$H/.local/lib/sats-stall-watchdog" "$H/.local/bin" "$H/work/t3-mcp-connect-2026-10-07/scripts" \
         "$H/.config/systemd/user" "$H/.local/state/sats-stall-watchdog" "$H/.local/state/sats-completion/requeue"
git -C "$CAND" show base:tools/sats-stall-watchdog/src/sats_stall_asks.py > "$H/.local/lib/sats-stall-watchdog/sats_stall_asks.py"
for m in sats_stall_collector.py sats_stall_mcp.py sats_stall_watchdog.py; do
  git -C "$CAND" show "base:tools/sats-stall-watchdog/src/$m" > "$H/.local/lib/sats-stall-watchdog/$m"
done
git -C "$CAND" show base:notify/sats-completion-notify > "$H/.local/bin/sats-completion-notify"
chmod 755 "$H/.local/bin/sats-completion-notify"
git -C "$CAND" show base:mcp/mcp_call.py > "$H/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py"
chmod 644 "$H/.local/lib/sats-stall-watchdog/sats_stall_asks.py" "$H/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py"
cp "$DBCOPY" "$H/.local/state/sats-stall-watchdog/asks.sqlite3"
cp -p "$RQCOPY"/*.json "$H/.local/state/sats-completion/requeue/"
cat > "$SB/shim/systemctl" <<'EOF'
#!/usr/bin/env bash
echo "systemctl $*" >> "$SHIM_LOG"
case "$*" in
  *"show -p ActiveState --value sats-stall-watchdog.service") echo inactive ;;
  *"show -p NextElapseUSecRealtime --value sats-stall-watchdog.timer") date -d '+4 min' '+%a %Y-%m-%d %H:%M:%S %Z' ;;
  *"show -p ActiveEnterTimestamp --value sats-stall-watchdog.timer") echo 'Fri 2026-10-23 08:00:00 CDT' ;;
  *"is-active sats-completion-requeue.timer") echo active ;;
esac
exit 0
EOF
chmod 700 "$SB/shim/systemctl"
export SHIM_LOG="$SB/systemctl.log" HOME="$H" PATH="$SB/shim:$PATH" NOTICE_PACKAGE_RECORD_ROOT="$SB"
sha() { sha256sum "$1" | cut -d' ' -f1; }
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; FAILED=1; fi; }
FAILED=0
ASKS="$H/.local/lib/sats-stall-watchdog/sats_stall_asks.py" NOTIFY="$H/.local/bin/sats-completion-notify"
MCP="$H/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py" DB="$H/.local/state/sats-stall-watchdog/asks.sqlite3"
RQ="$H/.local/state/sats-completion/requeue"
before=$(sqlite3 -readonly "$DB" "SELECT sql FROM sqlite_master WHERE name='events'"; sqlite3 -readonly "$DB" "SELECT count(*) FROM events")

bash "$CAND/install/install.sh" --head HEAD --dry-run > "$SB/dry-run.txt"
check "dry run changes nothing" '[ "$(sha "$ASKS")" = 406e3fd97579e823f67d27f4e02f4b81cab11a720f39df8ff5bb7e2af16a0a22 ] && { [ ! -e "$SHIM_LOG" ] || ! grep -q -v " show " "$SHIM_LOG"; }'
bash "$CAND/install/install.sh" --head HEAD > "$SB/install.txt"
R=$(ls -d "$SB"/install-record-*)
check "files are the candidate" '[ "$(sha "$ASKS")" = "$(sha "$CAND/tools/sats-stall-watchdog/src/sats_stall_asks.py")" ] && [ "$(sha "$NOTIFY")" = "$(sha "$CAND/notify/sats-completion-notify")" ] && [ "$(sha "$MCP")" = "$(sha "$CAND/mcp/mcp_call.py")" ]'
check "backups are the bases" '[ "$(sha "$R/asks.bak")" = 406e3fd97579e823f67d27f4e02f4b81cab11a720f39df8ff5bb7e2af16a0a22 ] && [ "$(sha "$R/notify.bak")" = ad1f0106f6f8d0fad97067d7fa2807bd41c9991af5c9fc12adae91b45fc1ae62 ] && [ "$(sha "$R/mcp.bak")" = d1bb0937f00685989da4debf547fa2bcc5675226d695f78a471ba08c4eb7e4e7 ] && [ -f "$DB.bak-notice-package-$(basename "$R" | sed s/install-record-//)" ]'
check "migration up ok" 'python3 -I -c "import json,sys; r=json.load(open(sys.argv[1])); sys.exit(0 if r[\"ok\"] and r[\"applied\"] else 1)" "$R/migration-up.json"'
check "only the replay entry stays queued" '[ "$(ls "$RQ")" = "$(python3 -I -c "import json,sys; print(\"\n\".join(e[\"file\"] for e in json.load(open(sys.argv[1]))[\"entries\"] if e[\"decision\"]==\"replay\"))" "$CAND/install/requeue-triage.json")" ]'
check "archived entries kept with a manifest" '[ "$(ls "$H"/.local/state/sats-completion/requeue-archive-*/ | grep -c "\.json$")" = 25 ]'
check "systemctl touched only the requeue units" '! grep -v " show " "$SHIM_LOG" | grep -v "daemon-reload" | grep -q -v "sats-completion-requeue"'
: > "$SHIM_LOG"
bash "$CAND/install/rollback.sh" "$R" > "$SB/rollback.txt"
check "rollback restores the bases" '[ "$(sha "$ASKS")" = 406e3fd97579e823f67d27f4e02f4b81cab11a720f39df8ff5bb7e2af16a0a22 ] && [ "$(sha "$NOTIFY")" = ad1f0106f6f8d0fad97067d7fa2807bd41c9991af5c9fc12adae91b45fc1ae62 ] && [ "$(sha "$MCP")" = d1bb0937f00685989da4debf547fa2bcc5675226d695f78a471ba08c4eb7e4e7 ] && [ "$(stat -c %a "$NOTIFY")" = 755 ]'
after=$(sqlite3 -readonly "$DB" "SELECT sql FROM sqlite_master WHERE name='events'"; sqlite3 -readonly "$DB" "SELECT count(*) FROM events")
check "rollback restores the events schema and rows" '[ "$before" = "$after" ] && [ "$(sqlite3 -readonly "$DB" "PRAGMA integrity_check")" = ok ]'
check "rollback removed the units into the record" '[ ! -e "$H/.config/systemd/user/sats-completion-requeue.timer" ] && [ -f "$R/sats-completion-requeue.timer.removed" ]'
check "rollback systemctl calls" '! grep -v " show " "$SHIM_LOG" | grep -v "daemon-reload" | grep -q -v "sats-completion-requeue"'
exit "$FAILED"
