# Receipts: notice-package-20261023 candidate

Generated 2026-10-24 00:33 CDT on framework-desktop by `install/receipts.sh`. Candidate HEAD tested:
`de051cff50e9b7e32a3a34997a62bbbe01835672`. Raw outputs: `candidate/.tmp-run/receipts/`.

Two failures recur in every run of the frozen suite, base included:
`test_bad_delivery_data_does_not_hide_a_live_lane` and `test_real_collector_excludes_terminal_pending_approval_and_child`.
`sats_stall_collector.discover()` (unchanged, 1a5acf4a) rejects lane roots outside `~/work`
(`root-scope-rejected`). This lane lives under `~/.t3-nightly/scratch`, and the 2026-10-20 run passed from `~/work`.

The live asks base is cb8a6cc0, the needs-victor fix (2026-10-23 22:55:52 CDT, canon source 4a02910). The
package's first pin, 406e3fd9, is its backup and the candidate's `base` tag; § 2 runs the new tests on both.

## 1. Candidate suites

### watchdog suite, candidate

`cd candidate/tools/sats-stall-watchdog && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
.................<frozen genericpath>:51: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7f74ab1c18a0>
ResourceWarning: Enable tracemalloc to get the object allocation traceback
................................................................F.................................................................F.........
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
Ran 157 tests in 26.189s

FAILED (failures=2)
```

### notifier item 7, candidate

`cd candidate/notify && python3 -m unittest discover -s tests -p test_*.py` → exit 0

```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.129s

OK
```

### mcp_call patch 2, candidate

`cd candidate/mcp && python3 -m unittest discover -s tests -p test_*.py` → exit 0

```
..........
----------------------------------------------------------------------
Ran 10 tests in 0.068s

OK
```

### install gate and replay recheck, candidate

`cd candidate/install && python3 -m unittest discover -s tests -p test_*.py` → exit 0

```
.........
----------------------------------------------------------------------
Ran 9 tests in 1.187s

OK
```

## 2. The package's watchdog tests against the unpatched live bases (must fail)

### package watchdog tests on the live asks cb8a6cc0

`cd candidate/.tmp-run/receipts/base-watchdog-live/tools/sats-stall-watchdog/tests && python3 -m unittest test_asks.DoneTriggerTests test_asks.MarkersAnywhereTests test_asks.PerAskTests test_asks.EventsMigrationTests test_generations.EventTests.test_done_once_on_the_done_reply_never_on_settle test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none test_asks.LiveBaseTests.test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send` → exit 1

```
1 ERROR: test_7237c08a_inline_blocked_is_an_ask_and_its_settle_sends_no_done (test_asks.MarkersAnywhereTests.test_7237c08a_inline_blocked_is_an_ask_and_its_settle_sends_no_done)
1 ERROR: test_closed_as_blocked_mbp_64539631 (test_asks.MarkersAnywhereTests.test_closed_as_blocked_mbp_64539631)
1 ERROR: test_downgrade_parks_per_ask_rows_and_the_old_watchdog_runs_on_both_schemas (test_asks.EventsMigrationTests.test_downgrade_parks_per_ask_rows_and_the_old_watchdog_runs_on_both_schemas)
1 ERROR: test_DSM2_decision_reports_stay_local_and_decision_asks_send (test_asks.MarkersAnywhereTests.test_DSM2_decision_reports_stay_local_and_decision_asks_send) (text='This needs a decision from **Victor**: which key?')
1 ERROR: test_DSM3_a_per_ask_only_generation_downgrades_to_the_legacy_key (test_asks.EventsMigrationTests.test_DSM3_a_per_ask_only_generation_downgrades_to_the_legacy_key)
1 ERROR: test_fenced_asks_mbp_64539631 (test_asks.MarkersAnywhereTests.test_fenced_asks_mbp_64539631)
1 ERROR: test_inline_bold_blocked_fd_7237c08a (test_asks.MarkersAnywhereTests.test_inline_bold_blocked_fd_7237c08a)
1 ERROR: test_markers_inside_inline_code_and_fences (test_asks.MarkersAnywhereTests.test_markers_inside_inline_code_and_fences)
1 ERROR: test_upgrade_keeps_every_row_and_downgrade_restores_the_old_schema (test_asks.EventsMigrationTests.test_upgrade_keeps_every_row_and_downgrade_restores_the_old_schema)
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
1 FAIL: test_DSM3_the_old_module_on_the_per_ask_schema_can_send_a_second_blocked (test_asks.EventsMigrationTests.test_DSM3_the_old_module_on_the_per_ask_schema_can_send_a_second_blocked)
1 FAIL: test_fd_7237c08a_three_asks_and_no_done_on_settle (test_asks.PerAskTests.test_fd_7237c08a_three_asks_and_no_done_on_settle)
1 FAIL: test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send (test_asks.LiveBaseTests.test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send)
1 FAIL: test_mbp_64539631_fenced_asks_and_close_out_are_two_asks (test_asks.PerAskTests.test_mbp_64539631_fenced_asks_and_close_out_are_two_asks)
1 FAIL: test_needs_victor_then_a_different_blocked_line_are_two_asks (test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks)
1 FAIL: test_negated_lead_and_settle_alone_send_no_done (test_asks.DoneTriggerTests.test_negated_lead_and_settle_alone_send_no_done)
1 FAIL: test_negations_and_reports_do_not_match (test_asks.MarkersAnywhereTests.test_negations_and_reports_do_not_match) (text='not BLOCKED anymore /x')
1 FAIL: test_negations_and_reports_do_not_match (test_asks.MarkersAnywhereTests.test_negations_and_reports_do_not_match) (text='Not BLOCKED: the key arrived and the push went out.')
1 FAIL: test_start_and_done_stay_one_per_generation (test_asks.PerAskTests.test_start_and_done_stay_one_per_generation)
1 FAIL: test_two_asks_are_two_hook_notices_and_a_repeat_is_none (test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none)
----------------------------------------------------------------------
Ran 28 tests in 1.596s

FAILED (failures=22, errors=9)
```

