# Install: notice-package-20261023 items 1-7 on framework-desktop

Authority: Victor 8:39 PM CT 2026-10-23, relayed by Sats: "GO: lift Genesis's stop for one F-D lane to write
items 5-7 under review, then install items 1-7 together". It does not cover restarting any server, T3 or the
hub, replaying old DONE notices, or patch 3. Each of those needs its own GO, and this install does none of them.

Run it only after review-and-babysit ACCEPT of the candidate commit and of the canon-clone commits. Install all of
it in one window: the live files, the DB migration, the requeue units and the canon push. Canon item 3 lands with
patch 1, never alone.

## What changes

| Item | Live path | Base sha256 | Candidate sha256 (repo path) |
|---|---|---|---|
| 1, 5, 6 | `~/.local/lib/sats-stall-watchdog/sats_stall_asks.py` | `cb8a6cc0…ad94`, the needs-victor fix installed 2026-10-23 22:55:52 CDT (canon source 4a02910). Its own `.bak-needs-victor-20261023T225552` beside it is `406e3fd9…0a22`, this package's first pin, and the install never touches it | `46280245…35eb` (`tools/sats-stall-watchdog/src/sats_stall_asks.py`), which carries every cb8a6cc0 behavior (RECEIPTS.md § 2c) |
| 6 | `~/.local/lib/sats-stall-watchdog/sats_stall_watchdog.py` | `6ea2e6fb…a06d` | `78b5b26a…a871` (`tools/sats-stall-watchdog/src/sats_stall_watchdog.py`): `AskTransport.notice_message`, which tells which ask a thread's own notice carried |
| 6 | `~/.local/state/sats-stall-watchdog/asks.sqlite3` events table | one-per-generation key | per-ask key (`install/events_migration.py up`) |
| 2 | `~/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py` | `d1bb0937…e4e7` | `a294dd2b…8823` (`mcp/mcp_call.py`); it reads asks with the installed watchdog's `classify()` |
| 7b, 7c | `~/.local/bin/sats-completion-notify` | `ad1f0106…ae62` | `0bfdc3b9…5159` (`notify/sats-completion-notify`) |
| 7a | `~/.config/systemd/user/sats-completion-requeue.{service,timer}` | absent | `notify/systemd/` (`9181dda6…`, `ffdbad43…`) |
| 7a | `~/.local/state/sats-completion/requeue/` | 25 entries | 1 replay kept if its ask is still unanswered at install; the rest moved to `requeue-archive-<date>/` (`install/requeue-triage.json`, `TRIAGE.md`) |
| 3, 4 | only21mil/victor-vault `main` | `ee57fda` (4a02910 below it) | canon-clone A-C, E, the merge M of `ee57fda` and the tools mirrors E2 and E3, plus D, F, G and H if review accepts them |

## Steps

1. **Dry run.** `install/install.sh --head <reviewed commit> --dry-run`. It runs every check and changes
   nothing; it reads systemctl state and local files only. Each live file is at its base or already installed,
   every target path is free of symlinks, the candidate tree is clean at that commit, the requeue holds exactly
   the 25 triaged entries with matching sha256, and the watchdog is between ticks. A changed requeue stops the
   install and needs a fresh triage.
   - The tick gate is `install/watchdog_gate.py`. The watchdog timer is monotonic (`OnBootSec`,
     `OnUnitActiveSec`), and systemd 259 leaves its `NextElapseUSecRealtime` empty, so the gate reads
     `systemctl --user list-timers --all --output=json` (`next`, epoch µs), else `NextElapseUSecMonotonic`
     against `CLOCK_MONOTONIC`. It passes when both units read `LoadState=loaded`, the service is idle (inactive
     or failed), the timer is active with its next tick 90 s or more away (or inactive), and every read
     succeeded. A failed or empty systemctl read, or any other state, is not ok. It waits up to 10 minutes. A tick runs every 5 minutes and the gate is busy for the whole run, so a
     long tick shortens the window.
