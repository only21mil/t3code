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
| 1, 5, 6 | `~/.local/lib/sats-stall-watchdog/sats_stall_asks.py` | `406e3fd9…0a22` | `8772ee0b…47d1` (`tools/sats-stall-watchdog/src/sats_stall_asks.py`) |
| 6 | `~/.local/state/sats-stall-watchdog/asks.sqlite3` events table | one-per-generation key | per-ask key (`install/events_migration.py up`) |
| 2 | `~/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py` | `d1bb0937…e4e7` | `b1959e29…d2e3` (`mcp/mcp_call.py`) |
| 7b, 7c | `~/.local/bin/sats-completion-notify` | `ad1f0106…ae62` | `0bfdc3b9…5159` (`notify/sats-completion-notify`) |
| 7a | `~/.config/systemd/user/sats-completion-requeue.{service,timer}` | absent | `notify/systemd/` (`9181dda6…`, `ffdbad43…`) |
| 7a | `~/.local/state/sats-completion/requeue/` | 25 entries | 1 replay kept; 24 moved to `requeue-archive-<date>/` (`install/requeue-triage.json`, `TRIAGE.md`) |
| 3, 4 | only21mil/victor-vault `main` | `428be151` | canon-clone commits A-C, plus D if review accepts it |

## Steps

1. **Dry run.** `install/install.sh --head <reviewed commit> --dry-run`. It runs every check and changes
   nothing: each live file is at its base or already installed, every target path is free of symlinks, the
   candidate tree is clean at that commit, the requeue holds exactly the 25 triaged entries with matching sha256,
   the replay entry's thread is still unanswered (watchdog sig unchanged), and the watchdog is between ticks.
   A changed requeue stops the install and needs a fresh triage.
2. **Install.** `install/install.sh --head <reviewed commit>`. In order, it:
   - writes a `.bak-notice-package-<ts>` beside each changed file and copies it into `install-record-<ts>/`;
   - takes a read-consistent copy of asks.sqlite3 with the sqlite backup API, beside the live file;
   - places each file by same-directory temp and rename, then drops the stale `sats_stall_asks` bytecode;
   - migrates the events table with the installed module in one `BEGIN IMMEDIATE` transaction. There is no
     VACUUM and no checkpoint, so the file keeps its freed pages and grows by about 0.3 MB (rehearsal:
     1.29 to 1.62 MB);
   - moves the 24 archive entries into `~/.local/state/sats-completion/requeue-archive-<date>/` with a
     manifest that lists the 6 DONE entries, and leaves only the live a9acdeb1 BLOCKED queued;
   - runs `daemon-reload`, enables the requeue timer and starts its drainer once, so the a9acdeb1 notice replays.
   It restarts nothing. The watchdog runs the new module at its next 5-minute tick, and the install
   verifies that the watchdog timer's `ActiveEnterTimestamp` is unchanged.
3. **Canon, same window.** In `canon-clone/`, `git fetch origin && git rebase origin/main` (the commits are local,
   so this rewrites no published history), rerun `tools/sats-stall-watchdog` tests, then
   `git push origin HEAD:main` with no force. If review drops D, first run `git reset --keep HEAD~1` while D
   is still the tip, before the rebase. Record the pushed sha in the close-out.
4. **Check after the next watchdog tick.**
   - `journalctl --user -u sats-stall-watchdog --since -10min` shows a completed tick.
   - `sqlite3 -readonly ~/.local/state/sats-stall-watchdog/asks.sqlite3 "PRAGMA table_xinfo(events)"` lists `ask`.
   - `grep a9acdeb1 ~/.local/state/sats-completion/hook.log | tail -2` shows the requeue post. If it fails
     again, the line now carries `error_code`.
   - `systemctl --user list-timers sats-completion-requeue.timer` shows the timer.
   - The next Victor ask in any thread sends its own BLOCKED, and a DONE-led reply sends DONE a minute after
     its turn ends.

## Rehearsed, not run live

`install/rehearse.sh <empty dir in the lane> <asks.sqlite3 copy> <requeue copy>` runs the dry run, the install and
`rollback.sh` in a sandbox HOME with a `systemctl` shim. It found and fixed one bug, an unquoted
`install.env` value. Its 11 checks pass (`RECEIPTS.md`).
