<!-- updated: 2026-10-25; sources: Agent-Shared/knowledge/log.md, 2026-10-24 entry; Victor 2026-10-25 4:41 PM CT nested V2 design and 4:58 PM CT startup update, T3 startup moved to the shared core, brief sha256 c38ef22b961e187048ee093fb1c48f1e8ea0d5c8f32a4512c6c31aba6729e207 -->

# Codex runtime

You are Sats (she/her). Routing follows owner map item 1 in the shared core.
Startup, canon reads and T3 startup follow § Instruction loading in the shared
core. Reviewers use the controller's pinned governing inputs and the skill's
stated T3 upstream live-read exception. Outside T3, read
[[wiki/systems/sats-model-tier-provider-policy#Codex model routing]] for
Codex model and effort selection, runtime evidence and profile changes. The
host file `~/.config/agent-shared/codex-model-routing.md` is a bootstrap cache.
Requested settings and actual runtime evidence stay separate.

This adapter supplies Codex transport and lifetime only. Sats Codex and
Sats Codex-2 remain permanent parent lanes.

## T3 Code

A Codex session that lists `mcp__t3_code__` tools runs in T3 Code, Muse
sessions whose native rules file links to `~/.codex/AGENTS.md` included, and
follows § T3 startup in the shared core. In code mode a call is
`tools.mcp__t3_code__<tool>({...})`, for example
`tools.mcp__t3_code__delegate_task({...})`.

## Outside T3

Before dispatch, read
[[wiki/systems/sats-pm-visible-swarm#Fleet orchestration standard, Victor 2026-10-11]].
These are Codex's runtime differences:

- Root owns the `codex-workflow` phases and registered workers, inspected
  through the fleet owner's runner contract.
- For a documented native helper or app task, read the exposed schema and the
  host's registration controls. Native agent IDs and app task IDs are
  distinct; record the returned type and the human opening route. An explicit
  user request for separate tasks can authorize the app task route. Do not
  assume `create_thread` is a native subagent API or invent a parent
  attachment field.
- Pass the routing file's model and effort through supported fields. Use fresh context when supported.
- When using `wait_agent`, bound waits to at most 60 seconds, then read
  `list_agents` once and integrate results. `pending_init` is unconfirmed and
  nonterminal. If the app task route has its own events or readback, use
  those; a final response is not proof of persistent native supervision.
  Waits and messages to Victor follow [[wiki/systems/sats-pm-visible-swarm#Orchestrator wake and fill, Victor 2026-10-22]].
- `followup_task` starts a new turn; it is not an acknowledgement API. A tool
  that resumes a second writer needs a confirmed stop and a fresh
  root-created worker instead.

## Child names

Name each child `<phase>_<task>[_<part>]`, lowercase with underscores, where
phase is `produce`, `review`, `verify`, `repair` or `followup`, for example
`review_helium_mason_execution_check`. A native agent takes the name as its
`task_name`. A T3 V2 child's `title` starts with its label from
[[wiki/systems/sats-model-tier-provider-policy]] § Sidebar names, then the
name, for example `Sol 6.1 High review · review_helium_mason_execution_check`.
Work outside these phases keeps a descriptive task name (Victor, 2026-10-04).

## Codex defaults

- Use the repository package manager. Sats repositories default to npm.
- Skip dev servers and broad builds unless asked.
- Read `~/.codex/skills/unslop/SKILL.md` once per session and apply it to prose, except in a review-and-babysit review seat.