### package watchdog tests on the first-pin asks 406e3fd9

`cd candidate/.tmp-run/receipts/base-watchdog-first-pin/tools/sats-stall-watchdog/tests && python3 -m unittest test_asks.DoneTriggerTests test_asks.MarkersAnywhereTests test_asks.PerAskTests test_asks.EventsMigrationTests test_generations.EventTests.test_done_once_on_the_done_reply_never_on_settle test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none test_asks.LiveBaseTests.test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send` → exit 1

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
1 FAIL: test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send (test_asks.LiveBaseTests.test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send)
1 FAIL: test_mbp_64539631_fenced_asks_and_close_out_are_two_asks (test_asks.PerAskTests.test_mbp_64539631_fenced_asks_and_close_out_are_two_asks)
1 FAIL: test_needs_victor_then_a_different_blocked_line_are_two_asks (test_generations.EventTests.test_needs_victor_then_a_different_blocked_line_are_two_asks)
1 FAIL: test_negated_lead_and_settle_alone_send_no_done (test_asks.DoneTriggerTests.test_negated_lead_and_settle_alone_send_no_done)
1 FAIL: test_negations_and_reports_do_not_match (test_asks.MarkersAnywhereTests.test_negations_and_reports_do_not_match) (text='not BLOCKED anymore /x')
1 FAIL: test_negations_and_reports_do_not_match (test_asks.MarkersAnywhereTests.test_negations_and_reports_do_not_match) (text='Not BLOCKED: the key arrived and the push went out.')
1 FAIL: test_start_and_done_stay_one_per_generation (test_asks.PerAskTests.test_start_and_done_stay_one_per_generation)
1 FAIL: test_two_asks_are_two_hook_notices_and_a_repeat_is_none (test_notice_package_hook.InertNoticePackageHook.test_two_asks_are_two_hook_notices_and_a_repeat_is_none)
----------------------------------------------------------------------
Ran 28 tests in 1.210s

FAILED (failures=24, errors=8)
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
Ran 7 tests in 0.117s

FAILED (failures=10, errors=2)
```

### patch 2 tests on live mcp_call.py d1bb0937

`cd candidate/.tmp-run/receipts/base-mcp && env WATCHDOG_SRC=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
sssssssFss
======================================================================
FAIL: test_guard_exists (test_settle_guard.SettleGuardTests.test_guard_exists)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/base-mcp/tests/test_settle_guard.py", line 76, in test_guard_exists
    self.assertTrue(callable(guard), 'mcp_call.py has no sweep_settle_refusal')
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : mcp_call.py has no sweep_settle_refusal

