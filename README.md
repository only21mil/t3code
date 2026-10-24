# notice-package-20261023 candidate

Reviewable in place: `git log --oneline base..HEAD`, `git diff base..HEAD -- <path>`. Tags mark each step:
`base` (live files and the suite frozen with them), `patch-1`, `patch-2`, `item-5`, `item-6`, `item-7`. The
round-1 repairs follow the round-0 candidate `e6a95f42` (`git log --oneline e6a95f42..HEAD`), the round-2 repairs
follow `a31f46b`, and the round-3 repairs follow `917f4de`.

`base` holds the asks module 406e3fd9, where production started. Since 2026-10-23 22:55:52 CDT the live asks module
is cb8a6cc0, the needs-victor fix (canon source 4a02910), frozen at
`tools/sats-stall-watchdog/tests/preimage/live-20261023-needs-victor/`. The install expects and backs up cb8a6cc0;
`git diff --no-index` of that file against `src/sats_stall_asks.py` is the change it makes to the live module.

| Repo path | Installs to | Package item |
|---|---|---|
| `tools/sats-stall-watchdog/src/sats_stall_asks.py` | `~/.local/lib/sats-stall-watchdog/sats_stall_asks.py` | 1, 5, 6 |
| `tools/sats-stall-watchdog/src/sats_stall_watchdog.py` | `~/.local/lib/sats-stall-watchdog/sats_stall_watchdog.py` | 6 (`AskTransport.notice_message`) |
| `tools/sats-stall-watchdog/tests/` | none (suite; also lands in victor-vault, item 4) | 1, 5, 6 |
| `mcp/mcp_call.py`, `mcp/tests/` | `~/work/t3-mcp-connect-2026-10-07/scripts/mcp_call.py` | 2 |
| `notify/sats-completion-notify`, `notify/tests/` | `~/.local/bin/sats-completion-notify` | 7b, 7c |
| `notify/systemd/` | `~/.config/systemd/user/` | 7a |
| `install/` | none: `install.sh`, `rollback.sh`, `rehearse.sh`, `watchdog_gate.py`, `replay_recheck.py`, `events_migration.py`, `requeue-triage.json`, `tests/` | all |

`INSTALL.md`, `ROLLBACK.md` and `RECEIPTS.md` sit beside this file. Canon items 3 and 4 are commits in
`../canon-clone/` (only21mil/victor-vault), not here.
