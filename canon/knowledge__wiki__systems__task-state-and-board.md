---
title: Resumable task state and parent boards
created: 2026-09-27
updated: 2026-10-25
type: system
status: active
tags: [agent-system, workflow]
sources:
  - 'Victor 2026-10-25 4:41 PM CT nested V2 design and 4:58 PM CT canon alignment (objective canon-nested-v2-and-cc-providers-20261025, brief sha256 c38ef22b961e187048ee093fb1c48f1e8ea0d5c8f32a4512c6c31aba6729e207): each orchestrator layer keeps its own board; the master tracks per-PR threads, PR watch and worktree retirement'
  - 'Victor 2026-10-24, canon-gh-main-20261024: canon read source, owned by [[wiki/systems/agent-shared-victor-vault-auto-push#Current contract (2026-10-20)]] item 6, Read path'
  - RESEARCH/karpathy-loops-2026-09-27/CONSENSUS.md
  - RESEARCH/karpathy-loops-2026-09-27/DRAFT.md
  - Victor 2026-10-07, every T3 Code child through T3 Orchestrator V2 (objective t3-v2-standard-20261007)
  - Victor ruling 5, 2026-10-18 (D14): NOTES.md only for resumable, writing or long-running work
  - 'Cut spans, 2026-10-18: [[wiki/archive/task-state-and-board-2026-10-18]]'
confidence: medium
owner: sats
---

# Resumable task state and parent boards

