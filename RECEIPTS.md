# Receipts: notice-package-20261023 candidate

Generated 2026-10-23 22:44 CDT on framework-desktop by `install/receipts.sh`. Candidate HEAD tested:
`d719668619d3d171ba01c35aee5fc7e3682fdc08`. Raw outputs: `candidate/.tmp-run/receipts/`.

Two failures recur in every run of the frozen suite, base included:
`test_bad_delivery_data_does_not_hide_a_live_lane` and `test_real_collector_excludes_terminal_pending_approval_and_child`.
`sats_stall_collector.discover()` (unchanged, 1a5acf4a) rejects lane roots outside `~/work`
(`root-scope-rejected`). This lane lives under `~/.t3-nightly/scratch`, and the 2026-10-20 run passed from `~/work`.

## Summary (round-1 repair)

| Check | Result |
|---|---|
| Watchdog suite on the candidate | 146 run, 144 pass; the 2 failures are the location-bound collector tests above, failing identically on the base |
| Notifier item 7 tests on the candidate | 7 of 7 pass |
| Settle guard tests on the candidate (patch 2, SOL-5, SOL-6) | 8 of 8 pass |
| Install gate and replay recheck tests (DS-H1, SOL-7) | 7 of 7 pass |
| Round-1 watchdog tests on round-0 e6a95f42 | all 11 fail or error, as they must (SOL-1, DS-H2, SOL-2, SOL-3, SOL-4, DS-M2, DS-M3) |
| Round-1 settle guard tests on round-0 mcp_call.py b1959e29 | all 3 fail or error, as they must (SOL-5, SOL-6) |
| Rehearsal with the round-0 scripts, systemd-259 shim | the gate never passes (DS-H1): the dry run, install and rollback all stop at it |
| Rehearsal with the round-0 scripts past their old gate | the answered ask stays queued (SOL-7); the rollback of a resumed install leaves `sats_stall_asks.py` at the candidate (SOL-8) |
| Rehearsal with the repaired scripts (main, answered, resume) | 20 of 20 checks pass |
| RCA patch-1 checks on the candidate module | check_done.py: Kimi sends DONE once its turn ends and the other 5 cases match the RCA table; check_tick.py `--staged` passes |
| Round-0 tests on the live bases (reference) | still fail there, as in round 0 |
| victor-vault suite at the staged HEAD | 136 run, the same 2 location-bound failures; vault `sats_stall_asks.py` and `sats_stall_watchdog.py` equal the candidate |
| Migration rehearsal on a copy of the live asks.sqlite3 | up then down, round trip identical |
| shellcheck, systemd-analyze verify | clean |
| Live state | all four live files at their bases, no requeue units, 25 requeue entries matching the triage, events schema unchanged |

Commits after the tested HEAD add only this file (`git diff <tested HEAD>..HEAD --stat`).

## 1. Candidate suites

### watchdog suite, candidate

`cd candidate/tools/sats-stall-watchdog && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
........................................................................F....../home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src/sats_stall_mcp.py:117: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7f92cb7cd030>
  if not isinstance(rows, list) or not all(isinstance(x, dict) for x in rows):
ResourceWarning: Enable tracemalloc to get the object allocation traceback
.........................................................F.........
======================================================================
FAIL: test_bad_delivery_data_does_not_hide_a_live_lane (test_delivery_checkins.DeliveryCheckinTests.test_bad_delivery_data_does_not_hide_a_live_lane)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/tests/test_delivery_checkins.py", line 111, in test_bad_delivery_data_does_not_hide_a_live_lane
    self.assertEqual(len(result['lanes']), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 1

======================================================================
FAIL: test_real_collector_excludes_terminal_pending_approval_and_child (test_watchdog_route.CallerTests.test_real_collector_excludes_terminal_pending_approval_and_child)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/tests/test_watchdog_route.py", line 170, in test_real_collector_excludes_terminal_pending_approval_and_child
    self.assertEqual(len(collector.discover(config)['lanes']), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 1

----------------------------------------------------------------------
Ran 146 tests in 14.453s

FAILED (failures=2)
```

### notifier item 7, candidate

`cd candidate/notify && python3 -m unittest discover -s tests -p test_*.py` → exit 0

```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.096s

OK
```

### mcp_call patch 2, candidate

`cd candidate/mcp && python3 -m unittest discover -s tests -p test_*.py` → exit 0

```
........
----------------------------------------------------------------------
Ran 8 tests in 0.024s

OK
```

### install gate and replay recheck, candidate

