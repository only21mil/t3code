---
title: Sats visible swarm standard
aliases: ['Sats PM and visible swarm standard', 'visible swarm', 'single spawner']
created: 2026-10-01
updated: 2026-10-25
verified: 2026-10-05
type: system
status: active
tags: [agent-system, workflow, decision]
sources:
  - 'Victor 2026-10-25 10:47 PM CT approved the rule audit (research/gate-rethink-audit-20261025/RECOMMENDATIONS.md at 75d859c4), row C8'
  - 'Victor GO 2026-10-25 8:28 PM CT; Sats amended brief v2 8:54 PM CT (91c463b8): finite planned work, comparable lane sizes, review convergence and stop-notice ownership; RCA-SOURCES.md, F-D grokbot-rca-straggler-sources-20261025'
  - 'Victor 2026-10-25 18:00 CT: fold Grok-launched thread behavior into the same canon as his threads; keep launch mechanics separate and briefs task-specific'
  - 'Victor 2026-10-25 17:59 CT, same report-out task: explicitly check fill against § Worker cap at every T3 wake and fill while ready independent work waits; launch prompt points here and reports N/C'
  - 'Victor 2026-10-25 17:46 and 17:47 CT, grokbot-report-out-fix-20261025: Grok-launched T3 threads use the visual and Ben Davis report-outs too; § Orchestrator wake and fill points every T3 wake to the report-out standard'
  - 'Victor 2026-10-25 4:41 PM CT and 4:58 PM CT, nested V2 design (lane canon-nested-v2-and-cc-providers-20261025, T3 mcp:416dd0fd): master and per-PR V2 orchestrator threads, one PR per worktree, a per-thread delegate ceiling for T3 V2 threads filled when work is ready (§ Worker cap), master opens and watches PRs, fresh same-worktree CI repair, per-layer settlement, master final status read; Sats parent scope ruling (lane task swarm_scope_repair): that ceiling covers T3 master and per-PR threads only, outside-T3 and host capacity unchanged'
  - 'Genesis 2026-10-25, steer relay incident (F-D main d9ddd550, 1:46 PM CT): thread_not_sendable then an auto resend queued at ordinal 687; § Human message delivery now owns steer, retry steer, queue to the head or promote to steer, and § Check before launch points to it'
  - 'Sats 2026-10-25, applied by lane-notice-direct-https-20261025, cd7414e9: the terminal send runs the local sats-lane-notice send by direct HTTPS on mbp, mini, yoga, f13pro and fd, M3 relay pending (§ T3 terminal send routes and receipts)'
  - 'Lane fleet-token-audit-20261025 (T3 mcp:bd61df73), Sats 2026-10-25 12:56 PM CT item A: two settle sends to F13 Pro thread f07163de ran on its exhausted muse selection; § Human message delivery now points to the move-thread method in sats-t3-and-review-routing'
  - 'Sats 2026-10-25 12:03 PM CT via Hash, from Genesis''s settle audit (t3-e2771e52 AUDIT.md): children settle before their parent (§ Settle on finish, Eligible); 033de8df settled at 14:09Z, its 13 children at 15:07Z by an outside client'
  - '[[wiki/archive/canon-cleanup-core-changelog-2026-10-25]]'
confidence: high
owner: sats
authority: Sats swarm roles, creation, workspace, capacity, wakes, child lifecycle, briefs, reports, registry and acceptance
---

# Sats visible swarm standard

Swarm and herd mean coordinated work toward one goal. This page owns
orchestration for every Sats harness and machine. Load it before planning or
dispatching parallel work, acting as a lane, steering a worker, accepting a
report or closing a swarm. It grants no permission change, credential,
service configuration or external message, and it does not reach into another
person's or agent's scope. § Child permissions passes an orchestrator's
existing permissions to its children and grants nothing new.

- Grok seats: [[wiki/systems/grok-core-rules-2026-10-14]] and
  [[wiki/systems/grok-routing-table]].
- T3 models, effort and reviewers: [[wiki/systems/sats-t3-and-review-routing]].
- Review acceptance: [[wiki/systems/sats-review-and-babysit]].
- Where work runs (T3 thread or direct AUTO lane): § T3 scope.

## Roles and readiness

**Splitting** (Victor ruling 1, 2026-10-18). Split work only into truly
independent parts: parts that need no other part's result and write no
overlapping files. Size lanes by source size (for example, line count),
affected callers and proof burden, not by area alone. Split large read-only
areas into disjoint questions before launch; combine small related areas.
A cohesive outcome stays one lane through production,
review and repair. Swarm size follows § Worker cap.

Production runs one fresh agent per independent part in parallel. Root
integrates the parts. A producer runs its own preflight and its brief's
Verification check pack. Review splitting, rounds and follow-ups follow
review-and-babysit § 2; reviewer selection follows
[[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]].

A work item is one deliverable with its own produce, review and repair
phases; a task is one worker's assignment under one brief. Independent work
items run side by side (Victor, 2026-10-04). A work item waits on another only
when it needs that item's result, shares its write scope or integration
target, or needs the same exclusive device, computer-use session or pending
approval. Scheduling follows § Orchestrator wake and fill, Victor 2026-10-22.

Each objective has one recorded launch owner. Only that owner launches it; a
relaunch or parallel lane needs the owner's new recorded decision.

Root launches only dependency-ready work with a complete brief, supported
tools, an inspectable route and a nonconflicting write scope. **One writer**
owns each write scope and each shared mutation scope. Writers that share a
checkout keep strictly non-overlapping paths the brief names; work on the same
files stays with one writer. Integration into a shared branch or config is
serialized under one writer. Read-only lanes may share inputs. Registry
writing follows § Registry and closure.

**Steering.** A new task or new scope gets a fresh worker created by root.
Within the same task, root may send a bounded clarification only through a
tool whose documented contract delivers guidance to the same writer. If a
message would start a new turn or copy, or its semantics are unknown, root
confirms the old writer terminal before launching a corrected fresh brief.
Ordinary progress is no reason to restart.

## Runtime binding

### Fleet orchestration standard, Victor 2026-10-11