Use this page for task notes, parent-board records and the existing Workflow
drift helper. Before dispatch, relaunch, steering or lifecycle changes, read
[[wiki/systems/sats-pm-visible-swarm#Roles and readiness]] and
[[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]].
Before writing a brief, follow [[wiki/systems/sats-pm-visible-swarm#Brief contract]].
Before reporting, follow [[wiki/systems/task-notices-and-reporting]].

For the helper commands below, use Node 22.18+ and
`node <canon-root>/scripts/task-state.ts …`. Templates are in
`<canon-root>/templates/task-state/`.

## Child launch and relaunch

Keep `NOTES.md` for resumable, writing or long-running work; a one-shot reader
needs none. Initialize it in the assigned task directory with
`scripts/task-state.ts notes-init <absolute-task-directory>`. Preserve an
existing file. Update Done, Tried and failed, and Next at each milestone.
Give Done entries stable step IDs and evidence paths or hashes. Exclude
secrets and transcript dumps.

Before resuming, read all three sections and the failed-step evidence.
Continue from recorded Done work. Build a notes-based launch or relaunch
brief with `scripts/task-state.ts relaunch <absolute-task-directory>
<brief-file>`; its first instruction reads NOTES.md. The brief's contents
follow the swarm's Brief contract. Keep the same task directory so evidence
remains available. A resumed Workflow run reuses its cached calls; a V2
relaunch is a new `delegate_task` carrying the relaunch brief. A CI repair on
an open PR is likewise a fresh agent on the same PR worktree and the same task
directory; its trigger and brief inputs belong to
[[wiki/systems/t3-upstream-pr-lanes#PR watch, Victor 2026-10-25]]. Child
creation and retry decisions remain with the swarm owner above.

## Grok project state

For an existing Grok project state file, use `RESEARCH/<project>/STATE.yaml`.
Keep the template's JSON serialization, a YAML subset accepted by the
validator without a YAML dependency. Include `done_def`, `step`, `next_owner`,
`next_check_at`, `status` and `last_artifact`. Status is active, done or blocked.
`last_artifact` is null or a project-relative path and sha256 recorded when
the current step began. For grills retain `round`, `opened_at`, `seats_spoken`
and `next_eta` as evidence. Omit attempt and re-issue counters.

When running the existing stale-report helper, use an explicit Victor-only
inventory, never an arbitrary vault scan. Exclude Softfork, Signal and family
projects:

```json
{
  "research_root": "/absolute/Victor/Agent-Shared/RESEARCH",
  "projects": [
    {"id": "project_id", "scope": "victor", "state": "/absolute/Victor/Agent-Shared/RESEARCH/project_id/STATE.yaml"}
  ]
}
```

Run `scripts/task-state.ts stale <inventory.json> <UTC-now> <absolute-report-path>`.
Use `knowledge/_meta/grok-stale.md` for the generated report. The helper lists
overdue active steps with no changed artifact; the owner evaluates changed
artifacts against `done_def`. Missing or invalid state is unverified.
Check the exit status: a failed scan produces "Scan failed; unverified";
if writing fails, any old report is unusable. A clean scan empties the report.
This helper grants no scheduler or wake authority. Routine-resume approval
and the historical rollout limits are recorded in
`git show 8b42da5f:Agent-Shared/knowledge/wiki/systems/task-state-and-board.md`.

## Parent board and drift hook

Every orchestrator layer keeps its own `BOARD.md` from the template: the
master for the objective, and each per-PR orchestrator for its PR (roles:
[[wiki/systems/sats-pm-visible-swarm#Roles and readiness]]). A per-PR board
lives in the lane record folder the master's brief names, outside the PR
worktree. Put Objective, Decisions and Guards in the header, active rows in
Live and planned work in Plan. Live lists only the children that layer opened:
exact `wf_` run IDs for Workflow rows, `taskId` plus `childThreadId` for V2
delegate rows, `threadId` for per-PR orchestrator rows. The master also keeps
one PR row per PR from launch until the PR merges or closes: branch, worktree
path and current per-PR `threadId`, then the PR URL, PR-watch state and CI
disposition once it opens the PR
([[wiki/systems/t3-upstream-pr-lanes#PR watch, Victor 2026-10-25]]). A per-PR
handback closes that thread's row, never the PR row. Read V2
terminal status through `task_status`, and a per-PR orchestrator's through its
accepted final report, under
[[wiki/systems/sats-pm-visible-swarm#Orchestrator wake and fill, Victor 2026-10-22]].
Before its terminal handback, the master reconciles every Live row with the
final status check that section owns; a row without terminal evidence stays
Live with its gap named.

Before removing a closed row, append its receipt with
`scripts/task-state.ts board-log <absolute-board> <event.json>`.
Include `id`, `at`, `task` and `result`. For Workflow closure also include
`workflow_id` with its exact `wf_` ID and `status` with its terminal value.
For V2 closure put the task ID, child thread ID and read-back terminal value
in `result`; omit `workflow_id` and `status`, since this helper only accepts
Workflow IDs and drops unrecognized fields. A per-PR orchestrator's closure
`result` names its `threadId`, accepted handback state and settle readback. A
PR row's closure `result` names the PR URL, final PR state, watch stop and
worktree retirement state under
[[wiki/systems/sats-pm-visible-swarm#T3 Code children, Victor 2026-10-07]],
Workspace. Historical prose alone is not terminal proof. Preserve all prior
`BOARD-log.md` bytes. Each layer's orchestrator alone writes its own board and
log, and reads a child layer's board without writing it; the helper grants no
writer lease.

When the user replaces the objective, record the replacement brief and retire
the old Plan before the next dispatch. Reconcile Live through the swarm's
Roles and readiness section. Old held items stay out of the new queue unless
the replacement brief names them.

On compaction or takeover, read the header, Live, pointer journals and
`BOARD-log.md`, then continue authorized work; settled decisions live in the
header. Suggest a fresh session only when Victor starts an unrelated
objective, after writing its board and handoff. Token count, context size,
cost, time and attempt counts never trigger one.

### Workflow drift helper

Use `task-board-nudge --register <absolute-account-directory> <session-id>
<pointer.json>` to bind the existing hook to a board:

```json
{
  "board": "/absolute/work/lane/BOARD.md",
  "journals": {"wf_run_id": "/absolute/account/session/workflow/run/journal.jsonl"},
  "runtime_status": {"wf_run_id": "/absolute/work/lane/runtime-readback.json"}
}
```

Use runtime-returned journal paths. Optional `runtime_status` entries contain
`{"workflow_id":"wf_run_id","status":"running"}` or a terminal status.
Refresh them from runtime evidence. A start record or elapsed time does not
prove activity. Update the pointer when runs or objectives change; it searches
no other account.

The hook compares Live with ordered started/result/failed journal records.
A runtime `superseded` marker, keyed terminal runtime readback or keyed
parent closure receipt also closes a run. It reports terminal runs left in
Live, verified running runs missing from Live and unverified journals. Open
calls without current running evidence are unverified. Reconcile those local
records; the hook never changes the board, contacts children or sends wakes.

This hook covers Workflow `wf_` IDs only. Reconcile V2 tasks through the
swarm's Orchestrator wake and fill section. Extending the helper requires a
code change in `scripts/task-state.ts` and `task-board-nudge`.
`install-task-board-nudge --check` inspects both Victor Claude accounts;
`--install` changes them only during approved rollout, preserving other hooks
and settings. `--claude-dir <path>` selects one account. Node 22.18+ is required;
the hook stays silent without it. Historical migration modes are in
`git show 8b42da5f:Agent-Shared/knowledge/wiki/systems/task-state-and-board.md`.

## Monthly canon prune report

`canon-prune-report.timer` on Framework writes its report
(`knowledge/_meta/prune-YYYY-MM.md`) into the materialized live tree, so that
output is non-authoritative until the script's owner repairs it.
Canonical reports must follow [[wiki/systems/agent-shared-victor-vault-auto-push#Current contract (2026-10-20)]] item 1, Write path.
Read the latest landed report through item 6, Read path, before cleanup or
size work on adapters or `wiki/systems` pages. Letting the report apply fixes
needs a new approved brief. The 2026-10-24 timer and script readback is in
`git show 8b42da5f:Agent-Shared/knowledge/wiki/systems/task-state-and-board.md`.
