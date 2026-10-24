# Receipts: notice-package-20261023 candidate

Generated 2026-10-23 21:36 CDT on framework-desktop by `install/receipts.sh`. Candidate HEAD tested:
`1f69e4b0c44fb987236c60f6171053d336e80e94`. Raw outputs: `candidate/.tmp-run/receipts/`.

Two failures recur in every run of the frozen suite, base included:
`test_bad_delivery_data_does_not_hide_a_live_lane` and `test_real_collector_excludes_terminal_pending_approval_and_child`.
`sats_stall_collector.discover()` (unchanged, 1a5acf4a) rejects lane roots outside `~/work`
(`root-scope-rejected`). This lane lives under `~/.t3-nightly/scratch`, and the 2026-10-20 run passed from `~/work`.

## Summary

| Check | Result |
|---|---|
| Watchdog suite on the candidate | 135 run, 133 pass; the 2 failures are the location-bound collector tests above, failing identically on the base |
| Notifier item 7 tests on the candidate | 7 of 7 pass |
| Patch 2 guard tests on the candidate | 5 of 5 pass |
| New watchdog tests on live asks 406e3fd9 | 23 of 25 fail or error, as they must; the 2 that pass are guards that hold on both: no DONE when a BLOCKED follows, and the static no-VACUUM check |
| Item 7 tests on live notifier ad1f0106 | 6 of 7 fail or error; the unit-file test passes on both |
| Patch 2 tests on live mcp_call.py d1bb0937 | the guard is absent (1 fail, 4 skipped) |
| Frozen live suite on the live base (reference) | 103 run, the same 2 location-bound failures |
| victor-vault suite at the staged HEAD | 125 run, the same 2 location-bound failures; vault `sats_stall_asks.py` equals the candidate |
| Migration rehearsal on a copy of the live asks.sqlite3 | up then down, 289 events kept byte for byte, round trip identical |
| Install and rollback in a sandbox HOME | 11 of 11 checks pass |
| shellcheck, systemd-analyze verify | clean |
| Live state | bases unchanged, no requeue units, 25 requeue entries matching the triage, events schema unchanged |

A live bug the base run shows: `test_negations_and_reports_do_not_match` fails on 406e3fd9 for "not BLOCKED anymore /x"
and "Not BLOCKED: the key arrived and the push went out.". The live `BLOCKED_LINE_RE` takes "not" as its one-word
prefix, so a negated final line is a BLOCKED today. Item 5's negation guard fixes it.

Commits after the tested HEAD add only this file (`git diff <tested HEAD>..HEAD --stat`).

## 1. Candidate suites

### watchdog suite, candidate

`cd candidate/tools/sats-stall-watchdog && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
1 FAIL: test_bad_delivery_data_does_not_hide_a_live_lane (test_delivery_checkins.DeliveryCheckinTests.test_bad_delivery_data_does_not_hide_a_live_lane)
1 FAIL: test_real_collector_excludes_terminal_pending_approval_and_child (test_watchdog_route.CallerTests.test_real_collector_excludes_terminal_pending_approval_and_child)
----------------------------------------------------------------------
Ran 135 tests in 21.967s

FAILED (failures=2)
```

### notifier item 7, candidate

`cd candidate/notify && python3 -m unittest discover -s tests -p test_*.py` → exit 0

```
----------------------------------------------------------------------
Ran 7 tests in 0.141s

OK
```

### mcp_call patch 2, candidate

`cd candidate/mcp && python3 -m unittest discover -s tests -p test_*.py` → exit 0

```
----------------------------------------------------------------------
Ran 5 tests in 0.013s

OK
```

## 2. The same new tests against the unpatched live bases (must fail)

### new watchdog tests on live asks 406e3fd9

`cd candidate/.tmp-run/receipts/base-watchdog/tools/sats-stall-watchdog/tests && python3 -m unittest test_asks.DoneTriggerTests test_asks.MarkersAnywhereTests test_asks.PerAskTests test_asks.EventsMigrationTests test_generations.EventTests.test_done_once_on_the_done_reply_never_on_settle test_generations.EventTests.test_a_status_line_that_leads_with_done_is_the_generations_done test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none` → exit 1