This section owns worker creation, vehicles and runner inspection. Read it
before dispatch. Routing comes
from [[wiki/systems/sats-t3-and-review-routing]]. Read that page from GitHub
main under [[wiki/systems/agent-shared-victor-vault-auto-push#Current contract (2026-10-20)]]
item 6, Read path; use a local copy only after its currency proof.

- **Nested V2 layers** (Victor 2026-10-25 4:41 PM CT). In T3 a lane has one
  master V2 orchestrator thread, its main thread. The master opens one per-PR
  V2 orchestrator thread for each PR, bound to that PR's worktree
  (§ T3 Code children, Workspace), and starts delegates for work outside any
  PR. A per-PR orchestrator starts the delegates and reviewers for its PR in
  that worktree and returns any further PR to the master. A lane with no PR
  is a master with delegates. Outside T3 one root starts every worker and
  reviewer directly.
- **Root** on this page is the orchestrator that started the child in
  question: the master, a per-PR orchestrator or an outside-T3 root. Each
  root owns briefs, registry, replacements, review routing, terminal
  reconciliation, integration and final acceptance for its own children. The
  master alone opens PRs upstream and watches them
  ([[wiki/systems/t3-upstream-pr-lanes#PR watch, Victor 2026-10-25]]),
  writes the objective's owner registry rows (§ Registry and closure) and
  delivers to Victor. Stop-report ownership follows
  [[wiki/systems/task-notices-and-reporting#Terminal self-report]].
  A per-PR orchestrator is bound to its master through
  its brief and reports to it natively (§ T3 Code children, Workspace,
  Handback).
- Only an orchestrator layer (the master, a per-PR orchestrator or an
  outside-T3 root) starts children. A delegate or reviewer starts no agents,
  subagents, workflows, delegated tasks or threads and returns further
  decomposition to its root. Its brief names that role and root as facts
  (§ Brief contract); this bullet owns what the role does. No passive herd
  overseer runs: every orchestrator layer owns work and its own children.
- A seat that hands an objective to a T3 thread or AUTO lane makes that
  launched orchestrator its root. The launched agent owns its objective and
  may write its plan; for Grok dispatch the seat supplies intent, the AUTO
  lane writes PLAN.md and the seat monitors.

Vehicles:

- In T3 Code, every delegate (production, review, repair, verification,
  computer use, single-child work) starts through T3 Orchestrator V2
  `delegate_task` on every harness, under § T3 Code children. The master
  opens per-PR threads under § T3 Code children, Workspace.
- Outside T3 Code: Claude Code uses § Claude Code Workflow binding; Codex uses
  root-owned `codex-workflow` phase specs; Cursor runs a single worker until a
  compliant route exists; other harnesses keep their adapter's vehicle.

Inspection outside T3: for Codex, register each `codex-workflow` run's run ID,
worker label and task path, assigned files, PID and session ID when returned,
requested and observed model and effort, progress/status/meta/output paths
and terminal state. Inspect through `progress.md`, `progress.json`,
`status --json`, `agents/<label>/meta.json` and output files. Keep runner
processes attached to root's active turn and reconcile each before closing.
Runner workers are not sidebar agents; record their process and artifact
inspection apart from UI visibility. On Claude Code, native Agent IDs are the
inspection route, plus Workflow IDs and their progress tree when a Workflow
runs. Visibility requirements: § Shared runtime rules.

Source saved, UI visible, execution terminal, reviewed, accepted and deployed
are separate claims. Family scopes get this standard through their own
instruction distribution, without Victor's private canon.

#### All Sats and family agents use AUTO on every machine

All Sats and family agents on all machines use Codex Auto or Claude Auto. In
T3, use V2 with the routing owner's AUTO target. Outside T3, root-owned
Workflow and `codex-workflow` use the hub `AUTO_CODEX` or `AUTO_CLAUDE` route.
Transport and accounts:
[[wiki/systems/sats-model-tier-provider-policy#Accounts and transport]].
Personal settings keep the selected person's scope within AUTO and authorize
no personal provider or account pin. A subscription account name never
identifies the caller's person or scope. This is the required route, not proof
that every saved config or running agent complies.
Source: Victor 2026-10-12, direct.

#### Local validation

This subsection owns local validation for every lane, producer, reviewer and
repair. Record the lane's full pre-fix commit SHA in its inputs before editing
and keep it across repairs; a remote branch name or stale merge base is not
that pin.

Run the smallest direct file, test or affected-package commands that prove
the change. Bare `check:changed` and whole-workspace Knip do not run locally;
an explicit ref alone does not make a wrapper focused. CI owns broad lint,
typecheck, dependency analysis and full suites. Record results beside the
preview; an interrupted or unrun check is not a pass.

#### Step cleanup

When a step ends, its lane stops the processes, dev servers, apps and browsers
that step started (TERM, never KILL) and checks they exited. Anything the next
step needs gets a named owner in the lane record. Work the lane does not own is
reported, never stopped. Tools:
[[wiki/systems/lane-milestones-and-stall-watchdog#Heavy jobs and background stops]].

#### Worker cap

This subsection owns worker capacity. Each declared orchestrator thread runs
at most its profile's ceiling of active workers, reviewers included, on every
host and harness: Claude Code, Codex, T3 `delegate_task` children, CLIProxy
AUTO lanes, Muse and any other. Only ready work fills a slot; a free slot
never creates work. Admission follows § Orchestrator wake and fill.

- Victor/Sats T3 V2 orchestrator threads, the master and each per-PR thread
  (§ Fleet orchestration standard, Nested V2 layers): 20 active delegates per
  thread. Fill follows the finite done condition in § Orchestrator wake and
  fill (Victor 2026-10-25
  4:41 PM CT: "Each thread has a 20 delegate ceiling that is encourage to use
  it all when tasks are availitble").
- Victor/Sats profiles outside T3 (Claude Code native Agent or Workflow,
  Codex, CLIProxy AUTO lanes, Muse and any other): 40 active workers per root
  orchestrator thread (Victor, 2026-10-24 11:52 AM CT), unchanged by the
  nested V2 design.
- Mason/Alpheus profiles: 10 per thread on every machine.
- Rachel/Archimedes profiles: 10 per thread on every machine.
  Both family caps: Victor, 2026-10-23, as admin of the family scopes. Both
  family canons receive this page through `canon-family-project`
  ([[wiki/systems/canon-sync-fabric-2026-09-24#Family projection]]).
- Host ceilings (Victor, 2026-10-21): 100 concurrent agents on
  framework-desktop (Victor, 2026-10-25 9:05 PM CT); 40 on Yoga,
  victors-macbook-pro (M5), both F13 Pros and the Muse VM;
  20 on the Mac Mini, Mason's M3 MBP and Rachel's MBA. The lower of the host
  ceiling and the profile cap binds.

A profile cap is per thread. The 20 is not a budget for the master's whole
tree: each per-PR thread has its own 20. A host ceiling is the separate host
limit above; the nested V2 design changes neither its numbers nor how it
counts.

The cap belongs to the declared person/agent profile and its orchestrator
thread. It is not per account, machine, OS login or shared hub. There is no
separate total-tree cap and no separate heavy-job cap (Victor, 2026-10-23).
Select and declare the profile before private reads or worker admission;
ambiguous scope fails closed. Source and memory access follow that scope, not
the ability to sudo.

**Counting.** Count every running worker, including work already running when
a thread starts or a rule changes. Queued and finished children do not count.
A running per-PR orchestrator thread takes one of its master's slots; its own
delegates take its own slots, never the master's.
A thread over its cap kills none of its
running workers and admits no new one until it is below the cap. Reported
agent counts (a launch's swarm size, the board's agent table) cover producers
and workers only: 1 for a normal lane or Grok-only work, one per truly
independent producing part. List the orchestrator and reviewers separately;
reviewers still take cap slots (Victor 2026-10-18 4:55 PM CT).

**Settings.** Each Victor/Sats Claude account's `settings.json` env sets
`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` and
`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, and each Codex home sets
`[agents] max_concurrent_threads_per_session`, to the host ceiling above.
Rachel/Archimedes and Mason/Alpheus accounts set all three to 10. V2 children
run outside those variables, so the owning orchestrator counts them itself. A
saved setting proves neither a host's live value nor session uptake.

M3 is a shared always-on server: Sats40 is the desired default there, with
Mason10 and Rachel10 selectable by their own scope. That is desired state, not
proof of an applied default or session uptake. Private Victor canon is never
copied into a family profile. Machine roles: [[wiki/systems/fleet-machine-roles]];
machine access:
[[wiki/systems/sats-vs-family-agent-scope#HARD: full unrestricted machine access, Victor 07:34 CT 2026-10-13]].

#### Orchestrator wake and fill, Victor 2026-10-22

This subsection owns waking, turn ends, admission and what an orchestrator
tells Victor on each wake, on every harness and in T3. A herd orchestrator
starts its children in parallel calls and waits. It ends its turn where its
harness wakes it on a child's finish, and keeps the turn open where nothing
does (Codex CLI row). It wakes on a child's finish (for a per-PR thread, its
handback send to the master, § T3 Code children, Workspace), Victor's
message, a native PR-watch update, or a stall or failure event from `wf-stall-watch`
(§ Claude Code Workflow binding), and on nothing else: it never polls and
runs no timer of its own. PR-watch response belongs to
[[wiki/systems/t3-upstream-pr-lanes#PR watch, Victor 2026-10-25]].
The F-D stall watchdog is removed, so nothing else reports a stalled lane.

- **Every wake runs one full pass.** Read the board, the run table and
  delivered results. Triage failed PR checks under the PR-watch owner before
  admitting planned independent work. Advance every ready lane: publish where
  Victor pre-approved it, next review round, repair, rerun. At every T3 wake,
  check running delegates against § Worker cap and fill up to that cap only
  while planned, ready independent work is waiting, admitted through the
  supported native task route. Fill-to-cap and keep-N instructions apply
  only to the accepted plan: planned slices plus one named checker pass.
  Once those finish, start no new delegates; synthesize the result and put
  remaining gaps in the DONE report. Unused slots, candidate-count aims and
  reserve findings create no work. New investigation needs the report
  owner's scope decision; failed mandatory checks and evidenced blockers
  retain their blocking disposition. Readiness and
  the authorized objective decide what runs; free slots never create
  assignments. A free slot may prepare an already held or blocked
  item (research evidence, draft candidates, tests, exact gated diffs or
  commands); preparation stops at the gate and starts no new objective. A
  Victor hold pauses the lanes it names until he says resume. In T3, native
  PR-watch notices queue behind the active run. After one pass of triage and
  dispatch and the report-out below, end the turn; delegated execution and
  later phases continue in their own turns so queued notices can run.
- **Wake report-outs.** End every T3 wake with the in-chat report-out under
  [[wiki/systems/task-notices-and-reporting#Report-out standard (all machines and harnesses in T3 Code)]]. Answer any Victor message
  first (§ T3 Code children, Turns). Other harnesses' turn ends follow the
  table below; bot messages keep
  [[wiki/systems/task-notices-and-reporting#Channels and shape]].
- **T3 status reads.** Read `task_status` for a child after its completion
  notice, for a named cancellation or recovery check, or in the master's one
  final reconciliation before handback (§ Settle on finish, Eligible); any
  other pass does not sweep every child. A terminal `task_status` read, or a full terminal result read
  with `t3_thread_read`, acknowledges automatic delivery. Before calling a
  notice lost, inspect `t3_queue_list` once; a completion queued behind the
  active turn needs that turn to end.
- Child handback and execution reconciliation follow § Progress and recovery.

| Harness | Children start with | A child's finish wakes root through | Turn end |
|---|---|---|---|
| T3 Code, any provider | `delegate_task` (§ T3 Code children); the master opens per-PR threads with `t3_thread_launch` (§ T3 Code children, Workspace) | T3's completion notice; then `task_status` for the named child. A per-PR thread's handback send to the master; unobserved until a canary runs | End every wake with the interim report-out under [[wiki/systems/task-notices-and-reporting#Report-out standard (all machines and harnesses in T3 Code)]]. |
| Claude Code outside T3 | Agent tool, `run_in_background: true`; Workflow only on opt-in (§ Claude Code Workflow binding) | the background task notification; Workflow completion and `wf-stall-watch` events | End the turn with no message. Not yet observed outside T3. |
| Codex CLI outside T3 | root-owned `codex-workflow` runner; native `spawn_agent` (`adapters/sats-codex-agents.md`) | Runner: nothing wakes a closed turn, so root keeps the exec session attached and its turn open ([[wiki/systems/codex-workflow-swarm#Operating notes]]) and reads the runner's files (§ Fleet orchestration standard, Inspection). Native agents: `wait_agent` under the adapter. | The turn stays open while children run; no text between waits. |
| OpenCode | Task with `background: true`; parent lane launched with `SAT_PARENT_LANE=true` (`adapters/sats-shared-orchestration.md`) | the Task completion notification; never `background.wait`, sleep or poll | End the dispatch turn after launch. Unverified whether OpenCode forces a final line. |
| Cursor | none outside T3: a single worker (`adapters/cursor/sats-cursor.mdc`); inside T3 the T3 row applies | nothing | Not applicable. |
| Grok Bot seats | AUTO lanes through `sats-lane-launch`, or one T3 thread through a T3 connector (`skills/grok-fleet/t3-orchestrator-prompt/SKILL.md` § How to reach T3) | the lane's completion classifier and `sats-completion-notify` to the bound `--recipient` ([[wiki/systems/cliproxy-spawn-skill-2026-10-07#Launch recipe: systemd-run + native completion hooks (2026-10-07)]]); a T3 thread's terminal self-report; a shell-gated check ([[wiki/systems/grok-bot-fleet-seats]]) | A seat's chat carries DONE, a real BLOCKED line, NEEDS-VICTOR asks and real DIED alerts only. Unverified whether a seat turn can end with no line. |
| Headless AUTO lanes | none; the producer lane hands its review to a T3 thread, except X lanes, and owns repair and re-review handoffs (review-and-babysit `vehicles/other-harnesses.md` § AUTO lanes on F-D) | nothing: the lane runs to its end | No chat. Milestones go to `MILESTONES.log`, the result to RESULT.md, then one terminal self-report. |

The T3 upstream PR pass is in [[wiki/systems/t3-upstream-pr-lanes#Orchestrator]].

#### T3 scope

Every T3 thread follows the same canon, whoever starts it. Task models and
effort follow [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]].
Wakes and fill follow § Orchestrator wake and fill and § Worker cap; chat
reports follow [[wiki/systems/task-notices-and-reporting#Report-out standard (all machines and harnesses in T3 Code)]].
Briefs follow § Brief contract. A title prefix or launch connector changes
none of that behavior. Grok-specific launch mechanics stay in
`skills/grok-fleet/t3-orchestrator-prompt/SKILL.md`.

T3 Code runs project builds, repo code and long multi-phase work. Thread and
workspace selection follow § T3 Code children, Workspace. Repair, review,
babysit-to-green and retry loops stay with the selected unit.

Other work Victor may want to question or steer, RCA, research and canon
included, also runs as a T3 thread that answers his questions and steers after
DONE (Victor 2026-10-18 9:01 PM CT; settle under § Settle on finish). A direct
Codex Auto or Claude Auto worker that writes its result to a file is only for
mechanical checks or scripted steps; its brief says why it is headless, and it
runs its loops inside its own AUTO lane. The canon lane recipe is in
`adapters/CLAUDE.md` § Dispatch and lifetime.

When Victor asks for T3, the work goes to T3. X work never runs in T3: its
drafting, review and posting stay headless, owned by Lightning
([[grok-routing-table]] rows 4 and 4p; review-and-babysit § Vehicles).

The launching seat selects the unit, then runs § Check before launch. The
seat launches the master; the master splits the work, runs its delegates and
opens the per-PR threads (§ Fleet orchestration standard). The seat opens no
per-leg threads.

- Launch steps, T3 access, the seat sign-in HOLD and wedge handling: skill
  `t3-orchestrator-prompt`
  (`Agent-Shared/skills/grok-fleet/t3-orchestrator-prompt/SKILL.md`), § How to
  reach T3 and § Steps.
- Searches and remote commands: `adapters/sats-shared-common.md` § Working style, Searches and remote commands.
- Shell-gated waits on a thread or gate: [[wiki/systems/task-notices-and-reporting#Quiet, waits and reads]].
- How a thread's finish reaches its launching seat: § Orchestrator wake and fill.

#### T3 terminal send routes and receipts, Victor 2026-10-20

Policy, key and delivery belong to
[[wiki/systems/task-notices-and-reporting#Terminal self-report]]; integration
belongs to [[wiki/systems/lane-milestones-and-stall-watchdog#Terminal delivery integration]].
This subsection owns only how a T3 thread's terminal send runs and how the
thread reads its receipt.

- The terminal send runs the local `sats-lane-notice send` on the thread's own
  host, which posts by direct HTTPS: no `ssh` hop and no `printf %q` quoting.
  It is installed on mbp, mini, yoga, f13pro and fd; its README holds the
  command line (Sats 2026-10-25, applied by lane-notice-direct-https-20261025,
  cd7414e9). M3 (`m3mbp`) still runs its SSH relay to F-D and is the one host
  pending. The Muse VM route ([[muse-vm-t3-route-2026-10-10]]) is unproven
  until its first canary.
- Put the send's one JSON receipt line and its exit code (rc) in the final
  message and in RESULT.
- The receipt counts as DELIVERED only under § Terminal self-report: an
  authenticated successful receipt matching the event ID, the full
  environment/thread/generation/state key, body hash and recipient, and naming
  the Sats run it started. A `"sats_receipt":"DELIVERED"` field without that
  match is not delivery.
- `"requeued":true` means the bounded outbox holds the event under its
  recorded key and owns its retries. Do not rerun.
- Any other result, a missing receipt or a NOT_SENT included, allows one
  rerun in the same turn for the same recorded event: same key, same frozen
  event ID and payload bytes. The rerun neither gets nor advances a key.
  Changed bytes under that key are a conflict, not a new send.
- If the rerun shows neither a matching DELIVERED nor `"requeued":true`, the
  outbox keeps the event, the final message ends with
  `NOTICE-UNDELIVERED <receipt or rc>`, RESULT records the gap, and the thread
  does not self-settle.

#### Settle on finish, archive after one week

- The shell sweep implementation is victor-vault
  `tools/grokbot-thread-status/`; its README owns invocation, receipt reads
  and the finish predicate. It writes a private per-host status file and
  uses T3's own settle action with a fresh eligibility check and readback.
  An old terminal receipt never qualifies a newer run. A missing transport
  field or incomplete listing keeps a thread ineligible. CLI status is a
  partial read-only view; automatic settlement needs the supported complete
  MCP route. Source publication does not prove per-host activation.
- **Eligible.** The master self-settles a DONE thread once its done check,
  applicable review and required terminal delivery pass and nothing remains
  for Victor. Each layer settles its own children as each finishes, in the
  turn it finished (§ Progress and recovery, Interim V2 containment): a
  per-PR orchestrator its delegates, the master its delegates and each
  per-PR thread once it accepts that thread's handback. Before its handback
  the master reads `task_status` once for each delegate it started and
  `t3_thread_read` for each per-PR thread it opened, settles any finished
  child still unsettled (a missed completion wake leaves one), and stops each
  PR watch it hands back to Victor
  ([[wiki/systems/t3-upstream-pr-lanes#PR watch, Victor 2026-10-25]]). A parent
  never settles while an owned finished child is unsettled (Sats 2026-10-25
  12:03 PM CT, from Genesis's settle audit: 21 mains settled before their
  children that day). An open PR it still watches, an unanswered
  Victor message, open decision or approval, unresolved blocker, promised
  follow-up, pending check or pending child keeps it active. On a host without
  the generation-bound notifier installed and read back, the dated fallback in
  [[wiki/systems/task-notices-and-reporting#Terminal self-report]] meets
  required delivery, recorded unverified.
- **Exception.** The T3 Code Nightly Upstream PRs lane stays open as a
  standing contribution lane and does not self-settle (Victor 2026-10-23
  6:50 PM CT, relayed by Sats).
- **Settle.** Recheck eligibility. Settle each finished child still
  unsettled with `t3_thread_organize` `{"action":"settle","threadId":"<child>"}`
  and read back `settled=true`; confirming a child terminal does not settle it.
  Then make `t3_thread_organize`
  `{"action":"settle"}` with no `threadId` the turn's last planned tool call.
  It returns `settlesWhenTurnEnds=true` and takes effect when the turn ends; a
  failed or interrupted turn, or a queued message, leaves the thread active.
  Final `settled=true` needs a supported readback after the turn completes.
  Runtime race behavior is unproved until real activation canaries run.
- **Steer after settle.** If a Victor message is steered into the turn after
  the settle call, answer it first and recheck. If anything now makes the
  thread ineligible, call `t3_thread_organize` `{"action":"unsettle"}` with no
  `threadId` before ending the turn. If the steer is resolved and every check
  passes, a final settle may run as the last planned call. Never interrupt the
  shared server to cancel settlement.
- A chat line saying DONE or settled is not a lifecycle action. Settlement
  and stop reporting are separate under
  [[wiki/systems/task-notices-and-reporting#Terminal self-report]].
- **Reopen.** A settled thread stays reusable. A new Victor message reopens
  work there and is answered first. Terminal generation allocation follows
  [[wiki/systems/task-notices-and-reporting#Terminal self-report]]; reopening
  alone keeps the prior generation, body and receipt.
- If a settle action or required delivery receipt is unavailable, leave the
  thread active and record the exact gap.
- **Opener settles.** The thread or bot that started a T3 thread settles it
  with `t3_thread_organize` `{"action":"settle","threadId":"<id>"}` as soon as
  it accepts the thread's DONE, without waiting to be asked. A bot settles only
  the master it started; each layer settles its own children under Eligible
  (Victor 2026-10-25 8:26 AM CT, 10:03 AM CT and 10:17 AM CT).
- **Supersede** (Victor 2026-10-23 9:13 PM CT). A launcher that starts a
  replacement thread first names the replacement `threadId` in the old thread,
  then settles the old thread with `t3_thread_organize`
  `{"action":"settle","threadId":"<old>"}`, whatever its last report, DONE or
  BLOCKED. A thread that learns a named replacement supersedes it sends its
  terminal report, then makes `t3_thread_organize` `{"action":"settle"}` with
  no `threadId` its last tool call, whatever its verdict. Settling is not
  acceptance and changes no result.
- A settled thread is archived after one week. Settling and archiving under
  these conditions need no approval. Worktree retirement follows § T3 Code
  children, Workspace.

#### Check before launch

Before opening a master T3 thread, identify its incident or topic and its unit
under § T3 Code children, Workspace. Check the owner registry and existing
lane or sweep result files for an open orchestrator on that incident or topic,
even when a related leg has a different title, repository or host. Steer that
orchestrator under § Human message delivery; related legs become its children,
not new roots. Use `t3_thread_search` for a named candidate. Cross-thread or
cross-host inventory follows
[[wiki/systems/sats-model-tier-provider-policy#Token economics, Victor 2026-10-20]];
read its result file before deciding to launch. An uncertain launch is checked
there too before any retry, using the same host and objective.

Restart a dead thread only on its launch owner's recorded decision
(§ Roles and readiness).

After every launch, verify that the first run started and the thread shows the
full brief. If either check fails, resend the full brief once through
`t3_thread_send` on that thread and verify again. If it still fails, report
HOLD with the thread ID and open no second thread. A returned thread or run ID
proves neither.

#### Universal milestones and stall watchdog, Victor 09:07 CT 2026-10-13

What gets reported and to whom: [[wiki/systems/task-notices-and-reporting]].
Launch and hook mechanics:
[[wiki/systems/lane-milestones-and-stall-watchdog]].

### T3 Code children, Victor 2026-10-07

The T3 transport is `delegate_task` from the `t3-code` MCP server, under the
harness-normalized name (for example `mcp__t3-code__delegate_task`). Every
orchestrator inside T3 starts every delegate through it, even when a native
agent supports the model; this overrides T3's hint to prefer native
subagents. Per-PR threads open under § Workspace instead. Where the
harness does not expose the T3 tools and `T3_ACP_MCP_NODE` is set, call the
same tools through the ACP `acp-mcp-call` fallback. Creator roles stay with
§ Fleet orchestration standard.

- **Questions.** A question or approval request from a child or helper (a
  `delegate_task` child, a thread it opened, an AUTO lane) goes to the
  orchestrator that opened it, not to Victor or Sats (Victor 2026-10-25
  8:27 AM CT). The orchestrator answers from its brief, canon and Victor's
  standing decisions: `t3_pending_request_list`, `t3_pending_request_read` and
  `t3_pending_request_respond` for a child's pending question, `t3_thread_send`
  for an opened thread. Only what it truly does not know, or one of Victor's
  own gates ([[grok-core-rules-2026-10-14]] rule 3 and the Safety gates in
  `adapters/sats-shared-common.md`), goes up to Victor through the
  orchestrator's own report route.
- **Model and effort.** Launch and read back every child, gather included,
  under [[wiki/systems/sats-t3-and-review-routing#T3 routing, Victor 2026-10-17]],
  Binding and readback. Every child's `title` starts with its real model and
  effort under [[wiki/systems/sats-model-tier-provider-policy]] § Sidebar
  names.
- **Reviewers.** Each review and babysit round selects reviewers under
  [[wiki/systems/sats-t3-and-review-routing#Review routing, Victor 2026-10-17 20:14 CT]];
  review-and-babysit § 2 owns the count and the skill owns rounds.
  Reviewers launch full access with review-only in their brief
  (review-and-babysit § 2), and root takes the skill's content manifest
  (§ Non-writing proof, `review-fingerprint`) before launch and again once
  `task_status` shows the reviewer terminal. A changed manifest voids the
  review.
- **Rounds and tracking.** Track each child by `taskId`; `childThreadId` is
  backing storage, not a continuation route. Each review round is a new
  `delegate_task` with its own `clientRequestId`, stable across retries of
  that round, carrying the original brief, prior findings, responses and
  unresolved objections. A new task preserves the logical reviewer assignment
  and focused re-check scope under review-and-babysit § 3 Repair and rounds.
- **Child finish.** Settle each child in the turn it finishes, under
  § Progress and recovery, Interim V2 containment.
- **Steering.** Follow § Roles and readiness and § Human message delivery, and
  read the live schema before steering.
- **Turns.** Reply-first applies on turn entry and whenever a human steer
  arrives during a running turn, before the next task action. Answer the
  question or decision directly in 1-3 lines; an acknowledgement, progress
  update or promise to answer later does not answer it. If evidence is
  missing, state the known result, the specific uncertainty and the next
  check. Answer every still-unanswered Victor item, newest first, then apply
  his steer before continuing. A bot batches relays only after Victor's items
  have answers. After DONE the thread answers his questions and steers,
  settled or not.
- **Inspection.** Inspect a child with `t3_thread_read` on its
  `childThreadId` for state and `t3_thread_configuration` for model and
  effort, and record whether its card opens as `observed`, `unverified` or
  `unavailable`. While cards do not open, keep fanning out with
  `t3_thread_read` as the inspection route (Victor, 2026-10-07).
- **Close.** Report a closeout table: one row per child with `taskId`,
  `childThreadId`, `title`, requested and read-back model and effort, and
  final `task_status`, plus failures and dropped work. Board rows follow
  [[task-state-and-board]].
- **V2 unavailable.** When neither MCP nor ACP transport reaches V2, report
  HOLD with the failure evidence. Native agents, Workflow, codex-workflow,
  OpenCode Task and direct CLI/API workers never replace V2 inside T3.
- **Cursor.** Provider authentication and route eligibility follow
  [[wiki/systems/sats-model-tier-provider-policy#Accounts and transport]].

#### Workspace

This is the only full statement of the T3 workspace rule. Other pages link
here.

Each unit of work that needs its own branch, such as a PR, gets one worktree
of a Git project, and a worktree holds one PR only (Victor 2026-10-25
4:41 PM CT). Create as few worktrees as the work needs; work that needs no
branch of its own creates none. The master opens each unit's per-PR thread
through `t3_thread_launch`: find the unit's existing worktree by branch with
`t3_worktree_list` and bind through `workspaceStrategy: existing_worktree`;
use `workspaceStrategy: worktree` once for a new unit. A non-Git root is
BLOCKED; the generic `~/work` directory is not a Git project. Reuse an active
thread covering the same unit under § Check before launch. Another branch is
another unit, never another child's checkout.

Every agent on the unit uses that worktree. `delegate_task` children use the
default shared checkout, with no `isolation: "worktree"` and no worktree path
in briefs or records. Writers share it under § Roles and readiness, One
writer. Threads Victor starts in the app use `defaultThreadEnvMode: worktree`.
An opener orchestrates its opened threads through `t3_thread_read`,
`t3_thread_wait` and `t3_thread_send`; their questions and settlement follow
§ T3 Code children, Questions and § Settle on finish.

**Handback.** A per-PR orchestrator is bound to its parent by the master
`threadId` its brief names (§ Brief contract). It reports natively: its final
thread message carries the finished PR (branch, reviewed head SHA, lane
record path, DONE or BLOCKED), and it sends that handback to the master with
one `t3_thread_send` under § Human message delivery. T3 documents no
automatic wake to an opener when a thread it launched finishes, so that send
is the finish wake; it stays unobserved until the lane's lifecycle canary
reads it back, and the master's final read under § Settle on finish,
Eligible catches a missed one. The per-PR orchestrator does not open the PR
upstream and writes no objective registry row. Its stop-report duty follows
[[wiki/systems/task-notices-and-reporting#Terminal self-report]].
The master opens the PR under the publication gates and owns its watch
([[wiki/systems/t3-upstream-pr-lanes#PR watch, Victor 2026-10-25]]).

**CI repair.** A CI repair that the master's PR-watch triage assigns goes to
a fresh per-PR orchestrator thread bound to the same PR worktree
(`existing_worktree`). Its brief carries the original brief, prior findings
and the CI log. The repair opens no new worktree and is never sent to a
finished child. A fresh delegate may take it only when its launcher's
checkout is that worktree.

**Main thread only** (Victor 2026-10-25 10:17 AM CT). A Grok Bot talks to T3
only through a lane's master, which starts, steers, answers and settles its
own child threads; the bot never steers or settles a child, and fixes a
stuck child by steering the master.

**Retirement.** T3 alone removes a managed worktree and everything in it,
`node_modules` and build outputs included; agents run no `rm`,
`git worktree remove` or cleanup script there. A PR's threads are ready for
deletion, which removes its worktree, once the PR is done: merged, closed, or
handed back to Victor with its watch stopped. Until then the worktree stays
for CI repair. Another finished thread is ready once its work is on main or
a dropped lane's branch is committed. The master reports each ready thread's
title and ID; Victor
deletes it in the UI and T3 removes the worktree. No agent-callable T3 route
removes a worktree: `t3_thread_organize` only pins, snoozes, settles,
archives or marks unread, and `t3_thread_update` changes no workspace. Until
a canary or a T3 feature proves another route, "the PR worktree is removed
when the PR is done" means the master reports it ready and Victor deletes it.
Keep lane records, evidence
and images outside the worktree so they survive. Uncommitted, unpushed or
active work keeps its protection under `adapters/sats-shared-common.md`
§ Scope and writes. Live-user check (Sats 2026-10-25 11:49 AM CT, from
Genesis's missing-worktree RCA; widened to shared paths by Hash, asked by
Genesis 2026-10-25 11:59 AM CT, after a goenv toolchain delete at 11:25 AM
CT), the only statement of it. Run it immediately before every delete of a
worktree, a branch, or a shared toolchain or directory (a goenv or other
version-manager toolchain, a shared cache, a shared work dir), inside T3 or
outside it, per delete, not once at plan time.

- **Thread check**, every delete: run `t3_thread_list` with
  `settled: false` and `includeSubagents: true` on that host's T3, for every
  project and every page, and read each returned thread's `worktreePath`,
  branch and brief (`t3_thread_read`). Skip any path that equals, contains or
  sits inside one of those `worktreePath`s, any branch one of those threads
  names, and any shared path one of those briefs names or its worktree
  references (`timeout 60 git grep -n -F <path>` inside that worktree).
- **Process check**, shared toolchains and directories only: confirm no
  running process uses the path, under `adapters/sats-shared-common.md`
  § Working style, Searches and remote commands, with `timeout` on the host
  that runs it and the explicit path, for example
  `ssh <host> 'timeout 60 lsof -w +D <path>'`. Never root it at `~`,
  `~/work`, `/home` or a multi-lane folder.

Either check finding a user skips the delete, and the deleter reports the
path and the user; a check that errors or times out counts as a hit. The
asymmetry is deliberate: a worktree or branch needs only the thread check,
and a process scan (`/proc`, `ps`, `lsof`) never counts for it, because an
idle unsettled thread has no process; a shared path needs both checks,
because work outside T3 uses it too. No brief, GO wording or "orphaned" label
overrides this rule or the T3-only removal above, the rule canon carried at
`c2564638`. A result that keeps a thread open while deleting its worktree,
its branch or a shared path it uses, or that deletes a shared path a running
process uses, is BLOCKED.

#### Human message delivery

Distinguish accepted, queued, provider-delivered and answered. Every message
an agent sends into a T3 thread (a relay, Victor's question, a settle or other
follow-up) takes these steps with the native T3 tools, and only these:

1. Send with `t3_thread_send` mode `steer`.
2. On `thread_not_sendable`, retry mode `steer` once, immediately.
3. If it still fails, send with mode `queue`, then call `t3_queue_list` with
   `limit: 1`. If the first item is not yours, call `t3_queue_reorder` with
   your `queuedRunId` and `beforeRunId` set to that first item's run ID.
4. If the thread has an active run when you check, call
   `t3_queue_promote_to_steer` with your `queuedRunId` and that run as
   `targetRunId`.

A relay ends first in the queue or steered into the active run, never behind
other queued items. Mode `auto` is not a fallback: with no active run it
equals `queue`, and a thread busy with many short runs (PR-watch wakes, for
example) is almost never caught mid-run, so an `auto` resend lands at the back
of its queue (Genesis incident, 2026-10-25: ordinal 687 behind about 187
queued wakes, about 20 minutes unanswered). Give each send its own
`clientRequestId`, stable across transport retries of that send. `queued` is
not proof the provider saw it. Record messageId, runId, selected mode,
returned delivery, queue position and timestamps. Never interrupt a shared
provider server. When these tools are missing, report a delivery blocker
naming the missing capability. Never retry a rejected stale target. Timeline visibility and
`inputIntent: steer` alone prove neither model receipt nor a queue-setting
root cause. A send runs on the thread's current model; a thread whose model is
out of usage moves first under
[[wiki/systems/sats-t3-and-review-routing#Move a thread off a model that is out of usage]].

### Child permissions, Victor 2026-10-11

1. **Same permissions as the orchestrator.** A delegated child runs with the
   permissions of the orchestrator that launched it, for the task it was
   given: the same runtime mode and tools, the same standing permissions
   (`adapters/sats-shared-common.md` § Safety gates) and every approval Victor
   gave the orchestrator for that task. The brief names any task-specific
   approval so the child can act on it. A child does not ask Victor again for
   something its orchestrator is already approved to do.
2. **What stays the same.** A safety gate the orchestrator is not approved for
   still needs Victor's or Rachel's approval. The child reports it to root
   under § T3 Code children, Questions, root asks once, and the approval then
   passes to the child. The brief still sets the task's limits: a reviewer
   reviews only and writes only its review file, and limits such as "no
   upstream posts" bind. Approval and review stay separate. Scope, privacy and
   secret-handling rules do not change. Upstream and external writes follow
   `adapters/sats-shared-common.md` § Safety gates; a child inherits no other
   publish approval.
3. **Seats and harnesses.**
   The Sats Codex seats, T3 orchestrator threads, Grok Bot seats and Muse, on
   every harness that can delegate.

### Approvals across chats, 2026-10-11

An approval Victor gives in any chat, thread or lane holds for every seat
working that item. A seat that learns of it from the board, the pack, Sats or
another seat acts on it without asking Victor again, and records where the
approval was given (chat or lane, time) in its pack or board. The approval
keeps the scope Victor gave it: the item, the steps and any limits he named.
An upstream or external write carries its receipt across seats under
[[grok-core-rules-2026-10-14]] rule 3 and
[[upstream-pr-go-gate-2026-10-11]] item 3. Source: Victor-approved 2026-10-11, relayed by Sats (paraphrase).

### Shared runtime rules

Before fan-out, bind the current host and harness's actual create, inspect,
message, event/wait, stop and archive operations, and record unsupported ones.
Use the exposed schema and current local documentation; never invent tool
fields, IDs, acknowledgements, lifecycle APIs or frontend behavior. A complete
brief in the supported creation call is enough. The user's explicit request for
separate inspectable tasks may authorize the app's separate-task route where
it is supported.

Every worker has an ID and an opening or inspection route available to the
human. Record inspectability separately from sidebar rendering: `observed`,
`unverified` or `unavailable`. A tool ID or board label proves only what the
tool exposes. If no inspectable route exists, hold further fan-out and report
the exact capability gap; in T3 Code, § T3 Code children, Inspection supplies
the route. Supervise running workers; never substitute hidden execution or
placeholder chats. A root-configured relay exposes its execution and terminal
evidence through its owning agent. On other harnesses, a CLI client or relay is
eligible only if every execution worker it starts meets § Fleet orchestration
standard's creator and inspection contract; the registered Codex runner route
provides process and artifact inspection, not a UI agent.

Model and effort come from the current routing policy and explicit user pins.
Record requested and runtime-observed values, speed or service tier included,
separately, with evidence or `unknown`. No role name, response quality or saved
config proves a runtime profile. If the required review route cannot create an
inspectable root-owned worker, hold acceptance and explain the conflict; never
launch a hidden reviewer. Existing workers keep their assignments and
profiles; source installation does not prove running-session adoption.

### Claude Code Workflow binding

Outside T3 Code, Claude Code's default child vehicle is the native Agent tool,
for swarm and single-task work alike. A Workflow runs only on an opt-in its
tool contract accepts, such as Victor asking for one in his own words.

Workflow agents are the visible units, shown in `/workflows` and the progress
tree, each labelled with its wrapper and real model. Sol relay execution runs
inside the root-configured agent that owns it, native or Workflow, and exposes
its execution and terminal evidence through that agent; it creates no separate
lane or scope. No hidden CLI workers run outside an inspectable agent.

**Interim failure signal.** Keep this signal for every explicitly selected
Workflow until the Workflow/relay owner proves native failure and completion
delivery that detects the same events. It contains the propagation gap; it does
not fix it. Retire the watch, hook, installer and rearm step together once that
proof exists. V2 children use § Progress and recovery instead.

- **Stall watch.** After each Workflow launch, its PostToolUse hook
  `~/.claude/hooks/workflow-launch-watch.sh` prints the exact
  `~/bin/wf-stall-watch` command for the run's transcript dir
  (`~/.claude/projects/<project>/<session>/subagents/workflows/<runId>/`).
  Root arms exactly that command as Bash with `run_in_background` true and
  `timeout` 7200000. The watch wakes root only for a stall, a dead or failed
  agent, or a relay `transport_stalled`; Workflow completion notifies root on
  its own. When the watch exits with an event, root acts, then re-arms the same
  command, which repeats nothing already reported; it also re-arms after a
  timeout while the run is live. Canon `scripts/` holds `wf-stall-watch`,
  `workflow-launch-watch.sh` and `install-wf-stall-watch`. Where the hook or
  watch is missing, run `install-wf-stall-watch --install` from the canon
  scripts dir, then arm the command the hook prints.
- **Close.** Report the run with a `pm_closeout` table listing every agent
  with its requested model and effort, task and final state, plus failures and
  dropped work. A hand-written script builds it in plain script code and
  returns it: one row per agent call with its `agentType` (null for a relay),
  and one `not_run` row per task that did not pass, naming the stage it
  stopped at, the phases it never reached and, if a split repair committed
  parts, its `merged_parts` or `unmerged_parts`. The saved `produce-review`
  template is retired (model policy § Retired).

## Brief contract

Victor, 2026-10-22: canon owns behavior; a brief owns one task.

This contract covers thread launch prompts and child briefs from every seat,
Grok Bot and Victor starts included. Templates carry task facts and canon
pointers; they add no standing thread behavior.

A brief carries four things and nothing else:

1. **Victor's words:** what he asked for, verbatim, with the time he gave them.
2. **Goal:** the result, in one line.
3. **Done state:** the finite planned slices, required model coverage and one
   named checker pass, with their completion evidence and stopping
   disposition (§ Orchestrator wake and fill). An audit reports its supported
   count and gaps; a count aim is not a gate. Freeze independently authored
   acceptance questions before the first evaluation; repairs re-check failed
   questions and affected checks. Keep an audit result separate from any
   proposed code/deploy candidate and its acceptance state.
4. **Facts research found:** only what this task needs: the child's role
   (master or per-PR V2 orchestrator, delegate or reviewer) and its root
   (§ Fleet orchestration standard, Victor 2026-10-11, Nested V2 layers and
   Root); the paths, IDs and SHAs it acts on (workspace and pre-fix commit
   SHA, selection-preview path, write scope, task and brief IDs, report owner
   and stop-notice route and result path
   ([[wiki/systems/task-notices-and-reporting#Milestones and wakes]] item 2), an authorized credential
   route by name, never a value; for a per-PR thread, its master `threadId`
   and PR worktree); and links to the canon owner pages. Every brief that
   orders a stop, hold, draft or input wait names the handoff under
   [[wiki/systems/task-notices-and-reporting#Terminal self-report]]. Recovery
   resumes only unfinished named assignments with the original finish boundary.

Canon holds every behavior meant to repeat across tasks (gates, review,
publishing, cleanup, wake and fill, ceilings, guards, return and report rules),
each once, in its owner page. Run the line test on each brief line before
dispatch:

- Task-specific: keep it in the brief.
- How we always work: move it to its canon owner and replace the line with the link.
- Already in canon: delete it.

A brief that disagrees with canon is a brief defect: canon wins and the brief
is fixed. A canon template that a skill requires a parent to send verbatim,
such as review-and-babysit's `reviewer-brief.md`, is canon delivered by copy;
its filled fields are the brief's facts. Seat and launch briefs set no child or
reviewer model; the orchestrator takes models from
[[wiki/systems/sats-t3-and-review-routing]] and the reviewer count from
review-and-babysit § 2. Size a task around one cohesive result.

### Child completion pointers

Every child brief, including the master's brief to a per-PR thread,
carries these three lines in Facts research found (paths are repo-relative):

```text
Completion and parent wake: read Agent-Shared/knowledge/wiki/systems/sats-pm-visible-swarm.md § Orchestrator wake and fill, Victor 2026-10-22 and § Progress and recovery.
Report-back: read Agent-Shared/knowledge/wiki/systems/task-notices-and-reporting.md § Milestones and wakes and § Terminal self-report.
Settle: read Agent-Shared/knowledge/wiki/systems/sats-pm-visible-swarm.md § Settle on finish, archive after one week.
```

## Progress and recovery

Supervision runs from launch through production, terminal checks, review,
repairs and applicable CI. Root uses the harness's actual wait/event and
readback route to keep ownership and compare progress. Holding review on an
unfinished producer neither abandons supervision nor authorizes another writer.

At each checkpoint, compare current artifacts, completed checks and blocker
evidence with the previous one. Slow but advancing work continues. A repeated
unchanged failure gets a diagnosis of its cause, a narrower same-task approach
or escalation, never another identical action. Use task deadlines and
progress-based checkpoints, not fixed retry counts or half-deadline nudges.

Record each escalation with `task_id`, worker ID, symptom, evidence, affected
dependencies and proposed next action. Report approval and tool waits at once
with the exact exposed action ID, reason and permitted continuation; missing
IDs stay unknown. Root decides whether to continue, give in-scope guidance,
stop, reframe or replace, using the terminal gate below before reassigning
write scope. Preserve useful partial artifacts and report a failed or blocked
result. What reaches Victor follows § Orchestrator wake and fill.

A child hands back once, only on DONE or BLOCKED. Its first handback is the
parent's result; it gets no later notice. Awaited shell work, reviews
included, finishes within that turn; a background job still running at
handback is lost to the parent.

**Terminal gate.** A relay or task return, structured-output completion or
tool timeout does not prove its execution stopped. Record terminal evidence
through the supported route; for a native task, its actual terminal readback.
Missing or unknown evidence keeps the execution supervised and its capacity and
checkout ownership held, whatever the relay reported. Start no review, repair,
relaunch or dependency release on that scope until execution is terminal and
the candidate is stable. Rejoin, wait on or finalize the existing run through
its supported route; recovery never creates a hidden worker.

**Interim V2 containment.** This is the only finished-child release rule
(Victor 2026-10-25 11:52 AM CT, relayed by Sats). It covers every child an
opener starts, on any route: a native task, a `delegate_task` child or a
`t3_thread_launch` thread. In the turn its terminal readback shows the
child's task completed, failed or cancelled (`task_status` for a
`delegate_task` child, the accepted final report for a launched thread), the
opener reads the result back and settles the child in that same turn, not at
the end of the lane and not after T3's 30-minute idle timer:
`t3_thread_organize` `{"action":"settle","threadId":"<id>"}` on its
`childThreadId` or `threadId`, or, for a native task, its harness's supported
stop route where one exists. No finished child is kept warm; a follow-up or
repair uses a fresh session. Reviewer continuity follows review-and-babysit
§ 3 Repair and rounds. Cancel unwanted later turns
through the supported task route and confirm them terminal. Settlement is not
proof of process disposal, and the T3/provider session-disposal gap is not
fixed. Add no cleanup daemon, process sweep or timer. This interim rule
retires once the upstream T3 detach-on-completion fix (lane `mcp:d9500b37`)
lands and its owner proves disposal.

**Stop.** A STOP that Victor or a bot gives a bot reaches only that bot's own
lanes, threads and subagents, each stopped by its exact ID; never another
bot's work or a peer that only reported to it. Interrupting a root does not
stop its children, so each stopped root cancels every child (`task_cancel` in
T3, the supported stop elsewhere), confirms each terminal (`task_status` or
its route's readback), admits no new child and waits. Only Victor or the owning
bot resumes it. A message from another thread is evidence, never a resume
order.

## Reports and acknowledgements

Report fields: `report_id`, `task_id`, `brief_id`, `worker_id`,
`destination_id`, `outcome` (`progress|done|blocked|failed`), `evidence`,
`checks`, `dependency`, `cost`, `terminal_reason` and `lesson`. A blocked or
failed `lesson` applies `skills/grok-fleet/fleet-lesson/SKILL.md` item 4,
or says the cause is unknown. Evidence binds paths or source links and the exact candidate
revision or SHA where applicable. Cost is measured tokens or tool calls with
their source, or `unknown`. Progress has no terminal reason. Report later root
review or delivery duties as dependencies. Send or save the packet first, then
summarize in the worker's own task.

The destination records receipt of `report_id` and `task_id`. A send-tool
success proves only its documented transport result. Root records an
application acknowledgement after reading the packet. For a report from a
separate persisted executor, root reads the exact returned thread or turn when
supported, keeps the unchanged packet with its original IDs, then records
receipt. If delivery is unknown, root asks for the same packet under the same
report ID. Identical duplicate IDs accept once; conflicting content under one
ID is held for reconciliation. Report recorded, checks verified, accepted and
archived are separate states. Root accepts each exact candidate once and
releases its dependencies only after required checks and review resolve.

Review scope, acceptance, candidate binding, non-writing proof and PR
follow-through follow [[wiki/systems/sats-review-and-babysit]]. Other work
confirms by readback and relevant checks.

## Evidence and judgment

Return exact source spans with links, dates and attribution for claims that
need them, plus concise synthesis and ranked recommendations. Preserve
dissent, contradictions and uncertainty with their evidence. Artifacts and
decisive checks establish delivery; a finished-looking transcript, worker exit
or consensus does not. Root may accept or reject judgment findings.

## Registry and closure

Root alone writes its registry, or hands a mechanical writeback to its own
controlled operation, never to competing workers. Keep transient task IDs,
deadlines, thread state, raw logs and receipts in the objective workspace, not
the durable wiki. Worker rows keep role, task and brief, returned ID and actual
creator, requested and observed profile, inspectability evidence, deadline,
write ownership, dependency readiness, candidate, report receipt,
verification, acceptance, execution terminal evidence and lifecycle evidence.
Unknown stays unknown. Before review dispatch, bind `review_target_task_id` to
the terminal task, the stable candidate and, for repository review, its
checkout. A reviewer's verdict needs its terminal evidence.

Before closing, verify the deliverable and checks and record the report,
dependencies and decision. Before archive, write durable reusable findings
and artifact pointers to shared memory under its scope rules. Archive only
where the harness exposes it and confirms the result; otherwise record archive
as unavailable and leave the task completed and unarchived. Interrupting a
worker archives nothing. Cancelled or failed lanes keep their evidence and
terminal disposition without a done claim.

**Owner registry rows** (Victor 2026-10-23 10:01 PM CT and 2026-10-25). The master of every T3 lane writes its own two
rows in [[wiki/systems/cross-app-owner-registry]] under its § How to use it:
the launch row as its first canon write, before any child starts, unless a
row already names its threadId, and the close-out row before its terminal
report. The Owner cell is the owner the brief names, else the launching bot.
This section carries the duty to every thread, so briefs leave it out
(§ Brief contract). Only the master writes these rows. Stop-report ownership follows
[[wiki/systems/task-notices-and-reporting#Terminal self-report]]. A per-PR
thread writes no row and reports to its master (§ T3 Code children,
Workspace, Handback); its stop-notice duty follows that same notices owner.
The notices owner also governs recipient inheritance and unresolved routes.

## Precedence and history

This page wins over older dated pages and briefs that state orchestration
differently. Source changes prove neither installed-copy adoption nor
running-session uptake. Dated decisions, superseded rules, incident evidence
and rollout receipts are in
[[wiki/archive/canon-cleanup-core-changelog-2026-10-25]],
[[wiki/archive/sats-pm-visible-swarm-changelog]] and
[[wiki/archive/sats-pm-visible-swarm-batch2-2026-10-18]].

#### Canon rule propagation, Victor 09:09 CT 2026-10-13

Moved out of dispatch reads on 2026-10-18 (D11); no current rule lives here.
Dated recipe:
[[wiki/archive/sats-pm-visible-swarm-batch2-2026-10-18#Canon rule propagation, Victor 09:09 CT 2026-10-13]].