`cd candidate/install && python3 -m unittest discover -s tests -p test_*.py` → exit 0

```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.398s

OK
```

## 2. The same new tests against the unpatched live bases (must fail)

### new watchdog tests on live asks 406e3fd9

`cd candidate/.tmp-run/receipts/base-watchdog/tools/sats-stall-watchdog/tests && python3 -m unittest test_asks.DoneTriggerTests test_asks.MarkersAnywhereTests test_asks.PerAskTests test_asks.EventsMigrationTests test_generations.EventTests.test_done_once_on_the_done_reply_never_on_settle test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none` → exit 1

```
1 ERROR: test_7237c08a_inline_blocked_is_an_ask_and_its_settle_sends_no_done (test_asks.MarkersAnywhereTests.test_7237c08a_inline_blocked_is_an_ask_and_its_settle_sends_no_done)
1 ERROR: test_closed_as_blocked_mbp_64539631 (test_asks.MarkersAnywhereTests.test_closed_as_blocked_mbp_64539631)
1 ERROR: test_downgrade_parks_per_ask_rows_and_the_old_watchdog_runs_on_both_schemas (test_asks.EventsMigrationTests.test_downgrade_parks_per_ask_rows_and_the_old_watchdog_runs_on_both_schemas)
1 ERROR: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='This needs a decision from **Victor**: which key?')
1 ERROR: test_fenced_asks_mbp_64539631 (test_asks.MarkersAnywhereTests.test_fenced_asks_mbp_64539631)
1 ERROR: test_inline_bold_blocked_fd_7237c08a (test_asks.MarkersAnywhereTests.test_inline_bold_blocked_fd_7237c08a)
1 ERROR: test_markers_inside_inline_code_and_fences (test_asks.MarkersAnywhereTests.test_markers_inside_inline_code_and_fences)
1 ERROR: test_upgrade_keeps_every_row_and_downgrade_restores_the_old_schema (test_asks.EventsMigrationTests.test_upgrade_keeps_every_row_and_downgrade_restores_the_old_schema)
1 FAIL: test_5a44357c_t01_and_24285_each_send (test_asks.PerAskTests.test_5a44357c_t01_and_24285_each_send)
1 FAIL: test_a_failed_upgrade_changes_nothing (test_asks.EventsMigrationTests.test_a_failed_upgrade_changes_nothing)
1 FAIL: test_an_ask_sent_under_the_old_key_is_not_sent_again_after_the_upgrade (test_asks.PerAskTests.test_an_ask_sent_under_the_old_key_is_not_sent_again_after_the_upgrade)
1 FAIL: test_c95235ec_generation_4_sends_four (test_asks.PerAskTests.test_c95235ec_generation_4_sends_four)
1 FAIL: test_decision_for_you_is_an_ask_c95235ec (test_asks.MarkersAnywhereTests.test_decision_for_you_is_an_ask_c95235ec)
1 FAIL: test_decision_for_you_sends_a_blocked_c95235ec (test_asks.MarkersAnywhereTests.test_decision_for_you_sends_a_blocked_c95235ec)
1 FAIL: test_done_inside_the_grace_is_reread_once_and_claimed (test_asks.DoneTriggerTests.test_done_inside_the_grace_is_reread_once_and_claimed)
1 FAIL: test_done_once_on_the_done_reply_never_on_settle (test_generations.EventTests.test_done_once_on_the_done_reply_never_on_settle)
1 FAIL: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='A decision from Victor is needed before the push.')
1 FAIL: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='**C14 needs a decision from you.** The repair found no maintained hub client.')
1 FAIL: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='**Decision for you:** may P03 have a 4th review round?')
1 FAIL: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='**Decisions for Victor:** pick A or B.')
1 FAIL: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='- **Two decisions for you:**')
1 FAIL: test_DSM3_a_per_ask_only_generation_downgrades_to_the_legacy_key (test_asks.EventsMigrationTests.test_DSM3_a_per_ask_only_generation_downgrades_to_the_legacy_key)
1 FAIL: test_DSM3_the_old_module_on_the_per_ask_schema_can_send_a_second_blocked (test_asks.EventsMigrationTests.test_DSM3_the_old_module_on_the_per_ask_schema_can_send_a_second_blocked)
1 FAIL: test_fd_7237c08a_three_asks_and_no_done_on_settle (test_asks.PerAskTests.test_fd_7237c08a_three_asks_and_no_done_on_settle)
1 FAIL: test_mbp_64539631_fenced_asks_and_close_out_are_two_asks (test_asks.PerAskTests.test_mbp_64539631_fenced_asks_and_close_out_are_two_asks)
1 FAIL: test_needs_victor_then_a_different_blocked_line_are_two_asks (test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks)
1 FAIL: test_negated_lead_and_settle_alone_send_no_done (test_asks.DoneTriggerTests.test_negated_lead_and_settle_alone_send_no_done)
1 FAIL: test_negations_and_reports_do_not_match (test_asks.MarkersAnywhereTests.test_negations_and_reports_do_not_match) (text='not BLOCKED anymore /x')
1 FAIL: test_negations_and_reports_do_not_match (test_asks.MarkersAnywhereTests.test_negations_and_reports_do_not_match) (text='Not BLOCKED: the key arrived and the push went out.')
1 FAIL: test_start_and_done_stay_one_per_generation (test_asks.PerAskTests.test_start_and_done_stay_one_per_generation)
1 FAIL: test_two_asks_are_two_hook_notices_and_a_repeat_is_none (test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none)
----------------------------------------------------------------------
Ran 27 tests in 0.954s

FAILED (failures=23, errors=8)
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
Ran 7 tests in 0.306s

FAILED (failures=10, errors=2)
```