----------------------------------------------------------------------
Ran 10 tests in 0.001s

FAILED (failures=1, skipped=9)
```

### frozen live suite on its own base (reference)

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
Ran 103 tests in 15.460s

FAILED (failures=2)
```

## 2b. Review round-2 tests against the round-1 candidate a31f46b (must fail)

### round-2 watchdog tests on a31f46b (asks f68b5e47)

`cd candidate/.tmp-run/receipts/round1/tools/sats-stall-watchdog/tests && python3 -m unittest test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done test_asks.ThreadNoticeTests.test_SOL2_r2_complete_decision_ids_and_a_phrase_of_one_ask_only test_asks.ScanTests.test_agent_artifacts_after_an_ask_leave_it_open test_asks.LiveBaseTests` → exit 1

```
1 ERROR: test_agent_artifacts_after_an_ask_leave_it_open (test_asks.ScanTests.test_agent_artifacts_after_an_ask_leave_it_open)
1 ERROR: test_LIVE1_artifacts_leave_asks_and_urgent_open_at_find_and_reconcile (test_asks.LiveBaseTests.test_LIVE1_artifacts_leave_asks_and_urgent_open_at_find_and_reconcile)
1 FAIL: test_LIVE1_a_restated_ask_sends_nothing_and_a_new_one_sends_once (test_asks.LiveBaseTests.test_LIVE1_a_restated_ask_sends_nothing_and_a_new_one_sends_once)
1 FAIL: test_LIVE1_a_restated_ask_sends_nothing_and_a_new_one_sends_once (test_asks.LiveBaseTests.test_LIVE1_a_restated_ask_sends_nothing_and_a_new_one_sends_once) (module='candidate', text='NEEDS-VICTOR t1 DECISION-RT-A and DECISION-RT-B are both open /ab')
1 FAIL: test_LIVE1_a_restated_ask_sends_nothing_and_a_new_one_sends_once (test_asks.LiveBaseTests.test_LIVE1_a_restated_ask_sends_nothing_and_a_new_one_sends_once) (module='candidate', text='NEEDS-VICTOR t1 rotate the hub key /y')
1 FAIL: test_LIVE1_rows_the_live_base_wrote_carry_over_the_install_and_its_rollback (test_asks.LiveBaseTests.test_LIVE1_rows_the_live_base_wrote_carry_over_the_install_and_its_rollback)
1 FAIL: test_LIVE1_the_live_base_fixture_matrix_passes_on_the_candidate_and_the_live_base (test_asks.LiveBaseTests.test_LIVE1_the_live_base_fixture_matrix_passes_on_the_candidate_and_the_live_base) (module='src')
1 FAIL: test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send (test_asks.LiveBaseTests.test_LIVE2_prose_that_names_the_markers_is_no_ask_and_asks_in_the_same_shapes_send)
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate)
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='BLOCKED lines are now counted anywhere.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='Decisions for Victor count as asks now.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR AND BLOCKED markers count anywhere.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR detection is covered by 3 tests.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR matches inside fences and inline code.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR now matches inside code spans.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR Or BLOCKED lines count.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR status is now covered by the suite.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done)
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='Assuming the vote lands, the research stays DONE.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='I cannot say the objective is DONE yet.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='If CI passes, the objective is DONE.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='It is DONE except the last check still fails.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='Phase 1 is DONE, now starting phase 2.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='Phase 2 is still running while phase 1 is DONE.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='Phase 2 running. Phase 1 is DONE.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='Restate it as `The research stays DONE.`')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='Review reopened the work. The objective is DONE.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='`The objective is DONE.`')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='The objective is DONE if CI passes.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='The objective is DONE once the review votes.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='The objective is DONE, pending the second vote.')
1 FAIL: test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done (test_generations.EventTests.test_SOL1_r2_progress_and_qualified_restatements_after_a_done_led_line_send_no_done) (text='The objective was DONE until review reopened it.')
1 FAIL: test_SOL2_r2_complete_decision_ids_and_a_phrase_of_one_ask_only (test_asks.ThreadNoticeTests.test_SOL2_r2_complete_decision_ids_and_a_phrase_of_one_ask_only)
----------------------------------------------------------------------
Ran 9 tests in 3.087s

FAILED (failures=31, errors=2)
```

### round-2 settle guard test on a31f46b mcp_call.py (NEW-2)

