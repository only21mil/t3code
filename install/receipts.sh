#!/usr/bin/env bash
# Done-check receipts for the candidate (RECEIPTS.md): every suite on the candidate, the new tests against the
# unpatched live bases (they must fail there), the vault suite, the rehearsals and the live-state readback.
#   receipts.sh > RECEIPTS.md        (writes only under <lane>/.tmp-run and <lane>/candidate/.tmp-run)
set -uo pipefail
CAND="$(cd "$(dirname "$0")/.." && pwd)"
LANE="$(dirname "$CAND")"
RUN="$CAND/.tmp-run/receipts"
rm -rf "$RUN" && mkdir -p "$RUN"
export TMPDIR="$CAND/.tmp-run" PYTHONDONTWRITEBYTECODE=1
W="$CAND/tools/sats-stall-watchdog"

block() {  # title, directory, command...: run, then print the command, exit code and output tail
  local title="$1" dir="$2" out code; shift 2
  out="$RUN/$(echo "$title" | tr -c 'A-Za-z0-9' '-').txt"
  (cd "$dir" && nice -n 10 "$@") > "$out" 2>&1
  code=$?
  printf '### %s\n\n`cd %s && %s` → exit %d\n\n```\n' "$title" "${dir#"$LANE"/}" "$*" "$code"
  grep -E '^(FAIL|ERROR):' "$out" | sort | uniq -c | sed 's/^ *//'
  tail -n 4 "$out"
  printf '```\n\n'
}

echo "# Receipts: notice-package-20261023 candidate"
echo
echo "Generated $(date '+%Y-%m-%d %H:%M %Z') on $(hostname) by \`install/receipts.sh\`. Candidate HEAD tested:"
echo "\`$(git -C "$CAND" rev-parse HEAD)\`. Raw outputs: \`candidate/.tmp-run/receipts/\`."
echo
echo "Two failures recur in every run of the frozen suite, base included:"
echo "\`test_bad_delivery_data_does_not_hide_a_live_lane\` and \`test_real_collector_excludes_terminal_pending_approval_and_child\`."
echo "\`sats_stall_collector.discover()\` (unchanged, 1a5acf4a) rejects lane roots outside \`~/work\`"
echo "(\`root-scope-rejected\`). This lane lives under \`~/.t3-nightly/scratch\`, and the 2026-10-20 run passed from \`~/work\`."
echo
echo "## 1. Candidate suites"
echo
block "watchdog suite, candidate" "$W" python3 -m unittest discover -s tests -p 'test_*.py'
block "notifier item 7, candidate" "$CAND/notify" python3 -m unittest discover -s tests -p 'test_*.py'
block "mcp_call patch 2, candidate" "$CAND/mcp" python3 -m unittest discover -s tests -p 'test_*.py'

echo "## 2. The same new tests against the unpatched live bases (must fail)"
echo
BW="$RUN/base-watchdog/tools/sats-stall-watchdog"
mkdir -p "$(dirname "$BW")" && cp -r "$W" "$BW" && rm -rf "$BW/tests/.tmp"
git -C "$CAND" show base:tools/sats-stall-watchdog/src/sats_stall_asks.py > "$BW/src/sats_stall_asks.py"
block "new watchdog tests on live asks 406e3fd9" "$BW" python3 -m unittest \
  test_asks.DoneTriggerTests test_asks.MarkersAnywhereTests test_asks.PerAskTests test_asks.EventsMigrationTests \
  test_generations.EventTests.test_done_once_on_the_done_reply_never_on_settle \
  test_generations.EventTests.test_a_status_line_that_leads_with_done_is_the_generations_done \
  test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks \
  test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none
mkdir -p "$RUN/base-notify" && git -C "$CAND" show base:notify/sats-completion-notify > "$RUN/base-notify/sats-completion-notify"
block "notifier item 7 tests on live notifier ad1f0106" "$CAND/notify" env NOTIFIER_SOURCE="$RUN/base-notify/sats-completion-notify" \
  python3 -m unittest discover -s tests -p 'test_item7.py'
mkdir -p "$RUN/base-mcp/tests" && git -C "$CAND" show base:mcp/mcp_call.py > "$RUN/base-mcp/mcp_call.py" && cp "$CAND/mcp/tests/"*.py "$RUN/base-mcp/tests/"
block "patch 2 tests on live mcp_call.py d1bb0937" "$RUN/base-mcp" python3 -m unittest discover -s tests -p 'test_*.py'
mkdir -p "$RUN/frozen" && git -C "$CAND" archive base tools/sats-stall-watchdog | tar -x -C "$RUN/frozen"
block "frozen live suite on live base (reference)" "$RUN/frozen/tools/sats-stall-watchdog" python3 -m unittest discover -s tests -p 'test_*.py'

echo "## 3. victor-vault tools/sats-stall-watchdog (canon-clone, items 4)"
echo
echo "Staged, not pushed: \`$(git -C "$LANE/canon-clone" log --format='%h %s' origin/main..HEAD | tr '\n' ';' | sed 's/;/; /g')\`"
echo
block "vault suite at HEAD (catch-up + items 1, 5, 6)" "$LANE/canon-clone/tools/sats-stall-watchdog" python3 -m unittest discover -s tests -p 'test_*.py'
echo "Vault \`src/sats_stall_asks.py\` equals the candidate: $(cmp -s "$LANE/canon-clone/tools/sats-stall-watchdog/src/sats_stall_asks.py" "$W/src/sats_stall_asks.py" && echo yes || echo NO)."
echo

echo "## 4. Migration and install rehearsals"
echo
cp "$LANE/evidence/asks-copy-20261023T204626.sqlite3" "$RUN/asks-rehearse.sqlite3"
block "migration up and down on a copy of the live asks.sqlite3" "$CAND" python3 -I install/events_migration.py --lib tools/sats-stall-watchdog/src rehearse "$RUN/asks-rehearse.sqlite3"
block "install and rollback in a sandbox HOME" "$CAND" bash install/rehearse.sh "$LANE/.tmp-run/rehearsal-$(date +%H%M%S)" \
  "$LANE/evidence/asks-copy-20261023T204626.sqlite3" "$LANE/evidence/requeue-copy"
block "shellcheck" "$CAND" shellcheck -S warning install/install.sh install/rollback.sh install/rehearse.sh install/receipts.sh
block "systemd-analyze verify" "$CAND" systemd-analyze --user verify notify/systemd/sats-completion-requeue.service notify/systemd/sats-completion-requeue.timer

echo "## 5. Live state untouched by this phase"
echo
echo '```'
for f in "$HOME/.local/lib/sats-stall-watchdog/sats_stall_asks.py" "$HOME/.local/bin/sats-completion-notify" \
         "$HOME/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py"; do sha256sum "$f"; done
units=("$HOME"/.config/systemd/user/sats-completion-requeue.*); [ -e "${units[0]}" ] && echo "requeue unit files on F-D: ${#units[@]}" || echo "requeue unit files on F-D: 0"
python3 -I - "$CAND/install/requeue-triage.json" <<'EOF'
import hashlib, json, sys
from pathlib import Path
m = json.load(open(sys.argv[1])); rq = Path(m['directory'])
live = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in rq.glob('*.json')}
print('requeue entries: %d, all matching the triage sha256: %s' % (len(live), live == {e['file']: e['sha256'] for e in m['entries']}))
EOF
sqlite3 -readonly "file:$HOME/.local/state/sats-stall-watchdog/asks.sqlite3?mode=ro" "SELECT 'live events schema: ' || sql FROM sqlite_master WHERE name='events'"
echo '```'