```
1 ERROR: test_7237c08a_inline_blocked_is_an_ask_and_its_settle_sends_no_done (test_asks.MarkersAnywhereTests.test_7237c08a_inline_blocked_is_an_ask_and_its_settle_sends_no_done)
1 ERROR: test_closed_as_blocked_mbp_64539631 (test_asks.MarkersAnywhereTests.test_closed_as_blocked_mbp_64539631)
1 ERROR: test_downgrade_parks_per_ask_rows_and_the_old_watchdog_runs_on_both_schemas (test_asks.EventsMigrationTests.test_downgrade_parks_per_ask_rows_and_the_old_watchdog_runs_on_both_schemas)
1 ERROR: test_fenced_asks_mbp_64539631 (test_asks.MarkersAnywhereTests.test_fenced_asks_mbp_64539631)
1 ERROR: test_inline_bold_blocked_fd_7237c08a (test_asks.MarkersAnywhereTests.test_inline_bold_blocked_fd_7237c08a)
1 ERROR: test_markers_inside_inline_code_and_fences (test_asks.MarkersAnywhereTests.test_markers_inside_inline_code_and_fences)
1 ERROR: test_upgrade_keeps_every_row_and_downgrade_restores_the_old_schema (test_asks.EventsMigrationTests.test_upgrade_keeps_every_row_and_downgrade_restores_the_old_schema)
1 FAIL: test_5a44357c_t01_and_24285_each_send (test_asks.PerAskTests.test_5a44357c_t01_and_24285_each_send)
1 FAIL: test_a_failed_upgrade_changes_nothing (test_asks.EventsMigrationTests.test_a_failed_upgrade_changes_nothing)
1 FAIL: test_an_ask_sent_under_the_old_key_is_not_sent_again_after_the_upgrade (test_asks.PerAskTests.test_an_ask_sent_under_the_old_key_is_not_sent_again_after_the_upgrade)
1 FAIL: test_a_status_line_that_leads_with_done_is_the_generations_done (test_generations.EventTests.test_a_status_line_that_leads_with_done_is_the_generations_done)
1 FAIL: test_c95235ec_generation_4_sends_four (test_asks.PerAskTests.test_c95235ec_generation_4_sends_four)
1 FAIL: test_decision_for_you_is_an_ask_c95235ec (test_asks.MarkersAnywhereTests.test_decision_for_you_is_an_ask_c95235ec)
1 FAIL: test_decision_for_you_sends_a_blocked_c95235ec (test_asks.MarkersAnywhereTests.test_decision_for_you_sends_a_blocked_c95235ec)
1 FAIL: test_done_inside_the_grace_is_reread_once_and_claimed (test_asks.DoneTriggerTests.test_done_inside_the_grace_is_reread_once_and_claimed)
1 FAIL: test_done_once_on_the_done_reply_never_on_settle (test_generations.EventTests.test_done_once_on_the_done_reply_never_on_settle)
1 FAIL: test_fd_7237c08a_three_asks_and_no_done_on_settle (test_asks.PerAskTests.test_fd_7237c08a_three_asks_and_no_done_on_settle)
1 FAIL: test_mbp_64539631_fenced_asks_and_close_out_are_two_asks (test_asks.PerAskTests.test_mbp_64539631_fenced_asks_and_close_out_are_two_asks)
1 FAIL: test_needs_victor_then_a_different_blocked_line_are_two_asks (test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks)
1 FAIL: test_negated_lead_and_settle_alone_send_no_done (test_asks.DoneTriggerTests.test_negated_lead_and_settle_alone_send_no_done)
1 FAIL: test_negations_and_reports_do_not_match (test_asks.MarkersAnywhereTests.test_negations_and_reports_do_not_match) (text='not BLOCKED anymore /x')
1 FAIL: test_negations_and_reports_do_not_match (test_asks.MarkersAnywhereTests.test_negations_and_reports_do_not_match) (text='Not BLOCKED: the key arrived and the push went out.')
1 FAIL: test_start_and_done_stay_one_per_generation (test_asks.PerAskTests.test_start_and_done_stay_one_per_generation)
1 FAIL: test_two_asks_are_two_hook_notices_and_a_repeat_is_none (test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none)
----------------------------------------------------------------------
Ran 25 tests in 1.615s

FAILED (failures=17, errors=7)
```

### notifier item 7 tests on live notifier ad1f0106

`cd candidate/notify && env NOTIFIER_SOURCE=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/base-notify/sats-completion-notify python3 -m unittest discover -s tests -p test_item7.py` → exit 1

```
1 ERROR: test_failed_kick_is_an_error_line_and_never_raises (test_item7.ItemSevenTests.test_failed_kick_is_an_error_line_and_never_raises)
1 ERROR: test_quota_message_keeps_its_counts (test_item7.ItemSevenTests.test_quota_message_keeps_its_counts)
1 FAIL: test_any_error_code_is_kept_whatever_it_is (test_item7.ItemSevenTests.test_any_error_code_is_kept_whatever_it_is)
1 FAIL: test_any_error_code_is_kept_whatever_it_is (test_item7.ItemSevenTests.test_any_error_code_is_kept_whatever_it_is) (expected='429')
1 FAIL: test_any_error_code_is_kept_whatever_it_is (test_item7.ItemSevenTests.test_any_error_code_is_kept_whatever_it_is) (expected='Bad Request')
1 FAIL: test_any_error_code_is_kept_whatever_it_is (test_item7.ItemSevenTests.test_any_error_code_is_kept_whatever_it_is) (expected='E42')
1 FAIL: test_any_error_code_is_kept_whatever_it_is (test_item7.ItemSevenTests.test_any_error_code_is_kept_whatever_it_is) (expected='invalid_request_error')
1 FAIL: test_any_error_code_is_kept_whatever_it_is (test_item7.ItemSevenTests.test_any_error_code_is_kept_whatever_it_is) (expected='not_found')
1 FAIL: test_any_error_code_is_kept_whatever_it_is (test_item7.ItemSevenTests.test_any_error_code_is_kept_whatever_it_is) (expected='unauthorized')
1 FAIL: test_any_error_code_is_kept_whatever_it_is (test_item7.ItemSevenTests.test_any_error_code_is_kept_whatever_it_is) (expected='webhook_not_accepted')
1 FAIL: test_codes_are_bounded_and_scrubbed (test_item7.ItemSevenTests.test_codes_are_bounded_and_scrubbed)
1 FAIL: test_http_error_projection_reaches_the_requeue_log_line (test_item7.ItemSevenTests.test_http_error_projection_reaches_the_requeue_log_line)
----------------------------------------------------------------------
Ran 7 tests in 0.143s

FAILED (failures=10, errors=2)
```