`cd candidate/.tmp-run/receipts/round1/mcp && env WATCHDOG_SRC=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src python3 -m unittest tests.test_settle_guard.SettleGuardTests.test_NEW2_a_producer_or_repair_child_is_no_required_reviewer` → exit 1

```
FF
======================================================================
FAIL: test_NEW2_a_producer_or_repair_child_is_no_required_reviewer (tests.test_settle_guard.SettleGuardTests.test_NEW2_a_producer_or_repair_child_is_no_required_reviewer) (producer='Round-1 repair of review findings')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/round1/mcp/tests/test_settle_guard.py", line 161, in test_NEW2_a_producer_or_repair_child_is_no_required_reviewer
    self.assertIsNone(guard(self.model(self.done(), children=children), 'fd', 'p'))
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'reviewer sol ended without an ACCEPT (BLOCKED, no verdict or failed run)' is not None

======================================================================
FAIL: test_NEW2_a_producer_or_repair_child_is_no_required_reviewer (tests.test_settle_guard.SettleGuardTests.test_NEW2_a_producer_or_repair_child_is_no_required_reviewer) (producer='Repair review round 2 findings')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/round1/mcp/tests/test_settle_guard.py", line 161, in test_NEW2_a_producer_or_repair_child_is_no_required_reviewer
    self.assertIsNone(guard(self.model(self.done(), children=children), 'fd', 'p'))
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'reviewer sol ended without an ACCEPT (BLOCKED, no verdict or failed run)' is not None

----------------------------------------------------------------------
Ran 1 test in 0.024s

FAILED (failures=2)
```

### round-2 gate and recheck tests on a31f46b watchdog_gate.py and replay_recheck.py

`cd candidate/.tmp-run/receipts/round1/install && python3 -m unittest tests.test_install.GateTests.test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed tests.test_install.RecheckTests.test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer` → exit 1

```
1 FAIL: test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer (tests.test_install.RecheckTests.test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer) (fields={'createdBy': 'agent', 'creationSource': 'provider'})
1 FAIL: test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer (tests.test_install.RecheckTests.test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer) (fields={'createdBy': 'agent', 'creationSource': 'server'})
1 FAIL: test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer (tests.test_install.RecheckTests.test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer) (fields={'createdBy': 'agent', 'creationSource': 'server', 'delegatedCompletion': {'taskIds': ['t']}})
1 FAIL: test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer (tests.test_install.RecheckTests.test_LIVE1_an_agent_artifact_after_the_ask_is_no_answer) (fields={'createdBy': 'system', 'creationSource': 'server'})
1 FAIL: test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed (tests.test_install.GateTests.test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed) [empty service state]
1 FAIL: test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed (tests.test_install.GateTests.test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed) [failed timer]
1 FAIL: test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed (tests.test_install.GateTests.test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed) [service in maintenance]
1 FAIL: test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed (tests.test_install.GateTests.test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed) [systemctl exits 1 with empty stdout]
1 FAIL: test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed (tests.test_install.GateTests.test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed) [units not found (systemd reads them inactive)]
1 FAIL: test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed (tests.test_install.GateTests.test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed) [unknown service state]
1 FAIL: test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed (tests.test_install.GateTests.test_SOLR21_systemctl_errors_unknown_states_and_missing_units_fail_closed) [unknown timer state]
----------------------------------------------------------------------
Ran 2 tests in 0.451s

FAILED (failures=11)
```

### rehearsal with the a31f46b install.sh and rollback.sh on the cb8a6cc0 live base (LIVE-1)

`cd candidate && env REHEARSE_SCRIPTS=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/round1/install-scripts bash install/rehearse.sh /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal-round1 /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/repair-r2/asks-copy-20261023T233547.sqlite3 /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/evidence/requeue-copy` → exit 1

```
FAIL main: dry run passes the gate on a monotonic timer (DS-H1)
PASS main: dry run changes nothing
FAIL main: install exits 0
FAIL main: files are the candidate
FAIL main: backups are the bases
FAIL main: migration up ok
FAIL main: the unanswered replay is rechecked and stays queued (SOL-7)
ls: cannot access '/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal-round1/main/home/.local/state/sats-completion/requeue-archive-*/': No such file or directory
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
FAIL first-pin: a live 406e3fd9 stops the install before any change (LIVE-1)
```

