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
  if [ "$(wc -l < "$out")" -le 30 ]; then cat "$out"; else  # short outputs whole, long ones as failures and tail
    grep -E '^(FAIL|ERROR):' "$out" | sort | uniq -c | sed 's/^ *//'
    tail -n 4 "$out"
  fi
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
block "install gate and replay recheck, candidate" "$CAND/install" python3 -m unittest discover -s tests -p 'test_*.py'

echo "## 2. The same new tests against the unpatched live bases (must fail)"
echo
BW="$RUN/base-watchdog/tools/sats-stall-watchdog"
mkdir -p "$(dirname "$BW")" && cp -r "$W" "$BW" && rm -rf "$BW/tests/.tmp"
git -C "$CAND" show base:tools/sats-stall-watchdog/src/sats_stall_asks.py > "$BW/src/sats_stall_asks.py"
block "new watchdog tests on live asks 406e3fd9" "$BW/tests" python3 -m unittest \
  test_asks.DoneTriggerTests test_asks.MarkersAnywhereTests test_asks.PerAskTests test_asks.EventsMigrationTests \
  test_generations.EventTests.test_done_once_on_the_done_reply_never_on_settle \
  test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks \
  test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none
mkdir -p "$RUN/base-notify" && git -C "$CAND" show base:notify/sats-completion-notify > "$RUN/base-notify/sats-completion-notify"
block "notifier item 7 tests on live notifier ad1f0106" "$CAND/notify" env NOTIFIER_SOURCE="$RUN/base-notify/sats-completion-notify" \
  python3 -m unittest discover -s tests -p 'test_item7.py'
mkdir -p "$RUN/base-mcp/tests" && git -C "$CAND" show base:mcp/mcp_call.py > "$RUN/base-mcp/mcp_call.py" && cp "$CAND/mcp/tests/"*.py "$RUN/base-mcp/tests/"
block "patch 2 tests on live mcp_call.py d1bb0937" "$RUN/base-mcp" python3 -m unittest discover -s tests -p 'test_*.py'
mkdir -p "$RUN/frozen" && git -C "$CAND" archive base tools/sats-stall-watchdog | tar -x -C "$RUN/frozen"
block "frozen live suite on live base (reference)" "$RUN/frozen/tools/sats-stall-watchdog" python3 -m unittest discover -s tests -p 'test_*.py'

echo "## 2b. Review round-1 tests against the round-0 candidate e6a95f42 (must fail)"
echo
PRE="$RUN/round0"
mkdir -p "$PRE/install-scripts" "$PRE/mcp/tests"
git -C "$CAND" archive HEAD tools/sats-stall-watchdog | tar -x -C "$PRE"
for m in sats_stall_asks.py sats_stall_watchdog.py; do git -C "$CAND" show "e6a95f42:tools/sats-stall-watchdog/src/$m" > "$PRE/tools/sats-stall-watchdog/src/$m"; done
git -C "$CAND" show e6a95f42:mcp/mcp_call.py > "$PRE/mcp/mcp_call.py" && cp "$CAND/mcp/tests/"*.py "$PRE/mcp/tests/"
for f in install.sh rollback.sh; do git -C "$CAND" show "e6a95f42:install/$f" > "$PRE/install-scripts/$f"; done
block "round-1 watchdog tests on e6a95f42 (asks 8772ee0b, watchdog 6ea2e6fb)" "$PRE/tools/sats-stall-watchdog/tests" python3 -m unittest \
  test_generations.EventTests.test_SOL1_a_done_led_progress_line_then_a_final_progress_reply_sends_no_done \
  test_generations.EventTests.test_SOL1_kimi_replies_that_restate_done_keep_it_on_the_done_replys_run \
  test_generations.EventTests.test_DSH2_single_read_message_after_a_done_reply_opens_a_generation \
  test_generations.EventTests.test_DSH2_grace_reread_message_after_a_done_reply_opens_a_generation \
  test_generations.EventTests.test_DSH2_a_follow_up_inside_the_done_replys_grace_claims_that_done_after_the_grace \
  test_asks.ThreadNoticeTests.test_SOL2_a_delivered_turn_notice_covers_only_the_asks_it_carried \
  test_generations.RepairRound1Tests test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send \
  test_asks.EventsMigrationTests.test_DSM3_a_per_ask_only_generation_downgrades_to_the_legacy_key