### patch 2 tests on live mcp_call.py d1bb0937

`cd candidate/.tmp-run/receipts/base-mcp && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
sssssFss
======================================================================
FAIL: test_guard_exists (test_settle_guard.SettleGuardTests.test_guard_exists)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/base-mcp/tests/test_settle_guard.py", line 76, in test_guard_exists
    self.assertTrue(callable(guard), 'mcp_call.py has no sweep_settle_refusal')
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : mcp_call.py has no sweep_settle_refusal

----------------------------------------------------------------------
Ran 8 tests in 0.001s

FAILED (failures=1, skipped=7)
```

### frozen live suite on live base (reference)

`cd candidate/.tmp-run/receipts/frozen/tools/sats-stall-watchdog && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
...............................................F.............................................F.........
======================================================================
FAIL: test_bad_delivery_data_does_not_hide_a_live_lane (test_delivery_checkins.DeliveryCheckinTests.test_bad_delivery_data_does_not_hide_a_live_lane)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/frozen/tools/sats-stall-watchdog/tests/test_delivery_checkins.py", line 111, in test_bad_delivery_data_does_not_hide_a_live_lane
    self.assertEqual(len(result['lanes']), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 1

======================================================================
FAIL: test_real_collector_excludes_terminal_pending_approval_and_child (test_watchdog_route.CallerTests.test_real_collector_excludes_terminal_pending_approval_and_child)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/frozen/tools/sats-stall-watchdog/tests/test_watchdog_route.py", line 170, in test_real_collector_excludes_terminal_pending_approval_and_child
    self.assertEqual(len(collector.discover(config)['lanes']), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 1

----------------------------------------------------------------------
Ran 103 tests in 10.492s

FAILED (failures=2)
```

## 2b. Review round-1 tests against the round-0 candidate e6a95f42 (must fail)

### round-1 watchdog tests on e6a95f42 (asks 8772ee0b, watchdog 6ea2e6fb)

`cd candidate/.tmp-run/receipts/round0/tools/sats-stall-watchdog/tests && python3 -m unittest test_generations.EventTests.test_SOL1_a_done_led_progress_line_then_a_final_progress_reply_sends_no_done test_generations.EventTests.test_SOL1_kimi_replies_that_restate_done_keep_it_on_the_done_replys_run test_generations.EventTests.test_DSH2_single_read_message_after_a_done_reply_opens_a_generation test_generations.EventTests.test_DSH2_grace_reread_message_after_a_done_reply_opens_a_generation test_generations.EventTests.test_DSH2_a_follow_up_inside_the_done_replys_grace_claims_that_done_after_the_grace test_asks.ThreadNoticeTests.test_SOL2_a_delivered_turn_notice_covers_only_the_asks_it_carried test_generations.RepairRound1Tests test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send test_asks.EventsMigrationTests.test_DSM3_a_per_ask_only_generation_downgrades_to_the_legacy_key` → exit 1

