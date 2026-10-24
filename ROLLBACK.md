# Rollback: notice-package-20261023

`install/rollback.sh <lane>/install-record-<ts>` undoes the live install. Like the install, it restarts no
service and runs between watchdog ticks, gated by the `watchdog_gate.py` the install copied into the record.

0. Checks, before it changes anything, that every changed file has a restore source: the ORIGINAL base backup
   the record names (`install.env` `BAK_<file>`, listed in `backups.txt`), a real file at the base sha256. For a
   resumed install that is the backup the interrupted run wrote. A file that is neither its base nor the
   installed candidate stops the rollback too.
1. Disables and stops `sats-completion-requeue.timer` and its service, moves both unit files into the record
   (kept, not deleted), and runs `daemon-reload`.
2. Runs the events down-migration with the candidate module copied into the record (`downgrade_events`, one
   transaction, no VACUUM or checkpoint). The events table returns to its old DDL byte for byte. Each
   (thread, generation, state) keeps one row: its legacy row when it has one, else its first per-ask row,
   which takes the legacy event id (`per_ask_event_id` keeps the old one). The old watchdog then binds later asks
   of that generation to the kept row: it neither claims a second BLOCKED nor binds to a missing id. The other
   per-ask BLOCKED rows move to `events_parked`, a table the old watchdog never reads. The rehearsal on the live
   DB copy round-trips byte-identical.
3. Restores `sats_stall_asks.py`, `sats_stall_watchdog.py`, `sats-completion-notify` and `mcp_call.py` from
   their recorded original backups, with modes 644, 644, 755 and 644, and drops the stale bytecode. The asks
   module returns to the live base the install backed up, cb8a6cc0 (the needs-victor fix), never to 406e3fd9.
   Its own `.bak-needs-victor-20261023T225552` (406e3fd9) stays beside it untouched. The watchdog runs the
   restored modules at its next tick.
4. Canon is reverted separately and never force-pushed. On a fresh clone of main, `git revert` the pushed G, F
   and D (if pushed), E2, E, C and B, newest first. Keep M, the merge of `ee57fda`: reverting it would undo
   other lanes' commits. Keep A. Then put the record's `asks.bak` (cb8a6cc0) at
   `tools/sats-stall-watchdog/src/sats_stall_asks.py` in one commit, so the vault source matches the restored
   live file rather than A's 406e3fd9 copy, and push.

Safety notes:

- Order matters. Step 2 runs before step 3, both inside one gated window. The old module on the per-ask schema
  finds its legacy BLOCKED key free beside the per-ask rows, so a re-wake repeating an ask already sent
  per ask would send a second BLOCKED
  (`test_DSM3_the_old_module_on_the_per_ask_schema_can_send_a_second_blocked`; cb8a6cc0 keeps that legacy key
  for a generation's first BLOCKED, so the same holds for it). After the down-migration, cb8a6cc0 binds a
  restated ask to the kept row and gives a new ask its own `BLOCKED:<digest>` row
  (`test_LIVE1_rows_the_live_base_wrote_carry_over_the_install_and_its_rollback`). The reverse window is unsafe
  as well: the candidate module re-upgrades a downgraded table on its next tick. So never restore the files
  without the down-migration, and run both between the same two ticks.
- Archived requeue entries stay archived. Moving them back would queue 18 stale DIED notices and 6 DONE entries,
  and DONE entries are never replayed. The manifest in each `requeue-archive-<date>/` names every entry.
- Last resort only: restore the `asks.sqlite3` copy that `DB_BAK_ORIGINAL` in `install.env` names, with the
  watchdog idle. Events claimed after the install would be forgotten and could send again, so use the
  down-migration first.