The a31f46b dry run on a cb8a6cc0 HOME: `00:34:05 STOP: asks live hash cb8a6cc0f676ab0062b31ecbde7a59c2137e3bb9cb197b9fd066dd603925ad94 is neither the base nor the candidate`

## 2c. The live base's own 19-case matrix (blocked-threads-rca-20261023, MBP)

Unmodified MBP copy (`repair-r2/needs-victor-matrix/test_needs_victor.py`, sha256 `253b1c2fa50a892d`), deps = this suite's src:

### unmodified matrix on the live base cb8a6cc0

`cd repair-r2/needs-victor-matrix && python3 -B -I test_needs_victor.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/tests/preimage/live-20261023-needs-victor/sats_stall_asks.py` → exit 0

```
PASS own-run-active blocker_sent=False asks=[(3, 'pending', 'BLOCKED')]
PASS later-run-active occurrences=['generation-3-BLOCKED']
PASS completed-unsettled occurrences=['generation-3-BLOCKED']
PASS idle-unsettled occurrences=['generation-3-BLOCKED']
PASS catchup-native-completion blocker_sent=True asks=[(3, 'bound', 'BLOCKED')] occurrences=['generation-3-BLOCKED']
PASS catchup-server-wake-mcp-shape blocker_sent=True asks=[(3, 'bound', 'BLOCKED')] occurrences=['generation-3-BLOCKED']
PASS later-run-already-blocked occurrences=['generation-3-BLOCKED-b037633be9b527b0']
PASS second-report-same-generation occurrences=['generation-3-BLOCKED', 'generation-3-BLOCKED-1e43f1c7ee29219e']
PASS restated-ask-sends-nothing-new occurrences=['generation-3-BLOCKED']
PASS same-ask-never-twice sends=2
PASS human-answer-web blocker_sent=False asks=[]
PASS sats-relay-mcp (live item 1329 shape) blocker_sent=False asks=[]
PASS reconcile-pending-then-human blocker_sent=False asks=['overridden']
PASS reconcile-pending-then-server-wake blocker_sent=True asks=['bound']
PASS reread-ask-then-human blocker_sent=False asks=['overridden']
PASS reread-ask-then-server-wake blocker_sent=True asks=['bound']
PASS reread-event-then-human claimed=['pending'] blocker_sent=False events=['overridden']
PASS reread-event-then-server-wake claimed=['pending'] blocker_sent=True events=['sent']
PASS start-unchanged starts=['generation-4-START']
MATRIX PASS 19/19 sats_stall_asks.py
```

### unmodified matrix on the candidate (the per-ask occurrence suffix alone differs)

`cd repair-r2/needs-victor-matrix && python3 -B -I test_needs_victor.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src/sats_stall_asks.py` → exit 1

```
PASS own-run-active blocker_sent=False asks=[(3, 'pending', 'BLOCKED')]
PASS later-run-active occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS completed-unsettled occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS idle-unsettled occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS catchup-native-completion blocker_sent=True asks=[(3, 'bound', 'BLOCKED')] occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS catchup-server-wake-mcp-shape blocker_sent=True asks=[(3, 'bound', 'BLOCKED')] occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS later-run-already-blocked occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS second-report-same-generation occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a', 'generation-3-BLOCKED-ask-1e43f1c7ee29219eb2b847da1417ba91']
FAIL restated-ask-sends-nothing-new occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS same-ask-never-twice sends=2
PASS human-answer-web blocker_sent=False asks=[]
PASS sats-relay-mcp (live item 1329 shape) blocker_sent=False asks=[]
PASS reconcile-pending-then-human blocker_sent=False asks=['overridden']
PASS reconcile-pending-then-server-wake blocker_sent=True asks=['bound']
PASS reread-ask-then-human blocker_sent=False asks=['overridden']
PASS reread-ask-then-server-wake blocker_sent=True asks=['bound']
PASS reread-event-then-human claimed=['pending'] blocker_sent=False events=['overridden']
PASS reread-event-then-server-wake claimed=['pending'] blocker_sent=True events=['sent']
PASS start-unchanged starts=['generation-4-START']
MATRIX FAIL 18/19 sats_stall_asks.py
```

### suite copy (tests/needs_victor) on the candidate