2. **Install.** `install/install.sh --head <reviewed commit>`. In order, it:
   - writes a `.bak-notice-package-<ts>` beside each changed file, copies it into `install-record-<ts>/`, and
     lists every backup in `backups.txt` and `install.env`;
   - takes a read-consistent copy of asks.sqlite3 with the sqlite backup API, beside the live file;
   - places each file by same-directory temp and rename, then drops the stale `sats_stall_asks` and
     `sats_stall_watchdog` bytecode;
   - migrates the events table with the installed module in one `BEGIN IMMEDIATE` transaction. There is no
     VACUUM and no checkpoint, so the file keeps its freed pages and grows by about 0.3 MB (rehearsal:
     1.29 to 1.62 MB);
   - reads the replay entry's thread right before the replay. That is `t3_thread_read` on f13pro, read-only,
     through the reviewed `mcp/mcp_call.py` loaded with its PACK in the install record
     (`install/replay_recheck.py`, `replay-recheck.json`). An answer after the ask's position (27), by the
     watchdog's `answers()`, or any failed read, archives the entry instead of replaying it. A delegated
     completion, a server or provider wake or a system notice is no answer.
     The check keys on the answer position, never on settled state. a9acdeb1 shows `settled: true` only because
     the 19:39 sweep settled it over an unanswered Victor ask (notice-delay-rca-20261023; `TRIAGE.md`);
   - moves the stale and DONE entries, and an answered replay entry, into
     `~/.local/state/sats-completion/requeue-archive-<date>/` with a manifest that lists the 6 DONE entries;
   - runs `daemon-reload`, enables the requeue timer and starts its drainer once, so a still-unanswered a9acdeb1
     notice replays.
   It restarts nothing. The watchdog runs the new modules at its next 5-minute tick, and the install
   verifies that the watchdog timer's `ActiveEnterTimestamp` is unchanged.
   - **Interrupted install.** Rerun the same command. A file already at the candidate keeps the ORIGINAL base
     backup the interrupted run wrote beside it: the rerun finds it by sha256, records it in `backups.txt`
     ("an interrupted install") and `install.env`, and writes no second backup. With no base backup beside such
     a file, it stops before changing anything. If the DB was already migrated, `DB_BAK_ORIGINAL` names the
     interrupted run's one-per-generation copy.
3. **Canon, same window.** In `canon-clone/`, `git fetch origin && git merge --no-edit origin/main`. The branch
   already merged `ee57fda` (M, `56e1fff`), so a merge keeps A-H's reviewed hashes and rewrites no history; a
   rebase would flatten M and rewrite them. Rerun `tools/sats-stall-watchdog` tests, check that origin/main is an
   ancestor, then `git push origin HEAD:main` with no force. If review drops D, drop F, G and H with it:
   `git revert --no-edit <H> <G> <F> <D>` before the merge. E, E2 and E3, the tools mirrors, stay. Record the pushed sha
   in the close-out.
4. **Check after the next watchdog tick.**
   - `journalctl --user -u sats-stall-watchdog --since -10min` shows a completed tick.
   - `sqlite3 -readonly ~/.local/state/sats-stall-watchdog/asks.sqlite3 "PRAGMA table_xinfo(events)"` lists `ask`.
   - `cat <record>/replay-recheck.json` says whether a9acdeb1 replayed. If it did,
     `grep a9acdeb1 ~/.local/state/sats-completion/hook.log | tail -2` shows the requeue post; a failure now
     carries `error_code`.
   - `systemctl --user list-timers sats-completion-requeue.timer` shows the timer.
   - The next Victor ask in any thread sends its own BLOCKED, and a DONE-led final reply sends DONE a minute
     after its turn ends.

## Rehearsed, not run live

`install/rehearse.sh <empty absolute dir in the lane> <asks.sqlite3 copy> <requeue copy>` runs four cases in
sandbox HOMEs, absolute paths only, with a `systemctl` shim that answers as live systemd 259 does
(`LoadState=loaded`, empty `NextElapseUSecRealtime`, a monotonic timespan, `list-timers` JSON) and a fixture
thread reader. Each HOME holds the live base: `sats_stall_asks.py` at cb8a6cc0 and its 406e3fd9
`.bak-needs-victor-20261023T225552` beside it.

- main: the dry run, the install and `rollback.sh`, which restores cb8a6cc0 and leaves the needs-victor backup as
  it was;
- answered: Victor answered the replay's ask after the triage;
- resume: an install interrupted after placing `sats_stall_asks.py`, rerun, then rolled back;
- first-pin: the live asks file is back at 406e3fd9, and the install stops before any change.

All 21 checks pass on a live DB copy that holds one of cb8a6cc0's `BLOCKED:<digest>` rows (`RECEIPTS.md`).
