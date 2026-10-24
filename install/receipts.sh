#!/usr/bin/env bash
# Done-check receipts for the candidate (RECEIPTS.md): every suite on the candidate, the new tests against the
# unpatched live bases and the round-1 and round-2 candidates (they must fail there), the round-3 reviewers' probes
# (lane repair-r3/probes.py), the live base's 19-case matrix, the vault suite, the rehearsals and the live-state readback.
#   receipts.sh > RECEIPTS.md        (writes only under <lane>/candidate/.tmp-run)
set -uo pipefail
CAND="$(cd "$(dirname "$0")/.." && pwd)"
LANE="$(dirname "$CAND")"
RUN="$CAND/.tmp-run/receipts"
rm -rf "$RUN" && mkdir -p "$RUN"
export TMPDIR="$CAND/.tmp-run" PYTHONDONTWRITEBYTECODE=1
W="$CAND/tools/sats-stall-watchdog"
LIVEBASE="$W/tests/preimage/live-20261023-needs-victor/sats_stall_asks.py"  # cb8a6cc0, the live asks base
DBCOPY="$LANE/repair-r2/asks-copy-20261023T233547.sqlite3"  # live copy 23:35 CDT, one cb8a6cc0 BLOCKED:<digest> row
PREV=a31f46b69a08322ff2b5a7a5d5d73e80e0305025              # the round-1 candidate the round-2 review read
PREV2=917f4de00c7e867d4202c868725ca508e5574034             # the round-2 candidate the round-3 review read

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
tests_on() {  # copy of the current watchdog tree at $1 with src/sats_stall_asks.py (and watchdog.py) from $2 (and $3)
  mkdir -p "$(dirname "$1")" && cp -r "$W" "$1" && rm -rf "$1/tests/.tmp"
  cp "$2" "$1/src/sats_stall_asks.py"
  [ -z "${3:-}" ] || cp "$3" "$1/src/sats_stall_watchdog.py"
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
echo "The live asks base is cb8a6cc0, the needs-victor fix (2026-10-23 22:55:52 CDT, canon source 4a02910). The"
echo "package's first pin, 406e3fd9, is its backup and the candidate's \`base\` tag; § 2 runs the new tests on both."
echo
echo "## 1. Candidate suites"
echo
block "watchdog suite, candidate" "$W" python3 -m unittest discover -s tests -p 'test_*.py'
block "notifier item 7, candidate" "$CAND/notify" python3 -m unittest discover -s tests -p 'test_*.py'
block "mcp_call patch 2, candidate" "$CAND/mcp" python3 -m unittest discover -s tests -p 'test_*.py'
block "install gate and replay recheck, candidate" "$CAND/install" python3 -m unittest discover -s tests -p 'test_*.py'

echo "## 2. The package's watchdog tests against the unpatched live bases (must fail)"
echo
for pin in live:"$LIVEBASE" first-pin:base; do
  name="${pin%%:*}" src="${pin#*:}"
  if [ "$src" = base ]; then src="$RUN/base-asks.py"; git -C "$CAND" show base:tools/sats-stall-watchdog/src/sats_stall_asks.py > "$src"; fi
  BW="$RUN/base-watchdog-$name/tools/sats-stall-watchdog"
  tests_on "$BW" "$src"
  block "package watchdog tests on the $name asks $(sha256sum "$src" | cut -c1-8)" "$BW/tests" python3 -m unittest \
    test_asks.DoneTriggerTests test_asks.MarkersAnywhereTests test_asks.PerAskTests test_asks.EventsMigrationTests \
    test_generations.EventTests.test_done_once_on_the_done_reply_never_on_settle \
    test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks \
    test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none \
    test_asks.LiveBaseTests.test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send
done
mkdir -p "$RUN/base-notify" && git -C "$CAND" show base:notify/sats-completion-notify > "$RUN/base-notify/sats-completion-notify"
block "notifier item 7 tests on live notifier ad1f0106" "$CAND/notify" env NOTIFIER_SOURCE="$RUN/base-notify/sats-completion-notify" \
  python3 -m unittest discover -s tests -p 'test_item7.py'
mkdir -p "$RUN/base-mcp/tests" && git -C "$CAND" show base:mcp/mcp_call.py > "$RUN/base-mcp/mcp_call.py" && cp "$CAND/mcp/tests/"*.py "$RUN/base-mcp/tests/"
block "patch 2 tests on live mcp_call.py d1bb0937" "$RUN/base-mcp" env WATCHDOG_SRC="$W/src" python3 -m unittest discover -s tests -p 'test_*.py'
mkdir -p "$RUN/frozen" && git -C "$CAND" archive base tools/sats-stall-watchdog | tar -x -C "$RUN/frozen"
block "frozen live suite on its own base (reference)" "$RUN/frozen/tools/sats-stall-watchdog" python3 -m unittest discover -s tests -p 'test_*.py'

echo "## 2b. Review round-2 tests against the round-1 candidate a31f46b (must fail)"
echo
PRE="$RUN/round1"
mkdir -p "$PRE/install/tests" "$PRE/mcp/tests" "$PRE/install-scripts"
tests_on "$PRE/tools/sats-stall-watchdog" <(git -C "$CAND" show "$PREV:tools/sats-stall-watchdog/src/sats_stall_asks.py") \
  <(git -C "$CAND" show "$PREV:tools/sats-stall-watchdog/src/sats_stall_watchdog.py")
git -C "$CAND" show "$PREV:mcp/mcp_call.py" > "$PRE/mcp/mcp_call.py" && cp "$CAND/mcp/tests/"*.py "$PRE/mcp/tests/"
for f in watchdog_gate.py replay_recheck.py requeue-triage.json; do git -C "$CAND" show "$PREV:install/$f" > "$PRE/install/$f"; done
cp "$CAND/install/tests/test_install.py" "$PRE/install/tests/"
for f in install.sh rollback.sh; do git -C "$CAND" show "$PREV:install/$f" > "$PRE/install-scripts/$f"; done
block "round-2 watchdog tests on a31f46b (asks f68b5e47)" "$PRE/tools/sats-stall-watchdog/tests" python3 -m unittest \
  test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done \
  test_asks.ThreadNoticeTests.test_SOL2_r2_complete_decision_ids_and_a_phrase_of_one_ask_only \
  test_asks.ScanTests.test_agent_artifacts_after_an_ask_leave_it_open test_asks.LiveBaseTests
block "round-2 settle guard test on a31f46b mcp_call.py (NEW-2)" "$PRE/mcp" env WATCHDOG_SRC="$W/src" python3 -m unittest \
  tests.test_settle_guard.SettleGuardTests.test_NEW2_a_producer_or_repair_child_is_no_required_reviewer
block "round-2 gate and recheck tests on a31f46b watchdog_gate.py and replay_recheck.py" "$PRE/install" python3 -m unittest \
  tests.test_install.GateTests.test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed \
  tests.test_install.RecheckTests.test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer
block "rehearsal with the a31f46b install.sh and rollback.sh on the cb8a6cc0 live base (LIVE-1)" "$CAND" env REHEARSE_SCRIPTS="$PRE/install-scripts" \
  bash install/rehearse.sh "$RUN/rehearsal-round1" "$DBCOPY" "$LANE/evidence/requeue-copy"
echo "The a31f46b dry run on a cb8a6cc0 HOME: \`$(head -n 3 "$RUN/rehearsal-round1/main/dry-run.txt" | grep -m1 STOP || echo 'no STOP line')\`"
echo

echo "## 2d. Review round-3 tests against the round-2 candidate 917f4de (must fail)"
echo
PRE2="$RUN/round2"
mkdir -p "$PRE2/mcp"
tests_on "$PRE2/tools/sats-stall-watchdog" <(git -C "$CAND" show "$PREV2:tools/sats-stall-watchdog/src/sats_stall_asks.py")
git -C "$CAND" show "$PREV2:mcp/mcp_call.py" > "$PRE2/mcp/mcp_call.py" && cp -r "$CAND/mcp/tests" "$PRE2/mcp/"
block "round-3 watchdog tests on 917f4de (asks $(git -C "$CAND" show "$PREV2:tools/sats-stall-watchdog/src/sats_stall_asks.py" | sha256sum | cut -c1-8))" \
  "$PRE2/tools/sats-stall-watchdog/tests" python3 -m unittest \
  test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done \
  test_asks.ThreadNoticeTests.test_SOL2_r3_marker_words_paths_and_negated_sentences_decide_what_a_notice_carries \
  test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate
block "round-3 settle guard test on 917f4de mcp_call.py (R3-5)" "$PRE2/mcp" env WATCHDOG_SRC="$W/src" python3 -m unittest \
  tests.test_settle_guard.SettleGuardTests.test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named
block "the reviewers' round-3 probes on 917f4de (repair-r3/probes.py)" "$CAND" python3 -B "$LANE/repair-r3/probes.py" \
  "$PRE2/tools/sats-stall-watchdog/src/sats_stall_asks.py" "$PRE2/mcp/mcp_call.py"
block "the reviewers' round-3 probes on the candidate" "$CAND" python3 -B "$LANE/repair-r3/probes.py" "$W/src/sats_stall_asks.py" "$CAND/mcp/mcp_call.py"

echo "## 2c. The live base's own 19-case matrix (blocked-threads-rca-20261023, MBP)"
echo
echo "Unmodified MBP copy (\`repair-r2/needs-victor-matrix/test_needs_victor.py\`, sha256 \`$(sha256sum "$LANE/repair-r2/needs-victor-matrix/test_needs_victor.py" | cut -c1-16)\`), deps = this suite's src:"
echo
block "unmodified matrix on the live base cb8a6cc0" "$LANE/repair-r2/needs-victor-matrix" python3 -B -I test_needs_victor.py "$LIVEBASE"
block "unmodified matrix on the candidate (the per-ask occurrence suffix alone differs)" "$LANE/repair-r2/needs-victor-matrix" python3 -B -I test_needs_victor.py "$W/src/sats_stall_asks.py"
block "suite copy (tests/needs_victor) on the candidate" "$W/tests/needs_victor" python3 -B -I test_needs_victor.py "$W/src/sats_stall_asks.py"
block "suite copy (tests/needs_victor) on round-1 a31f46b (must fail)" "$W/tests/needs_victor" python3 -B -I test_needs_victor.py "$PRE/tools/sats-stall-watchdog/src/sats_stall_asks.py"

echo "## 3. victor-vault tools/sats-stall-watchdog (canon-clone, item 4)"
echo
echo "Staged, not pushed: \`$(git -C "$LANE/canon-clone" log --format='%h %s' origin/main..HEAD | tr '\n' ';' | sed 's/;/; /g')\`"
echo
echo "4a02910 is an ancestor of HEAD: $(git -C "$LANE/canon-clone" merge-base --is-ancestor 4a02910 HEAD && echo yes || echo NO). origin/main is an ancestor (the push fast-forwards): $(git -C "$LANE/canon-clone" merge-base --is-ancestor origin/main HEAD && echo yes || echo NO)."
echo
block "vault suite at HEAD (catch-up + items 1, 5, 6, round-2 repairs)" "$LANE/canon-clone/tools/sats-stall-watchdog" python3 -m unittest discover -s tests -p 'test_*.py'
for m in sats_stall_asks.py sats_stall_watchdog.py; do
  echo "Vault \`src/$m\` equals the candidate: $(cmp -s "$LANE/canon-clone/tools/sats-stall-watchdog/src/$m" "$W/src/$m" && echo yes || echo NO)."
done
echo

echo "## 4. Migration and install rehearsals"
echo
cp "$DBCOPY" "$RUN/asks-rehearse.sqlite3"
block "migration up and down on a copy of the live asks.sqlite3 (23:35, one BLOCKED:<digest> row)" "$CAND" python3 -I install/events_migration.py --lib tools/sats-stall-watchdog/src rehearse "$RUN/asks-rehearse.sqlite3"
block "install and rollback in a sandbox HOME on the cb8a6cc0 live base" "$CAND" bash install/rehearse.sh "$RUN/rehearsal" \
  "$DBCOPY" "$LANE/evidence/requeue-copy"
RCA=/home/victor/.t3-nightly/worktrees/t3code-fork/grokbot-fd-master-fix-20261023/lanes/fd-master-fix-20261023/notice-delay-rca-20261023
block "RCA patch-1 behavior check (check_done.py, Kimi included) on the candidate module" "$CAND" python3 -B -I "$RCA/.stage/check_done.py" "$W/src/sats_stall_asks.py" "$W/src"
block "RCA patch-1 tick check (check_tick.py --staged) on the candidate module" "$CAND" python3 -B -I "$RCA/.stage/check_tick.py" "$W/src/sats_stall_asks.py" "$W/src" --staged
block "shellcheck" "$CAND" shellcheck -S warning install/install.sh install/rollback.sh install/rehearse.sh install/receipts.sh
block "systemd-analyze verify" "$CAND" systemd-analyze --user verify notify/systemd/sats-completion-requeue.service notify/systemd/sats-completion-requeue.timer

echo "## 5. Live state untouched by this phase"
echo
echo '```'
for f in "$HOME/.local/lib/sats-stall-watchdog/sats_stall_asks.py" "$HOME/.local/lib/sats-stall-watchdog/sats_stall_asks.py.bak-needs-victor-20261023T225552" \
         "$HOME/.local/lib/sats-stall-watchdog/sats_stall_watchdog.py" "$HOME/.local/bin/sats-completion-notify" \
         "$HOME/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py"; do sha256sum "$f"; done
units=("$HOME"/.config/systemd/user/sats-completion-requeue.*); [ -e "${units[0]}" ] && echo "requeue unit files on F-D: ${#units[@]}" || echo "requeue unit files on F-D: 0"
python3 -I -c 'import hashlib, json, sys
from pathlib import Path
m = json.load(open(sys.argv[1])); rq = Path(m["directory"])
live = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in rq.glob("*.json")}
print("requeue entries: %d, all matching the triage sha256: %s" % (len(live), live == {e["file"]: e["sha256"] for e in m["entries"]}))' "$CAND/install/requeue-triage.json"
sqlite3 -readonly "file:$HOME/.local/state/sats-stall-watchdog/asks.sqlite3?mode=ro" "SELECT 'live events schema: ' || sql FROM sqlite_master WHERE name='events'"
ls "$HOME"/.local/lib/sats-stall-watchdog/*.bak-notice-package-* 2>/dev/null | sed 's/^/notice-package backup present: /' || true
echo '```'