`cd candidate/tools/sats-stall-watchdog/tests/needs_victor && python3 -B -I test_needs_victor.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src/sats_stall_asks.py` → exit 0

```
PASS own-run-active blocker_sent=False asks=[(3, 'pending', 'BLOCKED')]
PASS later-run-active occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS completed-unsettled occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS idle-unsettled occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS catchup-native-completion blocker_sent=True asks=[(3, 'bound', 'BLOCKED')] occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS catchup-server-wake-mcp-shape blocker_sent=True asks=[(3, 'bound', 'BLOCKED')] occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS later-run-already-blocked occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS second-report-same-generation occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a', 'generation-3-BLOCKED-ask-1e43f1c7ee29219eb2b847da1417ba91']
PASS restated-ask-sends-nothing-new occurrences=['generation-3-BLOCKED']
PASS same-ask-never-twice sends=2
PASS human-answer-web blocker_sent=False asks=[]
PASS sats-relay-mcp (live item 1329 shape) blocker_sent=False asks=[]
PASS reconcile-pending-then-human blocker_sent=False asks=['overridden']
PASS reconcile-pending-then-server-wake blocker_sent=True asks=['bound']
PASS reread-ask-then-human blocker_sent=False asks=['overridden']
PASS reread-ask-then-server-wake blocker_sent=True asks=['bound']
PASS reread-event-then-human claimed=['pending'] blocker_sent=False events=['overridden']
PASS reread-event-then-server-wake claimed=['pending'] blocker_sent=True events=['sent']
PASS start-unchanged starts=['generation-4-START']
MATRIX PASS 19/19 sats_stall_asks.py
```

### suite copy (tests/needs_victor) on round-1 a31f46b (must fail)

`cd candidate/tools/sats-stall-watchdog/tests/needs_victor && python3 -B -I test_needs_victor.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/round1/tools/sats-stall-watchdog/src/sats_stall_asks.py` → exit 1

```
PASS own-run-active blocker_sent=False asks=[(3, 'pending', 'BLOCKED')]
PASS later-run-active occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS completed-unsettled occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS idle-unsettled occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
FAIL catchup-native-completion blocker_sent=False asks=[] occurrences=[]
FAIL catchup-server-wake-mcp-shape blocker_sent=False asks=[] occurrences=[]
PASS later-run-already-blocked occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a']
PASS second-report-same-generation occurrences=['generation-3-BLOCKED-ask-b037633be9b527b058d2650b31324b8a', 'generation-3-BLOCKED-ask-1e43f1c7ee29219eb2b847da1417ba91']
FAIL restated-ask-sends-nothing-new occurrences=['generation-3-BLOCKED', 'generation-3-BLOCKED']
PASS same-ask-never-twice sends=2
PASS human-answer-web blocker_sent=False asks=[]
PASS sats-relay-mcp (live item 1329 shape) blocker_sent=False asks=[]
PASS reconcile-pending-then-human blocker_sent=False asks=['overridden']
FAIL reconcile-pending-then-server-wake blocker_sent=False asks=['overridden']
PASS reread-ask-then-human blocker_sent=False asks=['overridden']
FAIL reread-ask-then-server-wake blocker_sent=False asks=['overridden']
PASS reread-event-then-human claimed=['pending'] blocker_sent=False events=['overridden']
FAIL reread-event-then-server-wake claimed=['pending'] blocker_sent=False events=['overridden']
PASS start-unchanged starts=['generation-4-START']
MATRIX FAIL 13/19 sats_stall_asks.py
```

## 2d. Review round-3 tests against the round-2 candidate 917f4de (must fail)

### round-3 watchdog tests on 917f4de (asks af27b66f)

`cd candidate/.tmp-run/receipts/round2/tools/sats-stall-watchdog/tests && python3 -m unittest test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done test_asks.ThreadNoticeTests.test_SOL2_r3_marker_words_paths_and_negated_sentences_decide_what_a_notice_carries test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate` → exit 1

