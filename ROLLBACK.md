# Rollback: notice-package-20261023

`install/rollback.sh <lane>/install-record-<ts>` undoes the live install. Like the install, it restarts no
service and runs between watchdog ticks.

1. Disables and stops `sats-completion-requeue.timer` and its service, moves both unit files into the record
   (kept, not deleted), and runs `daemon-reload`.
2. Runs the events down-migration with the candidate module copied into the record (`downgrade_events`, one
   transaction, no VACUUM or checkpoint). The events table returns to its old DDL byte for byte. The first event
   of each (thread, generation, state) stays. Later per-ask BLOCKED rows move to `events_parked`, a table the old
   watchdog never reads. The rehearsal on the live DB copy round-trips byte-identical.
3. Restores `sats_stall_asks.py`, `sats-completion-notify` and `mcp_call.py` from their
   `.bak-notice-package-<ts>` files, with modes 644, 755 and 644, and drops the stale bytecode. The watchdog runs
   the old module at its next tick.
4. Canon is reverted separately and never force-pushed. `git revert` the pushed D (if pushed), C and B on a
   fresh clone of main, then push. Keep A: it is the 406e3fd9/6ea2e6fb catch-up and matches the rolled-back live
   install.

Safety notes:

- Order is forgiving. The old module also runs on the per-ask schema, because `ask` is derived from the event
  JSON and INSERTs still name five columns. `test_downgrade_parks_per_ask_rows_and_the_old_watchdog_runs_on_both_schemas`
  shows it. So a restore without step 2 keeps the watchdog working under its old one-BLOCKED-per-generation rule.
- Archived requeue entries stay archived. Moving them back would queue 18 stale DIED notices and 6 DONE entries,
  and DONE entries are never replayed. The manifest in each `requeue-archive-<date>/` names every entry.
- Last resort only: restore `asks.sqlite3.bak-notice-package-<ts>` with the watchdog idle. Events claimed after
  the install would be forgotten and could send again, so use the down-migration first.