```
1 ERROR: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='This needs a decision from **Victor**: which key?')
1 FAIL: test_DSH2_a_follow_up_inside_the_done_replys_grace_claims_that_done_after_the_grace (test_generations.EventTests.test_DSH2_a_follow_up_inside_the_done_replys_grace_claims_that_done_after_the_grace)
1 FAIL: test_DSH2_grace_reread_message_after_a_done_reply_opens_a_generation (test_generations.EventTests.test_DSH2_grace_reread_message_after_a_done_reply_opens_a_generation)
1 FAIL: test_DSH2_single_read_message_after_a_done_reply_opens_a_generation (test_generations.EventTests.test_DSH2_single_read_message_after_a_done_reply_opens_a_generation)
1 FAIL: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='**Decision from Victor:** GO on P05.')
1 FAIL: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='Decision from you: approved at 21:40.')
1 FAIL: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='**Decisions from Victor** are in DECISIONS-CURRENT.md.')
1 FAIL: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='Decisions from Victor: A, then B.')
1 FAIL: test_DSM3_a_per_ask_only_generation_downgrades_to_the_legacy_key (test_asks.EventsMigrationTests.test_DSM3_a_per_ask_only_generation_downgrades_to_the_legacy_key)
1 FAIL: test_SOL1_a_done_led_progress_line_then_a_final_progress_reply_sends_no_done (test_generations.EventTests.test_SOL1_a_done_led_progress_line_then_a_final_progress_reply_sends_no_done)
1 FAIL: test_SOL1_kimi_replies_that_restate_done_keep_it_on_the_done_replys_run (test_generations.EventTests.test_SOL1_kimi_replies_that_restate_done_keep_it_on_the_done_replys_run)
1 FAIL: test_SOL2_a_delivered_turn_notice_covers_only_the_asks_it_carried (test_asks.ThreadNoticeTests.test_SOL2_a_delivered_turn_notice_covers_only_the_asks_it_carried)
1 FAIL: test_SOL3_a_pending_ask_whose_completed_text_asks_nothing_stays_local (test_generations.RepairRound1Tests.test_SOL3_a_pending_ask_whose_completed_text_asks_nothing_stays_local)
1 FAIL: test_SOL3_a_streamed_decision_id_line_that_completes_as_decision_for_you_sends (test_generations.RepairRound1Tests.test_SOL3_a_streamed_decision_id_line_that_completes_as_decision_for_you_sends)
1 FAIL: test_SOL4_a_reworded_ask_with_the_same_decision_id_is_one_notice (test_generations.RepairRound1Tests.test_SOL4_a_reworded_ask_with_the_same_decision_id_is_one_notice)
----------------------------------------------------------------------
Ran 11 tests in 0.511s

FAILED (failures=14, errors=1)
```

### round-1 settle guard tests on e6a95f42 mcp_call.py b1959e29

`cd candidate/.tmp-run/receipts/round0/mcp && env WATCHDOG_SRC=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src python3 -m unittest tests.test_settle_guard.SettleGuardTests.test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses tests.test_settle_guard.SettleGuardTests.test_SOL5_missing_watchdog_detection_refuses tests.test_settle_guard.SettleGuardTests.test_SOL6_a_required_reviewer_without_accept_refuses` → exit 1

```
1 ERROR: test_SOL5_missing_watchdog_detection_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL5_missing_watchdog_detection_refuses)
1 FAIL: test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses)
1 FAIL: test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses) [closed as BLOCKED]
1 FAIL: test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses) [decision for you]
1 FAIL: test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses) [decision from you, ask shape]
1 FAIL: test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL5_every_watchdog_ask_form_from_the_done_reply_on_refuses) [inline bold BLOCKED]
1 FAIL: test_SOL6_a_required_reviewer_without_accept_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL6_a_required_reviewer_without_accept_refuses) [BLOCKED peer]
1 FAIL: test_SOL6_a_required_reviewer_without_accept_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL6_a_required_reviewer_without_accept_refuses) [newest review BLOCKED]
1 FAIL: test_SOL6_a_required_reviewer_without_accept_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL6_a_required_reviewer_without_accept_refuses) [peer run failed]
1 FAIL: test_SOL6_a_required_reviewer_without_accept_refuses (tests.test_settle_guard.SettleGuardTests.test_SOL6_a_required_reviewer_without_accept_refuses) [peer with no reply]
----------------------------------------------------------------------
Ran 3 tests in 0.029s

FAILED (failures=9, errors=1)
```

### rehearsal with the e6a95f42 install.sh and rollback.sh, systemd-259 shim (DS-H1)

`cd candidate && env REHEARSE_SCRIPTS=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/round0/install-scripts bash install/rehearse.sh /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal-round0-259 /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/evidence/asks-copy-20261023T204626.sqlite3 /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/evidence/requeue-copy` → exit 1