```
1 ERROR: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (ask='BLOCKED: lines 40-60 were not applied. Which branch?')
1 ERROR: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (ask='BLOCKED: prefix check fails on F-D; may I bypass?')
1 ERROR: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (ask='Decision for you: lines 40 or 60 for the fix?')
1 ERROR: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (ask='NEEDS-VICTOR and BLOCKED: pick A or B before I can proceed.')
1 ERROR: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (ask='NEEDS-VICTOR: tags on release r3 are wrong; which set?')
1 ERROR: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (ask='NEEDS-VICTOR tokens expired.')
1 ERROR: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (ask='NEEDS-VICTOR tokens expired; approve replacing the credentials.')
1 ERROR: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (ask='NEEDS-VICTOR: tokens for the T05 push expire tomorrow; rotate now?')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate)
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='Decisions for Victor count as asks now.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR AND BLOCKED markers count anywhere.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR detection is covered by 3 tests.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR matches inside fences and inline code.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR now matches inside code spans.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR Or BLOCKED lines count.')
1 FAIL: test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate (test_asks.LiveBaseTests.test_LIVE2_r3_a_label_or_a_request_asks_and_a_mention_needs_joined_names_or_a_detection_predicate) (mention='NEEDS-VICTOR status is now covered by the suite.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done)
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='All work is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='No remaining items. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='Nothing is pending. The work is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='Nothing is running. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='No work is pending. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='The assignment is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='The delivery is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='The migration is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='The objective is DONE now.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='The repair is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='The review is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='The whole work is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (kept='The work is done.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='2 of 5 checks pass. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress="I'll post the logs. The objective is DONE.")
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='It is false that:\n\nThe objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='It is false that:\nThe objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='More results to come. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='No tests passed. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='Phase 2 is not finished. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='Phase 2 is ongoing. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='Phase 2 is underway. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='Phase 2 log:\n```\nstarting phase 2\n```\nThe objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='Should I rerun it? The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='The following sentence is a template, not a completion claim:\n> The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='The last check is in flight. The work is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='The nightly re-run is still going. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='- The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='The rerun is queued for tonight. The objective is DONE.')
1 FAIL: test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done (test_generations.EventTests.test_SOL1_r3_clause_negation_quotes_and_whole_work_subjects_decide_a_kept_done) (progress='Two checks are outstanding. The objective is DONE.')
1 FAIL: test_SOL2_r3_marker_words_paths_and_negated_sentences_decide_what_a_notice_carries (test_asks.ThreadNoticeTests.test_SOL2_r3_marker_words_paths_and_negated_sentences_decide_what_a_notice_carries)
----------------------------------------------------------------------
Ran 3 tests in 1.492s

FAILED (failures=40, errors=8)
```

### round-3 settle guard test on 917f4de mcp_call.py (R3-5)

`cd candidate/.tmp-run/receipts/round2/mcp && env WATCHDOG_SRC=/home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src python3 -m unittest tests.test_settle_guard.SettleGuardTests.test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named` → exit 1

```
1 FAIL: test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named (tests.test_settle_guard.SettleGuardTests.test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named) (producer='Notice package review round 2 repair by Sol')
1 FAIL: test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named (tests.test_settle_guard.SettleGuardTests.test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named) (reviewer='DeepSeek V4.1 Flash high - re-review of notice package')
1 FAIL: test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named (tests.test_settle_guard.SettleGuardTests.test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named) (reviewer='DeepSeek V4.1 Flash high - re-review of the repair')
1 FAIL: test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named (tests.test_settle_guard.SettleGuardTests.test_R35_a_producer_role_anywhere_is_no_seat_and_this_lanes_titles_read_as_named) (reviewer='Sol 6.1 High - review of repair round 2')
----------------------------------------------------------------------
Ran 1 test in 0.021s

FAILED (failures=4)
```

### the reviewers' round-3 probes on 917f4de (repair-r3/probes.py)

`cd candidate && python3 -B /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/repair-r3/probes.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/round2/tools/sats-stall-watchdog/src/sats_stall_asks.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/round2/mcp/mcp_call.py` → exit 1

```
OK    seat   'DeepSeek High review · review_notice_package_20261023_r1' -> True
WRONG seat   'Notice package review round 2 repair by Sol' -> True
OK    seat   'Opus 5.5 XHigh repair · repair_notice_package_20261023_r3' -> False
wrong: 34
```

### the reviewers' round-3 probes on the candidate

`cd candidate && python3 -B /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/repair-r3/probes.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/tools/sats-stall-watchdog/src/sats_stall_asks.py /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/mcp/mcp_call.py` → exit 0