### patch 2 tests on live mcp_call.py d1bb0937

`cd candidate/.tmp-run/receipts/base-mcp && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
1 FAIL: test_guard_exists (test_settle_guard.SettleGuardTests.test_guard_exists)
----------------------------------------------------------------------
Ran 5 tests in 0.001s

FAILED (failures=1, skipped=4)
```

### frozen live suite on live base (reference)

`cd candidate/.tmp-run/receipts/frozen/tools/sats-stall-watchdog && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
1 FAIL: test_bad_delivery_data_does_not_hide_a_live_lane (test_delivery_checkins.DeliveryCheckinTests.test_bad_delivery_data_does_not_hide_a_live_lane)
1 FAIL: test_real_collector_excludes_terminal_pending_approval_and_child (test_watchdog_route.CallerTests.test_real_collector_excludes_terminal_pending_approval_and_child)
----------------------------------------------------------------------
Ran 103 tests in 18.164s

FAILED (failures=2)
```

## 3. victor-vault tools/sats-stall-watchdog (canon-clone, items 4)

Staged, not pushed: `8558a4e canon (proposed, droppable): watchdog asks for notice-package items 5 and 6; 18cc3fd canon: watchdog DONE is the DONE reply, never a settle (notice-package-20261023 item 3); b278b7c tools/sats-stall-watchdog: DONE on the DONE reply, markers anywhere, one BLOCKED per ask; 390f1ff tools/sats-stall-watchdog: catch up to the live F-D install; `

### vault suite at HEAD (catch-up + items 1, 5, 6)

`cd canon-clone/tools/sats-stall-watchdog && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
1 FAIL: test_bad_delivery_data_does_not_hide_a_live_lane (test_delivery_checkins.DeliveryCheckinTests.test_bad_delivery_data_does_not_hide_a_live_lane)
1 FAIL: test_real_collector_excludes_terminal_pending_approval_and_child (test_watchdog_route.CallerTests.test_real_collector_excludes_terminal_pending_approval_and_child)
----------------------------------------------------------------------
Ran 125 tests in 15.802s

FAILED (failures=2)
```

Vault `src/sats_stall_asks.py` equals the candidate: yes.

## 4. Migration and install rehearsals

### migration up and down on a copy of the live asks.sqlite3

`cd candidate && python3 -I install/events_migration.py --lib tools/sats-stall-watchdog/src rehearse /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/asks-rehearse.sqlite3` → exit 0

```
  "ok": true,
  "parked": 0
 }
}
```

### install and rollback in a sandbox HOME

`cd candidate && bash install/rehearse.sh /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/evidence/asks-copy-20261023T204626.sqlite3 /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/evidence/requeue-copy` → exit 0

```
PASS rollback restores the bases
PASS rollback restores the events schema and rows
PASS rollback removed the units into the record
PASS rollback systemctl calls
```

### shellcheck

`cd candidate && shellcheck -S warning install/install.sh install/rollback.sh install/rehearse.sh install/receipts.sh` → exit 0

```
```

### systemd-analyze verify

`cd candidate && systemd-analyze --user verify notify/systemd/sats-completion-requeue.service notify/systemd/sats-completion-requeue.timer` → exit 0

```
```

## 5. Live state untouched by this phase

```
406e3fd97579e823f67d27f4e02f4b81cab11a720f39df8ff5bb7e2af16a0a22  /home/victor/.local/lib/sats-stall-watchdog/sats_stall_asks.py
ad1f0106f6f8d0fad97067d7fa2807bd41c9991af5c9fc12adae91b45fc1ae62  /home/victor/.local/bin/sats-completion-notify
d1bb0937f00685989da4debf547fa2bcc5675226d695f78a471ba08c4eb7e4e7  /home/victor/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py
requeue unit files on F-D: 0
requeue entries: 25, all matching the triage sha256: True
live events schema: CREATE TABLE events (id TEXT PRIMARY KEY, thread TEXT NOT NULL, generation INTEGER NOT NULL, state TEXT NOT NULL, data TEXT NOT NULL, UNIQUE (thread, generation, state))
```