block "round-1 settle guard tests on e6a95f42 mcp_call.py b1959e29" "$PRE/mcp" env WATCHDOG_SRC="$W/src" python3 -m unittest \
  tests.test_settle_guard.SettleGuardTests.test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses \
  tests.test_settle_guard.SettleGuardTests.test_SOL5_missing_watchdog_detection_refuses \
  tests.test_settle_guard.SettleGuardTests.test_SOL6_a_required_reviewer_without_accept_refuses
block "rehearsal with the e6a95f42 install.sh and rollback.sh, systemd-259 shim (DS-H1)" "$CAND" env REHEARSE_SCRIPTS="$PRE/install-scripts" \
  bash install/rehearse.sh "$RUN/rehearsal-round0-259" "$LANE/evidence/asks-copy-20261023T204626.sqlite3" "$LANE/evidence/requeue-copy"
block "rehearsal with the e6a95f42 scripts past their gate, old realtime shim (SOL-7, SOL-8)" "$CAND" env SHIM_REALTIME=1 REHEARSE_SCRIPTS="$PRE/install-scripts" \
  bash install/rehearse.sh "$RUN/rehearsal-round0-realtime" "$LANE/evidence/asks-copy-20261023T204626.sqlite3" "$LANE/evidence/requeue-copy"
echo "Asks after the round-0 rollback of a resumed install: \`$(sha256sum "$RUN/rehearsal-round0-realtime/resume/home/.local/lib/sats-stall-watchdog/sats_stall_asks.py" | cut -c1-16)\` (the candidate; base is 406e3fd9)."
echo

echo "## 3. victor-vault tools/sats-stall-watchdog (canon-clone, items 4)"
echo
echo "Staged, not pushed: \`$(git -C "$LANE/canon-clone" log --format='%h %s' origin/main..HEAD | tr '\n' ';' | sed 's/;/; /g')\`"
echo
block "vault suite at HEAD (catch-up + items 1, 5, 6)" "$LANE/canon-clone/tools/sats-stall-watchdog" python3 -m unittest discover -s tests -p 'test_*.py'
for m in sats_stall_asks.py sats_stall_watchdog.py; do
  echo "Vault \`src/$m\` equals the candidate: $(cmp -s "$LANE/canon-clone/tools/sats-stall-watchdog/src/$m" "$W/src/$m" && echo yes || echo NO)."
done
echo

echo "## 4. Migration and install rehearsals"
echo
cp "$LANE/evidence/asks-copy-20261023T204626.sqlite3" "$RUN/asks-rehearse.sqlite3"
block "migration up and down on a copy of the live asks.sqlite3" "$CAND" python3 -I install/events_migration.py --lib tools/sats-stall-watchdog/src rehearse "$RUN/asks-rehearse.sqlite3"
block "install and rollback in a sandbox HOME" "$CAND" bash install/rehearse.sh "$RUN/rehearsal" \
  "$LANE/evidence/asks-copy-20261023T204626.sqlite3" "$LANE/evidence/requeue-copy"
RCA=/home/victor/.t3-nightly/worktrees/t3code-fork/grokbot-fd-master-fix-20261023/lanes/fd-master-fix-20261023/notice-delay-rca-20261023
block "RCA patch-1 behavior check (check_done.py, Kimi included) on the candidate module" "$CAND" python3 -B -I "$RCA/.stage/check_done.py" "$W/src/sats_stall_asks.py" "$W/src"
block "RCA patch-1 tick check (check_tick.py --staged) on the candidate module" "$CAND" python3 -B -I "$RCA/.stage/check_tick.py" "$W/src/sats_stall_asks.py" "$W/src" --staged
block "shellcheck" "$CAND" shellcheck -S warning install/install.sh install/rollback.sh install/rehearse.sh install/receipts.sh
block "systemd-analyze verify" "$CAND" systemd-analyze --user verify notify/systemd/sats-completion-requeue.service notify/systemd/sats-completion-requeue.timer

echo "## 5. Live state untouched by this phase"
echo
echo '```'
for f in "$HOME/.local/lib/sats-stall-watchdog/sats_stall_asks.py" "$HOME/.local/lib/sats-stall-watchdog/sats_stall_watchdog.py" "$HOME/.local/bin/sats-completion-notify" \
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