```
OK    seat   'DeepSeek High review · review_notice_package_20261023_r1' -> True
OK    seat   'Notice package review round 2 repair by Sol' -> False
OK    seat   'Opus 5.5 XHigh repair · repair_notice_package_20261023_r3' -> False
wrong: 0
```

## 3. victor-vault tools/sats-stall-watchdog (canon-clone, item 4)

Staged, not pushed: `9ae00cc canon (H, proposed with D, F and G): round-3 ask and DONE wording; 2762218 tools/sats-stall-watchdog: notice-package round-3 repairs (equals the candidate); 176ca99 canon (G, proposed with D and F): round-2 ask and DONE wording;  the live needs-victor fix's rules; bf31f4d tools/sats-stall-watchdog: notice-package round-2 repairs and the live base's behavior (equals the candidate); 56e1fff Merge origin/main ee57fda into notice-package-20261023 (canon 4a02910 as ancestor); 0fad1e3 canon (proposed with D): each ask decided on its own;  the DONE reply is the final reply; e131c2d tools/sats-stall-watchdog: notice-package round-1 repairs (equals the candidate); 8558a4e canon (proposed, droppable): watchdog asks for notice-package items 5 and 6; 18cc3fd canon: watchdog DONE is the DONE reply, never a settle (notice-package-20261023 item 3); b278b7c tools/sats-stall-watchdog: DONE on the DONE reply, markers anywhere, one BLOCKED per ask; 390f1ff tools/sats-stall-watchdog: catch up to the live F-D install; `

4a02910 is an ancestor of HEAD: yes. origin/main is an ancestor (the push fast-forwards): yes.

### vault suite at HEAD (catch-up + items 1, 5, 6, round-1 to round-3 repairs)

`cd canon-clone/tools/sats-stall-watchdog && python3 -m unittest discover -s tests -p test_*.py` → exit 1

```
................<frozen codecs>:189: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x7fc93fbd6020>
ResourceWarning: Enable tracemalloc to get the object allocation traceback
.................................................................F.......................................................F.........
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
Ran 147 tests in 19.873s

FAILED (failures=2)
```

Vault `src/sats_stall_asks.py` equals the candidate: yes.
Vault `src/sats_stall_watchdog.py` equals the candidate: yes.

## 4. Migration and install rehearsals

### migration up and down on a copy of the live asks.sqlite3 (23:35, one BLOCKED:<digest> row)

`cd candidate && python3 -I install/events_migration.py --lib tools/sats-stall-watchdog/src rehearse /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/asks-rehearse.sqlite3` → exit 0

```
  "ok": true,
  "parked": 0
 }
}
```

### install and rollback in a sandbox HOME on the cb8a6cc0 live base

`cd candidate && bash install/rehearse.sh /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/candidate/.tmp-run/receipts/rehearsal /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/repair-r2/asks-copy-20261023T233547.sqlite3 /home/victor/.t3-nightly/scratch/2026-10-24-you-are-now-running-as-5aa90f48/evidence/requeue-copy` → exit 0

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
PASS first-pin: a live 406e3fd9 stops the install before any change (LIVE-1)
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
cb8a6cc0f676ab0062b31ecbde7a59c2137e3bb9cb197b9fd066dd603925ad94  /home/victor/.local/lib/sats-stall-watchdog/sats_stall_asks.py
406e3fd97579e823f67d27f4e02f4b81cab11a720f39df8ff5bb7e2af16a0a22  /home/victor/.local/lib/sats-stall-watchdog/sats_stall_asks.py.bak-needs-victor-20261023T225552
6ea2e6fb3fe1134b0a5f3b99962c2837842b20fda06ce9632e74e206dfa1a06d  /home/victor/.local/lib/sats-stall-watchdog/sats_stall_watchdog.py
ad1f0106f6f8d0fad97067d7fa2807bd41c9991af5c9fc12adae91b45fc1ae62  /home/victor/.local/bin/sats-completion-notify
d1bb0937f00685989da4debf547fa2bcc5675226d695f78a471ba08c4eb7e4e7  /home/victor/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py
requeue unit files on F-D: 0
requeue entries: 25, all matching the triage sha256: True
live events schema: CREATE TABLE events (id TEXT PRIMARY KEY, thread TEXT NOT NULL, generation INTEGER NOT NULL, state TEXT NOT NULL, data TEXT NOT NULL, UNIQUE (thread, generation, state))
```