```
FAIL main: dry run passes the gate on a monotonic timer (DS-H1)
PASS main: dry run changes nothing
FAIL main: install exits 0
FAIL main: files are the candidate
FAIL main: backups are the bases
FAIL main: migration up ok
FAIL main: the unanswered replay is rechecked and stays queued (SOL-7)
ls: cannot access '/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal-round0-259/main/home/.local/state/sats-completion/requeue-archive-*/': No such file or directory
FAIL main: archived entries kept with a manifest
PASS main: systemctl touched only the requeue units
FAIL main: rollback exits 0 past the gate
PASS main: rollback restores the bases
PASS main: rollback restores the events schema and rows
FAIL main: rollback removed the units into the record
PASS main: rollback systemctl calls
FAIL answered: an ask answered since the triage is archived, not replayed (SOL-7)
FAIL answered: the record names the answered entry
FAIL resume: the resumed install completes
FAIL resume: the original asks backup is kept and recorded (SOL-8)
FAIL resume: rollback of the resumed install restores every base, asks included (SOL-8)
PASS resume: rollback of the resumed install restores the events schema
```

### rehearsal with the e6a95f42 scripts past their gate, old realtime shim (SOL-7, SOL-8)

`cd candidate && env SHIM_REALTIME=1 REHEARSE_SCRIPTS=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/round0/install-scripts bash install/rehearse.sh /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal-round0-realtime /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/evidence/asks-copy-20261023T204626.sqlite3 /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/evidence/requeue-copy` → exit 1

```
FAIL main: dry run passes the gate on a monotonic timer (DS-H1)
PASS main: dry run changes nothing
PASS main: install exits 0
FAIL main: files are the candidate
sha256sum: /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal-round0-realtime/main/install-record-20261023T224508/watchdog.bak: No such file or directory
FAIL main: backups are the bases
PASS main: migration up ok
FAIL main: the unanswered replay is rechecked and stays queued (SOL-7)
PASS main: archived entries kept with a manifest
PASS main: systemctl touched only the requeue units
PASS main: rollback exits 0 past the gate
PASS main: rollback restores the bases
PASS main: rollback restores the events schema and rows
PASS main: rollback removed the units into the record
PASS main: rollback systemctl calls
FAIL answered: an ask answered since the triage is archived, not replayed (SOL-7)
grep: /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal-round0-realtime/answered/install-record-20261023T224509/replay-recheck.json: No such file or directory
FAIL answered: the record names the answered entry
FAIL resume: the resumed install completes
sha256sum: /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal-round0-realtime/resume/install-record-20261023T224509/asks.bak: No such file or directory
FAIL resume: the original asks backup is kept and recorded (SOL-8)
FAIL resume: rollback of the resumed install restores every base, asks included (SOL-8)
PASS resume: rollback of the resumed install restores the events schema
```

Asks after the round-0 rollback of a resumed install: `f68b5e47c110e3bf` (the candidate; base is 406e3fd9).

## 3. victor-vault tools/sats-stall-watchdog (canon-clone, items 4)

Staged, not pushed: `0fad1e3 canon (proposed with D): each ask decided on its own;  the DONE reply is the final reply; e131c2d tools/sats-stall-watchdog: notice-package round-1 repairs (equals the candidate); 8558a4e canon (proposed, droppable): watchdog asks for notice-package items 5 and 6; 18cc3fd canon: watchdog DONE is the DONE reply, never a settle (notice-package-20261023 item 3); b278b7c tools/sats-stall-watchdog: DONE on the DONE reply, markers anywhere, one BLOCKED per ask; 390f1ff tools/sats-stall-watchdog: catch up to the live F-D install; `

### vault suite at HEAD (catch-up + items 1, 5, 6)

`cd canon-clone/tools/sats-stall-watchdog && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
........................................................................F....../usr/lib64/python3.14/json/encoder.py:254: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7f7a45329c60>
  _iterencode = c_make_encoder(
ResourceWarning: Enable tracemalloc to get the object allocation traceback
...............................................F.........
======================================================================
FAIL: test_bad_delivery_data_does_not_hide_a_live_lane (test_delivery_checkins.DeliveryCheckinTests.test_bad_delivery_data_does_not_hide_a_live_lane)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/canon-clone/tools/sats-stall-watchdog/tests/test_delivery_checkins.py", line 111, in test_bad_delivery_data_does_not_hide_a_live_lane
    self.assertEqual(len(result['lanes']), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 1

======================================================================
FAIL: test_real_collector_excludes_terminal_pending_approval_and_child (test_watchdog_route.CallerTests.test_real_collector_excludes_terminal_pending_approval_and_child)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/canon-clone/tools/sats-stall-watchdog/tests/test_watchdog_route.py", line 170, in test_real_collector_excludes_terminal_pending_approval_and_child
    self.assertEqual(len(collector.discover(config)['lanes']), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 1

----------------------------------------------------------------------
Ran 136 tests in 12.198s

FAILED (failures=2)
```

Vault `src/sats_stall_asks.py` equals the candidate: yes.
Vault `src/sats_stall_watchdog.py` equals the candidate: yes.

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
PASS main: dry run passes the gate on a monotonic timer (DS-H1)
PASS main: dry run changes nothing
PASS main: install exits 0
PASS main: files are the candidate
PASS main: backups are the bases
PASS main: migration up ok
PASS main: the unanswered replay is rechecked and stays queued (SOL-7)
PASS main: archived entries kept with a manifest
PASS main: systemctl touched only the requeue units
PASS main: rollback exits 0 past the gate
PASS main: rollback restores the bases
PASS main: rollback restores the events schema and rows
PASS main: rollback removed the units into the record
PASS main: rollback systemctl calls
PASS answered: an ask answered since the triage is archived, not replayed (SOL-7)
PASS answered: the record names the answered entry
PASS resume: the resumed install completes
PASS resume: the original asks backup is kept and recorded (SOL-8)
PASS resume: rollback of the resumed install restores every base, asks included (SOL-8)
PASS resume: rollback of the resumed install restores the events schema
```

### RCA patch-1 behavior check (check_done.py, Kimi included) on the candidate module

`cd candidate && python3 -B -I /home/victor/.t3-nightly/worktrees/t3code-fork/grokbot-fd-master-fix-20261023/lanes/fd-master-fix-20261023/notice-delay-rca-20261023/.stage/check_done.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src/sats_stall_asks.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src` → exit 0

```
kimi, unsettled, turn ended                      done={1: True, 2: False, 3: False} marked=[] events=['DONE', 'START']
kimi, turn still running                         done={1: True, 2: False, 3: False} marked=[] events=['START']
4f5dd34b R2 pending, settled                     done={} marked=[] events=['START']
7237c08a reviewed BLOCKED, settled               done={} marked=[1] events=['START']
BLOCKED after DONE                               done={1: True} marked=[2] events=['START']
negated lead                                     done={} marked=[] events=['START']
```

### RCA patch-1 tick check (check_tick.py --staged) on the candidate module

`cd candidate && python3 -B -I /home/victor/.t3-nightly/worktrees/t3code-fork/grokbot-fd-master-fix-20261023/lanes/fd-master-fix-20261023/notice-delay-rca-20261023/.stage/check_tick.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src/sats_stall_asks.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src --staged` → exit 0

```
DONE, first tick inside grace      t+30s reads=1 sent=['generation-1-START'] | t+330s reads=1 sent=['generation-1-DONE'] | t+630s reads=0 sent=[]
DONE, first tick after grace       t+330s reads=1 sent=['generation-1-START', 'generation-1-DONE'] | t+630s reads=0 sent=[]
DONE then BLOCKED, inside grace    t+30s reads=1 sent=['generation-1-START'] | t+330s reads=0 sent=['generation-1-BLOCKED-ask-3631dc26a7e76f10bfd0f537dc128a81'] | t+630s reads=0 sent=[]
no DONE line, inside grace         t+30s reads=1 sent=['generation-1-START'] | t+330s reads=0 sent=[] | t+630s reads=0 sent=[]
staged assertions passed
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
6ea2e6fb3fe1134b0a5f3b99962c2837842b20fda06ce9632e74e206dfa1a06d  /home/victor/.local/lib/sats-stall-watchdog/sats_stall_watchdog.py
ad1f0106f6f8d0fad97067d7fa2807bd41c9991af5c9fc12adae91b45fc1ae62  /home/victor/.local/bin/sats-completion-notify
d1bb0937f00685989da4debf547fa2bcc5675226d695f78a471ba08c4eb7e4e7  /home/victor/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py
requeue unit files on F-D: 0
requeue entries: 25, all matching the triage sha256: True
live events schema: CREATE TABLE events (id TEXT PRIMARY KEY, thread TEXT NOT NULL, generation INTEGER NOT NULL, state TEXT NOT NULL, data TEXT NOT NULL, UNIQUE (thread, generation, state))
```
